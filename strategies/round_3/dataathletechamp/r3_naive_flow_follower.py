"""R3 naive flow follower (research families kept behind FAMILY; default = simplest winning family).

Default FAMILY "flow": keep a 200 ms window of signed MARKET-taker volume (+qty when the taker
lifts asks, -qty when it hits bids). Sum >= FLOW_V (600) -> target +LOTS; <= -FLOW_V -> -LOTS;
otherwise HOLD the previous target (always-in-market after the first signal). Execution: one
IOC to target at touch +- CAP ticks; no new order while one is pending; exposure incl. pending
never exceeds LOTS (100). No passive orders, no model, no fitted constants beyond 2 thresholds.
Official engine (5 ms, +-100, 10,000/s): R3 public 279,902 (fit 45.8/s, eval 47.2/s, 9/10
positive 600 s blocks, 285,900 lots, penalty 0); R2 public 170,949 (8/10 blocks, 302,900 lots).
Plateau: windows 100-300 ms x thresholds 400-800 all give R3 246-309k and R2 91-172k.
Other FAMILY values (mom, ema, mr, obi, sweep, mm, wide, jump, obimm, obiflow) are the
naive families tested in experiment 20261108-r3-w6-naive-001; all lost or were weaker.
"""

import math
from collections import deque

from simulator.models import OrderRequest, OrderStatus, OrderType, Side
from simulator.strategy import BaseStrategy

FAMILY = "flow"
LOTS = 100
CAP = 3
DECISION_MS = 200
WARM_S = 0.0
# mom
WINDOW_S = 1.0
DEADBAND = 1.0
BAND_MODE = "hold"  # hold | flat
# ema / mr
FAST_S = 1.0
SLOW_S = 10.0
HYST = 0.5
MR_K = 40.0
MR_EXIT = 0.0
# flow
FLOW_WIN_MS = 200
FLOW_V = 600
FLOW_SIGN = 1
# obi
OBI_LEVELS = 3
OBI_TH = 0.5
OBI_SIGN = 1
# sweep
SWEEP_TICKS = 3
SWEEP_HOLD_S = 5.0
SWEEP_DIR = -1
# mm / wide
MM_Q = 20
MM_SKEW = 50
MM_IMPROVE = False
WIDE_K = 4
WIDE_Q = 50
WIDE_EXIT_S = 1.0
# jump (big-move rider; LOTS may exceed 100 -> time-integrated penalty while held)
JUMP_D = 20.0
JUMP_HOLD_S = 1.0


class NaiveFlowFollower(BaseStrategy):
    def __init__(self) -> None:
        super().__init__()
        self.fam = FAMILY
        self.L = int(LOTS)
        self.cap = int(CAP)
        self.dec = int(DECISION_MS * 1000)
        self.warm = int(WARM_S * 1e6)
        self.win = int(WINDOW_S * 1e6)
        self.tf = FAST_S * 1e6
        self.ts = SLOW_S * 1e6
        self.flow_win = int(FLOW_WIN_MS * 1000)
        self.sweep_hold = int(SWEEP_HOLD_S * 1e6)
        self.wide_exit = int(WIDE_EXIT_S * 1e6)
        self.jump_hold = int(JUMP_HOLD_S * 1e6)
        self.pos = 0
        self.orders: dict = {}  # oid -> [sign, remaining, kind, price]
        self.cancelling: set = set()
        self.target = 0
        self.now = 0
        self.t0 = -1
        self.next_t = 0
        self.hist: deque = deque()
        self.ef = None
        self.es = None
        self.et = 0
        self.flow: deque = deque()
        self.flow_sum = 0
        self.sweep_until = 0
        self.inv_since = 0
        self.n_send = 0
        self.n_skip = 0
        self.n_cancel = 0
        self.n_signal = 0
        self.fill_lots: dict = {}

    # ------------- bookkeeping
    def _send(self, sign: int, qty: int, price: int, kind: str, ioc: bool) -> None:
        if qty <= 0 or price <= 0:
            return
        buys = sells = 0
        for o in self.orders.values():
            if o[0] > 0:
                buys += o[1]
            else:
                sells += o[1]
        if sign > 0:
            buys += qty
        else:
            sells += qty
        if self.pos + buys > self.L or sells - self.pos > self.L:
            self.n_skip += 1
            return
        oid = self.send_order(
            OrderRequest(
                side=Side.BUY if sign > 0 else Side.SELL,
                price=int(price),
                quantity=int(qty),
                order_type=OrderType.IOC if ioc else OrderType.LIMIT,
            )
        )
        self.n_send += 1
        self.orders[oid] = [sign, qty, kind, price]

    def _cancel(self, oid: str) -> None:
        if oid not in self.cancelling:
            self.cancelling.add(oid)
            self.n_cancel += 1
            self.cancel_order(oid)

    def on_private_order_update(self, event) -> None:
        oid = event.order_id
        st = event.status
        o = self.orders.get(oid)
        if st == OrderStatus.FILLED or st == OrderStatus.PARTIALLY_FILLED:
            if o is None:
                return
            q = event.filled_quantity
            before = self.pos
            self.pos += o[0] * q
            if before == 0 or (before > 0) != (self.pos > 0):
                self.inv_since = self.now
            o[1] -= q
            self.fill_lots[o[2]] = self.fill_lots.get(o[2], 0) + q
            if o[1] <= 0:
                del self.orders[oid]
                self.cancelling.discard(oid)
        elif st == OrderStatus.CANCELED or st == OrderStatus.REJECTED:
            self.orders.pop(oid, None)
            self.cancelling.discard(oid)

    def _rec_taker(self, bid: int, ask: int) -> None:
        if self.orders:
            return
        want = self.target - self.pos
        if want > 0:
            self._send(1, want, ask + self.cap, "ioc", True)
        elif want < 0:
            self._send(-1, -want, bid - self.cap, "ioc", True)

    def _set(self, s: int) -> None:
        tgt = s * self.L
        if tgt != self.target:
            self.target = tgt
            self.n_signal += 1

    # ------------- feed
    def on_order_book_change(self, snapshot, trades) -> None:
        t = snapshot.timestamp_us
        self.now = t
        if self.t0 < 0:
            self.t0 = t
        bid = ask = 0
        for o in snapshot.bids:
            if o.owner == "market":
                bid = o.price
                break
        for o in snapshot.asks:
            if o.owner == "market":
                ask = o.price
                break
        if bid <= 0 or ask <= 0:
            return
        mid = 0.5 * (bid + ask)
        fam = self.fam
        warm_ok = t - self.t0 >= self.warm
        if fam == "mom":
            h = self.hist
            h.append((t, mid))
            lo = t - self.win
            while len(h) > 1 and h[1][0] <= lo:
                h.popleft()
            if t >= self.next_t:
                self.next_t = t + self.dec
                if h[0][0] <= lo and warm_ok:
                    d = mid - h[0][1]
                    if d >= DEADBAND:
                        self._set(1)
                    elif d <= -DEADBAND:
                        self._set(-1)
                    elif BAND_MODE == "flat":
                        self._set(0)
            self._rec_taker(bid, ask)
        elif fam == "ema" or fam == "mr":
            if self.ef is None:
                self.ef = self.es = mid
                self.et = t
            elif t > self.et:
                dt = t - self.et
                self.ef += (1.0 - math.exp(-dt / self.tf)) * (mid - self.ef)
                self.es += (1.0 - math.exp(-dt / self.ts)) * (mid - self.es)
                self.et = t
            if t >= self.next_t:
                self.next_t = t + self.dec
                if warm_ok:
                    if fam == "ema":
                        d = self.ef - self.es
                        if d > HYST:
                            self._set(1)
                        elif d < -HYST:
                            self._set(-1)
                    else:
                        dev = mid - self.es
                        if dev > MR_K:
                            self._set(-1)
                        elif dev < -MR_K:
                            self._set(1)
                        elif self.target < 0 and dev <= MR_EXIT:
                            self._set(0)
                        elif self.target > 0 and dev >= -MR_EXIT:
                            self._set(0)
            self._rec_taker(bid, ask)
        elif fam == "flow":
            if trades:
                for tr in trades:
                    if tr.taker_owner != "market":
                        continue
                    sq = tr.quantity if tr.book_side == "ask" else -tr.quantity
                    self.flow.append((t, sq))
                    self.flow_sum += sq
            lo = t - self.flow_win
            fl = self.flow
            while fl and fl[0][0] <= lo:
                self.flow_sum -= fl.popleft()[1]
            if warm_ok:
                if self.flow_sum >= FLOW_V:
                    self._set(FLOW_SIGN)
                elif self.flow_sum <= -FLOW_V:
                    self._set(-FLOW_SIGN)
            self._rec_taker(bid, ask)
        elif fam == "obi":
            if t >= self.next_t:
                self.next_t = t + self.dec
                bq = aq = 0
                n = 0
                lp = None
                for o in snapshot.bids:
                    if o.owner != "market":
                        continue
                    if o.price != lp:
                        n += 1
                        if n > OBI_LEVELS:
                            break
                        lp = o.price
                    bq += o.quantity
                n = 0
                lp = None
                for o in snapshot.asks:
                    if o.owner != "market":
                        continue
                    if o.price != lp:
                        n += 1
                        if n > OBI_LEVELS:
                            break
                        lp = o.price
                    aq += o.quantity
                if bq + aq > 0 and warm_ok:
                    x = (bq - aq) / (bq + aq)
                    if x > OBI_TH:
                        self._set(OBI_SIGN)
                    elif x < -OBI_TH:
                        self._set(-OBI_SIGN)
            self._rec_taker(bid, ask)
        elif fam == "sweep":
            if trades:
                cur = None
                gs = 0
                pmin = pmax = 0
                groups = []
                for tr in trades:
                    if tr.taker_owner != "market":
                        continue
                    if tr.taker_order_id != cur:
                        if cur is not None:
                            groups.append((gs, pmax - pmin))
                        cur = tr.taker_order_id
                        gs = 1 if tr.book_side == "ask" else -1
                        pmin = pmax = tr.price
                    if tr.price < pmin:
                        pmin = tr.price
                    elif tr.price > pmax:
                        pmax = tr.price
                if cur is not None:
                    groups.append((gs, pmax - pmin))
                for gs, span in groups:
                    if span >= SWEEP_TICKS:
                        self._set(SWEEP_DIR * gs)
                        self.sweep_until = t + self.sweep_hold
            if self.target != 0 and t >= self.sweep_until:
                self._set(0)
            self._rec_taker(bid, ask)
        elif fam == "jump":
            h = self.hist
            h.append((t, mid))
            lo = t - self.win
            while len(h) > 1 and h[1][0] <= lo:
                h.popleft()
            d = mid - h[0][1]
            if warm_ok and d >= JUMP_D:
                self._set(1)
                self.sweep_until = t + self.jump_hold
            elif warm_ok and d <= -JUMP_D:
                self._set(-1)
                self.sweep_until = t + self.jump_hold
            if self.target != 0 and t >= self.sweep_until:
                self._set(0)
            self._rec_taker(bid, ask)
        elif fam == "obimm" or fam == "obiflow":
            x = self._obi(snapshot)
            s = 0
            if x is not None:
                if x > OBI_TH:
                    s = OBI_SIGN
                elif x < -OBI_TH:
                    s = -OBI_SIGN
            if fam == "obimm":
                q = int(MM_Q)
                self._quote(1, bid if (s > 0 and self.pos <= MM_SKEW) else None, q, "om")
                self._quote(-1, ask if (s < 0 and self.pos >= -MM_SKEW) else None, q, "om")
            else:
                # flow follower (hold) whose entries/flips need OBI agreement (s == flow sign)
                if trades:
                    for tr in trades:
                        if tr.taker_owner != "market":
                            continue
                        sq = tr.quantity if tr.book_side == "ask" else -tr.quantity
                        self.flow.append((t, sq))
                        self.flow_sum += sq
                lo = t - self.flow_win
                fl = self.flow
                while fl and fl[0][0] <= lo:
                    self.flow_sum -= fl.popleft()[1]
                if self.flow_sum >= FLOW_V and s >= 0:
                    self._set(1)
                elif self.flow_sum <= -FLOW_V and s <= 0:
                    self._set(-1)
                self._rec_taker(bid, ask)
        elif fam == "mm":
            self._mm(t, bid, ask)
        elif fam == "wide":
            self._wide(t, bid, ask)

    def _obi(self, snapshot):
        bq = aq = 0
        n = 0
        lp = None
        for o in snapshot.bids:
            if o.owner != "market":
                continue
            if o.price != lp:
                n += 1
                if n > OBI_LEVELS:
                    break
                lp = o.price
            bq += o.quantity
        n = 0
        lp = None
        for o in snapshot.asks:
            if o.owner != "market":
                continue
            if o.price != lp:
                n += 1
                if n > OBI_LEVELS:
                    break
                lp = o.price
            aq += o.quantity
        if bq + aq <= 0:
            return None
        return (bq - aq) / (bq + aq)

    def _quote(self, sign: int, price, qty: int, kind: str) -> None:
        mine = [(oid, o) for oid, o in self.orders.items() if o[0] == sign and o[2] == kind]
        if price is None:
            for oid, _ in mine:
                self._cancel(oid)
            return
        live = 0
        for oid, o in mine:
            if o[3] != price:
                self._cancel(oid)
            elif oid not in self.cancelling:
                live += 1
        if live or any(oid in self.cancelling for oid, _ in mine):
            return
        same = 0
        for o in self.orders.values():
            if o[0] == sign:
                same += o[1]
        room = (self.L - self.pos - same) if sign > 0 else (self.L + self.pos - same)
        q = qty if qty < room else room
        if q > 0:
            self._send(sign, q, price, kind, False)

    def _mm(self, t: int, bid: int, ask: int) -> None:
        q = int(MM_Q)
        bp = bid
        ap = ask
        if MM_IMPROVE and ask - bid >= 2:
            bp = bid + 1
            ap = ask - 1
            if ap <= bp:
                ap = bp + 1
        self._quote(1, bp if self.pos <= MM_SKEW else None, q, "mm")
        self._quote(-1, ap if self.pos >= -MM_SKEW else None, q, "mm")

    def _wide(self, t: int, bid: int, ask: int) -> None:
        k = int(WIDE_K)
        q = int(WIDE_Q)
        if self.pos != 0 and t - self.inv_since >= self.wide_exit:
            if not any(o[2] == "ioc" for o in self.orders.values()):
                s = -1 if self.pos > 0 else 1
                for oid, o in list(self.orders.items()):
                    if o[0] == s:
                        self._cancel(oid)
                if not any(o[0] == s for o in self.orders.values()):
                    if s > 0:
                        self._send(1, -self.pos, ask + self.cap, "ioc", True)
                    else:
                        self._send(-1, self.pos, bid - self.cap, "ioc", True)
            return
        self._quote(1, bid - k, q, "wq")
        self._quote(-1, ask + k, q, "wq")

    def diagnostics(self) -> dict:
        return {
            "n_send": self.n_send,
            "n_skip": self.n_skip,
            "n_cancel": self.n_cancel,
            "n_signal": self.n_signal,
            "fill_lots": self.fill_lots,
            "final_pos": self.pos,
        }
