"""Round 3 maker-only validation probe (dataathletechamp) = combined-regime ladder step C1.

Only the M1 FV-gated touch maker trades by default: FOLLOW_ENABLED = False disables all follower
logic (no entries, flips or exits), so the maker quotes at all times and the regime switch has no
effect.  The file is otherwise identical to r3_combined_regime.py.

One +/-MAX_LOTS inventory ledger is shared by two engines.

E1  Informed-flow follower ("D1").  Signal A per market taker order (trades grouped by
    taker_order_id, sign from book_side): (4th+ consecutive same-sign market taker order AND
    filled >= A_FILL_MIN) OR (|max - min fill price| >= A_SWEEP ticks) OR (filled >= A_BIG).
    A sets the target to sign * FOLLOW_LOTS, taken by IOC at the current opposite touch
    (+ENTRY_CAP), re-sent until done.  A same-sign A extends the FOLLOW_HOLD_S deadline; an
    opposite A flips (IOC through the touch by EXIT_CAP).  At the deadline the position is
    exited by joining the exit-side touch for EXIT_TOUCH_WAIT_S, then by IOC (EXIT_MODE='touch').
M1  FV-gated touch maker.  MAKER_Q lots per side at the market touch; a quote is re-priced
    (cancel, re-send after the cancel confirms) only when the touch moved away from it.  A side
    s (+1 bid, -1 ask) is cancelled / not placed while -s * FV >= FV_CANCEL, where
    FV = (max price of new bid limit inserts seen in the last FV_WIN_US + min price of new ask
    limit inserts in the last FV_WIN_US) / 2 - market mid (FV = 0 when either side had none;
    new = market order id larger than every id seen before).  Total inventory incl. pending
    orders is capped at MAKER_CAP while the maker quotes.
Regime switch.  rate = EMA (time constant RATE_TAU_S) of the signal-A count per second.
    High (rate >= RATE_HIGH): the follower may open, extend and flip.  Low: the follower opens
    nothing new and its open position is exited at the deadline; the maker quotes only while
    the follower is flat (also in the high state when MAKER_WHEN_FLAT_HIGH).  The follower has
    priority: activating it cancels all maker quotes and it owns the whole inventory until
    flat.  Every send is clipped so |pos + pending buys| and |pos - pending sells| stay
    <= MAX_LOTS (resting + in-flight orders of both engines).
EXIT_FV_MODE ('off' | 'ioc' | 'wait'): passive follower exits only while FV does not oppose
    the exit side; 'ioc' falls back to IOC at once when FV opposes, 'wait' keeps the exit
    timer and re-joins when it clears.
Parameters are module-level constants read at call time.
"""

from __future__ import annotations

import math
from collections import deque

from simulator.models import (
    OrderBookSnapshot,
    OrderRequest,
    OrderStatus,
    OrderType,
    PrivateOrderEvent,
    Side,
    Trade,
)
from simulator.strategy import BaseStrategy

# ---------------------------------------------------------------- shared ledger
MAX_LOTS = 100
# ---------------------------------------------------------------- E1 follower
FOLLOW_ENABLED = False  # maker-only probe: follower disabled
FOLLOW_LOTS = 100
FOLLOW_HOLD_S = 5.0
A_RUN_MIN = 4
A_FILL_MIN = 100
A_SWEEP = 2
A_BIG = 500
ENTRY_CAP = 0
EXIT_CAP = 3
EXIT_MODE = "touch"  # touch | ioc
EXIT_TOUCH_WAIT_S = 1.0
EXIT_FV_MODE = "off"  # off | ioc | wait
FOLLOW_LOW_EXTEND = False  # low regime: let same-sign A still extend an open position
# ---------------------------------------------------------------- M1 maker
MAKER_ENABLED = True
MAKER_Q = 20
MAKER_CAP = 80
MAKER_FV_GATE = True
FV_CANCEL = 0.5
FV_WIN_US = 50_000
# ---------------------------------------------------------------- regime switch
REGIME_ENABLED = True
RATE_TAU_S = 120.0
RATE_HIGH = 0.867
MAKER_WHEN_FLAT_HIGH = False

_BUY = Side.BUY
_SELL = Side.SELL
_IOC = OrderType.IOC
_LIMIT = OrderType.LIMIT
_FILLED = OrderStatus.FILLED
_PARTIAL = OrderStatus.PARTIALLY_FILLED
_CANCELED = OrderStatus.CANCELED
_REJECTED = OrderStatus.REJECTED
# follower order kinds (IOC kinds < K_PX)
K_IN = 0
K_FLIP = 1
K_OUT = 2
K_PX = 3


class CombinedMakerProbe(BaseStrategy):
    def __init__(self) -> None:
        super().__init__()
        self.pos = 0
        # follower: oid -> [sign, remaining, kind, price]
        self.fo: dict[str, list] = {}
        self.f_cxl: set[str] = set()
        self.f_on = False
        self.target = 0
        self.deadline = 0
        self.wait_until = 0
        # maker: oid -> [sign, remaining, price, cancelling]
        self.mo: dict[str, list] = {}
        self.main: dict[int, str | None] = {1: None, -1: None}
        # signal A / regime
        self.run_sign = 0
        self.run_len = 0
        self.rate = 0.0
        self.rate_t = 0
        # FV (new-insert extremes)
        self.prev_bids: list = []
        self.prev_asks: list = []
        self.prev_ids: dict[int, dict] = {1: {}, -1: {}}
        self.max_id = 0
        self.ins_bid: deque = deque()
        self.ins_ask: deque = deque()
        self.fv = 0.0
        # diagnostics (counters only)
        self.last_t = -1
        self.n_a = 0
        self.n_entry = 0
        self.n_flip = 0
        self.n_ignored_low = 0
        self.f_lots = 0
        self.m_lots = 0
        self.m_sent = 0
        self.us_total = 0
        self.us_high = 0
        self.us_maker = 0
        self.us_follow = 0
        self.max_expo = 0

    # ------------------------------------------------------------ helpers
    def _room(self, s: int, cap: int) -> int:
        buys = 0
        sells = 0
        for o in self.fo.values():
            if o[0] > 0:
                buys += o[1]
            else:
                sells += o[1]
        for o in self.mo.values():
            if o[0] > 0:
                buys += o[1]
            else:
                sells += o[1]
        if s > 0:
            return cap - (self.pos + buys)
        return cap + (self.pos - sells)

    def _expo_check(self, s: int, q: int) -> None:
        room = self._room(s, MAX_LOTS)
        e = MAX_LOTS - room + q
        if e > self.max_expo:
            self.max_expo = e

    def _f_send(self, s: int, qty: int, price: int, kind: int) -> None:
        room = self._room(s, MAX_LOTS)
        if qty > room:
            qty = room
        if qty <= 0 or price <= 0:
            return
        self._expo_check(s, qty)
        oid = self.send_order(
            OrderRequest(
                side=_BUY if s > 0 else _SELL,
                price=int(price),
                quantity=int(qty),
                order_type=_LIMIT if kind == K_PX else _IOC,
            )
        )
        self.fo[oid] = [s, qty, kind, price]

    def _f_cancel(self, oid: str) -> None:
        if oid not in self.f_cxl:
            self.f_cxl.add(oid)
            self.cancel_order(oid)

    def _m_cancel_all(self) -> None:
        for oid, r in self.mo.items():
            if not r[3]:
                r[3] = True
                self.cancel_order(oid)

    def _m_drop(self, oid: str, r: list) -> None:
        del self.mo[oid]
        s = r[0]
        if self.main[s] == oid:
            self.main[s] = None

    def _new_inserts(self, s: int, lst: list, t: int) -> None:
        ids = {v.order_id: v.price for v in lst}
        prev = self.prev_ids[s]
        self.prev_ids[s] = ids
        new = ids.keys() - prev.keys()
        if not new:
            return
        mx = self.max_id
        dq = self.ins_bid if s > 0 else self.ins_ask
        for oid in new:
            if not oid.isdigit():
                continue
            n = int(oid)
            if n <= mx:
                continue
            if n > self.max_id:
                self.max_id = n
            price = ids[oid]
            if s > 0:
                while dq and dq[-1][1] <= price:
                    dq.pop()
            else:
                while dq and dq[-1][1] >= price:
                    dq.pop()
            dq.append((t, price))

    def _rate_at(self, t: int) -> float:
        if t != self.rate_t:
            if self.rate > 0.0:
                self.rate *= math.exp(-(t - self.rate_t) / (RATE_TAU_S * 1e6))
            self.rate_t = t
        return self.rate

    # ------------------------------------------------------------ private feed
    def on_private_order_update(self, event: PrivateOrderEvent) -> None:
        oid = event.order_id
        st = event.status
        o = self.fo.get(oid)
        if o is not None:
            if st == _FILLED or st == _PARTIAL:
                q = event.filled_quantity
                self.pos += o[0] * q
                self.f_lots += q
                o[1] -= q
                if o[1] <= 0:
                    del self.fo[oid]
                    self.f_cxl.discard(oid)
            elif st == _CANCELED or st == _REJECTED:
                del self.fo[oid]
                self.f_cxl.discard(oid)
            return
        r = self.mo.get(oid)
        if r is not None:
            if st == _FILLED or st == _PARTIAL:
                q = event.filled_quantity
                self.pos += r[0] * q
                self.m_lots += q
                r[1] -= q
                if st == _FILLED or r[1] <= 0:
                    self._m_drop(oid, r)
            elif st == _CANCELED or st == _REJECTED:
                self._m_drop(oid, r)

    # ------------------------------------------------------------ public feed
    def on_order_book_change(self, snapshot: OrderBookSnapshot, trades: list[Trade]) -> None:
        t = snapshot.timestamp_us
        bids = snapshot.bids
        asks = snapshot.asks
        # ---------------- signal A (market takers only)
        sig = 0
        if trades:
            cur = None
            gs = 0
            filled = 0
            pmin = pmax = 0
            groups = []
            for tr in trades:
                if tr.taker_owner != "market":
                    continue
                if tr.taker_order_id != cur:
                    if cur is not None:
                        groups.append((gs, filled, pmax - pmin))
                    cur = tr.taker_order_id
                    gs = 1 if tr.book_side == "ask" else -1
                    filled = 0
                    pmin = pmax = tr.price
                filled += tr.quantity
                p = tr.price
                if p < pmin:
                    pmin = p
                elif p > pmax:
                    pmax = p
            if cur is not None:
                groups.append((gs, filled, pmax - pmin))
            n_new = 0
            for gs, filled, lv in groups:
                if gs == self.run_sign:
                    self.run_len += 1
                else:
                    self.run_sign = gs
                    self.run_len = 1
                if (
                    lv >= A_SWEEP
                    or filled >= A_BIG
                    or (self.run_len >= A_RUN_MIN and filled >= A_FILL_MIN)
                ):
                    n_new += 1
                    sig = gs
            if n_new:
                self._rate_at(t)
                self.rate += n_new * (1.0 - math.exp(-1.0 / RATE_TAU_S))
                self.n_a += n_new
        # ---------------- new-insert detection (FV)
        if bids != self.prev_bids:
            self._new_inserts(1, bids, t)
            self.prev_bids = bids
        if asks != self.prev_asks:
            self._new_inserts(-1, asks, t)
            self.prev_asks = asks
        # ---------------- market touch
        bbm = 0
        for v in bids:
            if v.owner == "market":
                bbm = v.price
                break
        bam = 0
        for v in asks:
            if v.owner == "market":
                bam = v.price
                break
        rate = self._rate_at(t)
        high = (not REGIME_ENABLED) or rate >= RATE_HIGH
        if self.last_t >= 0:
            dt = t - self.last_t
            self.us_total += dt
            if high:
                self.us_high += dt
            if self.f_on:
                self.us_follow += dt
            elif self.mo:
                self.us_maker += dt
        self.last_t = t
        if bbm <= 0 or bam <= 0:
            return
        mid = 0.5 * (bbm + bam)
        lo = t - FV_WIN_US
        db = self.ins_bid
        da = self.ins_ask
        while db and db[0][0] <= lo:
            db.popleft()
        while da and da[0][0] <= lo:
            da.popleft()
        fv = (db[0][1] + da[0][1]) / 2.0 - mid if (db and da) else 0.0
        self.fv = fv
        # ---------------- E1 follower (priority)
        if FOLLOW_ENABLED:
            if sig:
                self._f_signal(t, sig, high)
            if self.target != 0 and t >= self.deadline:
                self.target = 0
            if self.f_on:
                if self.target != self.pos or self.fo:
                    self._f_reconcile(t, bbm, bam)
                if self.target == 0 and self.pos == 0 and not self.fo:
                    self.f_on = False
        # ---------------- M1 maker
        if MAKER_ENABLED:
            if not self.f_on and (not FOLLOW_ENABLED or not high or MAKER_WHEN_FLAT_HIGH):
                self._maker(bbm, bam, fv)
            elif self.mo:
                self._m_cancel_all()

    # ------------------------------------------------------------ follower
    def _f_signal(self, t: int, s: int, high: bool) -> None:
        cur = 1 if self.target > 0 else (-1 if self.target < 0 else 0)
        if cur == s:
            if high or FOLLOW_LOW_EXTEND:
                self.deadline = t + int(FOLLOW_HOLD_S * 1e6)
            return
        if not high:
            self.n_ignored_low += 1
            return
        if not self.f_on:
            self.f_on = True
            self._m_cancel_all()
        if cur == 0:
            self.n_entry += 1
        else:
            self.n_flip += 1
        self.target = s * FOLLOW_LOTS
        self.deadline = t + int(FOLLOW_HOLD_S * 1e6)
        self.wait_until = 0

    def _f_reconcile(self, t: int, bid: int, ask: int) -> None:
        if self.f_cxl:
            return
        fo = self.fo
        for o in fo.values():
            if o[2] != K_PX:
                return  # wait for in-flight follower IOCs
        pos = self.pos
        tg = self.target
        want = tg - pos
        if want == 0:
            if pos == 0 and fo:
                for oid in list(fo):
                    self._f_cancel(oid)
            return
        ws = 1 if want > 0 else -1
        exiting = tg == 0 or (pos != 0 and (tg > 0) == (pos > 0) and abs(tg) < abs(pos))
        flipping = pos != 0 and tg != 0 and (tg > 0) != (pos > 0)
        if exiting:
            if EXIT_MODE == "touch":
                # all follower orders are passive exits here (IOCs returned above)
                fvm = EXIT_FV_MODE
                opp = fvm != "off" and -ws * self.fv >= FV_CANCEL
                if not fo:
                    if self.wait_until != -1:
                        wait_us = int(EXIT_TOUCH_WAIT_S * 1e6)
                        if fvm == "wait":
                            if self.wait_until == 0:
                                self.wait_until = t + wait_us
                            if t < self.wait_until:
                                if not opp:
                                    self._f_send(ws, abs(want), bid if ws > 0 else ask, K_PX)
                                return
                            self.wait_until = -1
                        elif opp:
                            self.wait_until = -1
                        else:
                            self._f_send(ws, abs(want), bid if ws > 0 else ask, K_PX)
                            self.wait_until = t + wait_us
                            return
                else:
                    if t >= self.wait_until or opp:
                        for oid in list(fo):
                            self._f_cancel(oid)
                        if fvm != "wait" or t >= self.wait_until:
                            self.wait_until = -1
                    return
            if fo:
                for oid in list(fo):
                    self._f_cancel(oid)
                return
            lim = ask + EXIT_CAP if ws > 0 else bid - EXIT_CAP
            self._f_send(ws, abs(want), lim, K_OUT)
            return
        if flipping:
            if fo:
                for oid in list(fo):
                    self._f_cancel(oid)
                return
            lim = ask + EXIT_CAP if ws > 0 else bid - EXIT_CAP
            self._f_send(ws, abs(want), lim, K_FLIP)
            return
        lim = ask + ENTRY_CAP if ws > 0 else bid - ENTRY_CAP
        self._f_send(ws, abs(want), lim, K_IN)

    # ------------------------------------------------------------ maker
    def _maker(self, bbm: int, bam: int, fv: float) -> None:
        gate = MAKER_FV_GATE
        cut = FV_CANCEL
        for s in (1, -1):
            blocked = gate and -s * fv >= cut
            oid = self.main[s]
            if oid is not None:
                r = self.mo.get(oid)
                if r is None:
                    self.main[s] = None
                    continue
                if r[3]:
                    continue
                if blocked or (s > 0 and r[2] < bbm) or (s < 0 and r[2] > bam):
                    r[3] = True
                    self.cancel_order(oid)
                continue
            if blocked:
                continue
            q = MAKER_Q
            room = self._room(s, MAKER_CAP)
            if room < q:
                q = room
            if q <= 0:
                continue
            px = bbm if s > 0 else bam
            self._expo_check(s, q)
            oid = self.send_order(
                OrderRequest(
                    side=_BUY if s > 0 else _SELL, price=int(px), quantity=int(q), order_type=_LIMIT
                )
            )
            self.mo[oid] = [s, q, px, False]
            self.main[s] = oid
            self.m_sent += 1

    # ------------------------------------------------------------ diagnostics (not for trading)
    def diagnostics(self) -> dict:
        tot = self.us_total if self.us_total > 0 else 1
        return {
            "a_signals": self.n_a,
            "entries": self.n_entry,
            "flips": self.n_flip,
            "signals_ignored_low": self.n_ignored_low,
            "follower_lots": self.f_lots,
            "maker_lots": self.m_lots,
            "maker_sent": self.m_sent,
            "share_high": self.us_high / tot,
            "share_follower_on": self.us_follow / tot,
            "share_maker_quoting": self.us_maker / tot,
            "max_expo_incl_pending": self.max_expo,
            "final_pos": self.pos,
        }
