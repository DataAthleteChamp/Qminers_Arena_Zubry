"""R3 aged-queue maker, best config as DEFAULT (KEEP_AGED, age 150 ms, 100 ms fill cooldown).

Validation probe copy of r3_aged_maker.py: only KEEP_AGED, AGE_KEEP_US and FILL_COOLDOWN_US defaults
differ. The text below describes the original file whose defaults were M1.

Original: R3 aged-queue maker (research strategy, default = M1 FV-gated touch maker).

Default behaviour (all new mechanisms off) reproduces M1_q20_fv05 of experiment
20261108-r3-gated-maker-official-001: one LIMIT of Q lots per side at the market touch, re-priced only
when the touch moved away, cancelled/blocked while the insert-implied fair value FV opposes the side by
>= FV_CANCEL ticks.  FV = (max price of NEW bid inserts in the last FV_WIN_US + min price of NEW ask
inserts in the last FV_WIN_US)/2 - market mid (0 when either side had no new insert).  Exposure
inv + resting/in-flight buys <= CAP and inv - resting/in-flight sells >= -CAP at all times.

Default-off mechanisms (module constants, read when the strategy is constructed):
  A1 PRE_TICKS>0  keep orders of Q_PRE lots at touch-1..touch-PRE_TICKS (bid; ask mirrored) so that they
                  age and collect queue behind them before the price reaches them; cancel them when
                  -s*FV >= PRE_FV_CANCEL, on a signal-A sweep against the side (A_GUARD) or when they are
                  more than MAX_DIST ticks behind the touch.  A touch order whose touch moved away by
                  <= PRE_TICKS ticks is kept (demoted to a pre order) instead of being re-priced.
  A2 KEEP_AGED    an order aged >= AGE_KEEP_US with >= QB_MIN market lots behind it is only cancelled when
                  -s*FV >= FV_STRONG (and is kept up to MAX_DIST ticks behind the touch instead of being
                  re-priced); JOIN_AGREE: new touch orders are only sent when s*FV > 0; YOUNG_CXL: orders
                  at the touch younger than AGE_KEEP_US are cancelled while s*FV <= 0.
  A2b TOUCH_AGE_MIN_US>0: a new touch order is only sent once the market touch price of that side has been
                  unchanged for >= TOUCH_AGE_MIN_US (do not chase fresh levels); FILL_COOLDOWN_US>0: no new touch
                  order on a side within FILL_COOLDOWN_US of our last fill on that side (fills cluster in sweeps).
  A3 Q_TOUCH>0    size of new (young) touch orders; pre-positioned orders keep Q_PRE.
  A4 UNWIND       the inventory-reducing side ignores JOIN_AGREE/YOUNG_CXL and sends max(size, min(|inv|,
                  UNW_MAX)) lots; IOC-reduce to STUCK_TO at the opposite touch -/+ EXIT_SLIP when |inv| >= CAP
                  for >= STUCK_US.
diagnostics() returns 1 s markouts (ticks/lot, vs market mid) of own fills by order age, role, queue-behind
and FV state.
"""

from __future__ import annotations

from collections import deque
from operator import attrgetter

from simulator.models import OrderBookSnapshot, OrderRequest, OrderStatus, OrderType, PrivateOrderEvent, Side, Trade
from simulator.strategy import BaseStrategy

# ---------------------------------------------------------------- base (M1)
Q = 20
CAP = 80
FV_GATE = True
FV_CANCEL = 0.5
FV_WIN_US = 50_000
# signal-A guard (off)
A_GUARD = False
GUARD_US = 200_000
A_RUN_MIN = 4
A_FILL_MIN = 100
A_SWEEP = 2
A_BIG = 500
# A1 pre-position
PRE_TICKS = 0
Q_PRE = 20
PRE_FV_CANCEL = 0.5
MAX_DIST = 2
TOUCH_JOIN = True
# A2 keep aged
KEEP_AGED = True
AGE_KEEP_US = 150_000
QB_MIN = 300
FV_STRONG = 1.5
JOIN_AGREE = False
YOUNG_CXL = False
TOUCH_AGE_MIN_US = 0
FILL_COOLDOWN_US = 100_000
# A3 size by age
Q_TOUCH = 0
# A4 passive unwind
UNWIND = False
UNW_MAX = 60
STUCK_US = 5_000_000
STUCK_TO = 40
EXIT_SLIP = 2
# diagnostics
MARKOUT_US = 1_000_000
FIT_SPLIT_US = 2_400_000_000

_GID = attrgetter("order_id")
_GPX = attrgetter("price")
_FILLS = (OrderStatus.PARTIALLY_FILLED, OrderStatus.FILLED)
# order record indices
S, REM, PX, CXL, ROLE, ACC, TACC, MOD, QA, QB = range(10)
MAINR, KEPTR, IOCR = 0, 1, 2
_ROLE_NAME = ("main", "kept", "ioc")


def _age_bucket(age: int) -> str:
    if age < 0:
        return "na"
    if age < 100_000:
        return "lt100ms"
    if age < 300_000:
        return "lt300ms"
    if age < 1_000_000:
        return "lt1s"
    return "ge1s"


class AgedMaker(BaseStrategy):
    def __init__(self) -> None:
        super().__init__()
        self.q = int(Q)
        self.cap = int(CAP)
        self.fv_gate = bool(FV_GATE)
        self.fv_cut = float(FV_CANCEL)
        self.fv_win = int(FV_WIN_US)
        self.a_guard = bool(A_GUARD)
        self.guard_us = int(GUARD_US)
        self.pre_ticks = int(PRE_TICKS)
        self.q_pre = int(Q_PRE)
        self.pre_cut = float(PRE_FV_CANCEL)
        self.max_dist = int(MAX_DIST)
        self.touch_join = bool(TOUCH_JOIN)
        self.keep_aged = bool(KEEP_AGED)
        self.age_keep = int(AGE_KEEP_US)
        self.qb_min = int(QB_MIN)
        self.fv_strong = float(FV_STRONG)
        self.join_agree = bool(JOIN_AGREE)
        self.young_cxl = bool(YOUNG_CXL)
        self.touch_age_min = int(TOUCH_AGE_MIN_US)
        self.fill_cd = int(FILL_COOLDOWN_US)
        self.touch_px = {1: 0, -1: 0}
        self.touch_since = {1: 0, -1: 0}
        self.last_fill = {1: -(10**18), -1: -(10**18)}
        self.q_touch = int(Q_TOUCH) if int(Q_TOUCH) > 0 else self.q
        self.unwind = bool(UNWIND)
        self.unw_max = int(UNW_MAX)
        self.stuck_us = int(STUCK_US)
        self.stuck_to = int(STUCK_TO)
        self.exit_slip = int(EXIT_SLIP)
        self.mo_us = int(MARKOUT_US)
        self.fit_split_us = int(FIT_SPLIT_US)
        if self.cap <= 0 or self.q <= 0 or self.q_pre <= 0 or self.max_dist < 0 or self.pre_ticks < 0:
            raise ValueError("invalid size/cap/distance parameters")
        if self.pre_ticks > self.max_dist:
            raise ValueError("PRE_TICKS must be <= MAX_DIST")
        self.inv = 0
        self.cash = 0.0
        self.pend = {1: 0, -1: 0}
        self.orders: dict[str, list] = {}
        self.main: dict[int, str | None] = {1: None, -1: None}
        self.kept: dict[int, dict[str, bool]] = {1: {}, -1: {}}
        self.n_ioc = 0
        # feed state
        self.mid = 0.0
        self.prev_lists: dict[int, list] = {1: [], -1: []}
        self.prev_ids: dict[int, dict] = {1: {}, -1: {}}
        self.max_id = 0
        self.ins_bid: deque = deque()
        self.ins_ask: deque = deque()
        self.fv = 0.0
        self.run_sign = 0
        self.run_len = 0
        self.guard_until = {1: -1, -1: -1}
        self.stuck_since: int | None = None
        # diagnostics
        self.st: dict[str, int] = {}
        self.pending_mo: deque = deque()
        self.mo_sum: dict[str, float] = {}
        self.mo_lots: dict[str, int] = {}
        self.fills_n = 0
        self.lots = 0
        self.max_abs_exposure = 0
        self.last_t: int | None = None
        self.span_us = 0
        self.cap_us = 0
        self.abs_inv_us = 0

    # ------------------------------------------------------------------ helpers
    def _c(self, key: str, n: int = 1) -> None:
        self.st[key] = self.st.get(key, 0) + n

    def _room(self, s: int) -> int:
        if s > 0:
            return self.cap - (self.inv + self.pend[1])
        return self.cap + (self.inv - self.pend[-1])

    def _send(self, s: int, qty: int, price: int, role: int) -> str | None:
        q = min(qty, self._room(s))
        if q <= 0 or price <= 0:
            return None
        oid = self.send_order(OrderRequest(side=Side.BUY if s > 0 else Side.SELL, price=price, quantity=q,
                                           order_type=OrderType.IOC if role == IOCR else OrderType.LIMIT))
        self.orders[oid] = [s, q, price, False, role, False, -1, False, -1, -1]
        self.pend[s] += q
        expo = max(self.inv + self.pend[1], -(self.inv - self.pend[-1]))
        if expo > self.max_abs_exposure:
            self.max_abs_exposure = expo
        if expo > self.cap:
            raise RuntimeError("exposure above CAP")
        if role == IOCR:
            self.n_ioc += 1
        elif role == MAINR:
            self.main[s] = oid
            self._c("sent_main")
        else:
            self.kept[s][oid] = True
            self._c("sent_pre")
        return oid

    def _cancel(self, oid: str, why: str) -> None:
        rec = self.orders[oid]
        if rec[CXL]:
            return
        rec[CXL] = True
        self.cancel_order(oid)
        self._c("cxl_" + why)

    def _drop(self, oid: str, rec: list) -> None:
        del self.orders[oid]
        s = rec[S]
        if self.main[s] == oid:
            self.main[s] = None
        self.kept[s].pop(oid, None)
        if rec[ROLE] == IOCR:
            self.n_ioc -= 1

    # ------------------------------------------------------------------ private feed
    def on_private_order_update(self, event: PrivateOrderEvent) -> None:
        oid = event.order_id
        rec = self.orders.get(oid)
        if rec is None:
            return
        status = event.status
        s = rec[S]
        if status in _FILLS:
            q = event.filled_quantity
            px = event.fill_price or 0
            self.inv += s * q
            self.cash -= s * q * px
            rec[REM] -= q
            self.pend[s] -= q
            self.fills_n += 1
            self.lots += q
            self.last_fill[s] = event.timestamp_us
            v = s * self.fv
            fv_state = "agree" if v > 0 else ("oppose" if v < 0 else "neutral")
            role = _ROLE_NAME[rec[ROLE]]
            b = rec[QB]
            qb_state = "ioc" if rec[ROLE] == IOCR else (
                "unk" if b < 0 else ("ge_min" if b >= self.qb_min else ("1_to_min" if b > 0 else "0")))
            ab = _age_bucket(event.timestamp_us - rec[TACC] if rec[TACC] >= 0 else -1)
            self.pending_mo.append((event.timestamp_us, s, px, q, fv_state, qb_state, ab, role))
            if status == OrderStatus.FILLED:
                self._drop(oid, rec)
        elif status == OrderStatus.ACCEPTED:
            rec[ACC] = True
            rec[TACC] = event.timestamp_us
        elif status == OrderStatus.CANCELED:
            self.pend[s] -= rec[REM]
            self._drop(oid, rec)
        elif status == OrderStatus.MODIFIED:
            new_rem = event.remaining_quantity
            self.pend[s] -= rec[REM] - new_rem
            rec[REM] = new_rem
            rec[MOD] = False
        elif status == OrderStatus.REJECTED:
            if rec[MOD] and event.remaining_quantity > 0 and event.message is None:
                rec[MOD] = False
                self._c("modify_rejected")
                return
            self._c("rejected")
            self.pend[s] -= rec[REM]
            self._drop(oid, rec)

    # ------------------------------------------------------------------ public feed
    def _new_inserts(self, s: int, lst: list, t: int) -> None:
        ids = dict(zip(map(_GID, lst), map(_GPX, lst)))
        prev = self.prev_ids[s]
        self.prev_ids[s] = ids
        new = ids.keys() - prev.keys()
        if not new:
            return
        mx = self.max_id
        dq = self.ins_bid if s > 0 else self.ins_ask
        for oid in new:
            if oid[0] == "u":
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

    def _queue_state(self, s: int, lst: list) -> None:
        """Market lots ahead of / behind each of our accepted resting orders on side s (one pass)."""
        mine = {}
        o = self.main[s]
        if o is not None:
            rec = self.orders[o]
            if rec[ACC]:
                mine[o] = rec
        for o in self.kept[s]:
            rec = self.orders[o]
            if rec[ACC]:
                mine[o] = rec
        if not mine:
            return
        deepest = 0
        for rec in mine.values():
            rec[QA] = rec[QB] = -1
            p = rec[PX]
            if not deepest or (s > 0 and p < deepest) or (s < 0 and p > deepest):
                deepest = p
        cur = None
        lvl = 0
        ours: list = []
        for v in lst:
            vp = v.price
            if vp != cur:
                for rec, before in ours:
                    rec[QA] = before
                    rec[QB] = lvl - before
                ours = []
                if (s > 0 and vp < deepest) or (s < 0 and vp > deepest):
                    break
                cur = vp
                lvl = 0
            if v.owner == "market":
                lvl += v.quantity
            else:
                rec = mine.get(v.order_id)
                if rec is not None:
                    ours.append((rec, lvl))
        for rec, before in ours:
            rec[QA] = before
            rec[QB] = lvl - before

    def on_order_book_change(self, snapshot: OrderBookSnapshot, trades: list[Trade]) -> None:
        t = snapshot.timestamp_us
        if self.last_t is not None:
            dt = t - self.last_t
            if dt:
                ai = abs(self.inv)
                self.span_us += dt
                self.abs_inv_us += ai * dt
                if ai >= self.cap:
                    self.cap_us += dt
        self.last_t = t
        # ---------------- markouts (mid standing just before this event)
        pm = self.pending_mo
        if pm and pm[0][0] + self.mo_us <= t:
            mid0 = self.mid
            split = self.fit_split_us
            while pm and pm[0][0] + self.mo_us <= t:
                tf, s, px, q, fs, qs, ab, rl = pm.popleft()
                mo = s * (mid0 - px) * q
                w = "fit" if tf < split else "eval"
                for key in ("all|" + w, "fv:" + fs + "|" + w, "qb:" + qs + "|" + w, "age:" + ab + "|" + w,
                            "role:" + rl + "|" + w, "roleage:" + rl + ":" + ab + "|" + w):
                    self.mo_sum[key] = self.mo_sum.get(key, 0.0) + mo
                    self.mo_lots[key] = self.mo_lots.get(key, 0) + q
        # ---------------- signal A (market takers only)
        if trades and self.a_guard:
            a_sign = 0
            cur = None
            filled = first = last = sgn = 0
            groups = []
            for tr in trades:
                if tr.taker_owner != "market":
                    continue
                if tr.taker_order_id != cur:
                    if cur is not None:
                        groups.append((sgn, filled, abs(last - first)))
                    cur = tr.taker_order_id
                    sgn = 1 if tr.book_side == "ask" else -1
                    filled = 0
                    first = tr.price
                filled += tr.quantity
                last = tr.price
            if cur is not None:
                groups.append((sgn, filled, abs(last - first)))
            for sgn, filled, lev in groups:
                if sgn == self.run_sign:
                    self.run_len += 1
                else:
                    self.run_sign = sgn
                    self.run_len = 1
                if ((self.run_len >= A_RUN_MIN and filled >= A_FILL_MIN) or lev >= A_SWEEP
                        or filled >= A_BIG):
                    a_sign = sgn
            if a_sign:
                self._c("A_signals")
                self.guard_until[-a_sign] = t + self.guard_us
        bids, asks = snapshot.bids, snapshot.asks
        ch_b = bids != self.prev_lists[1]
        ch_a = asks != self.prev_lists[-1]
        if ch_b:
            self._new_inserts(1, bids, t)
            self.prev_lists[1] = bids
        if ch_a:
            self._new_inserts(-1, asks, t)
            self.prev_lists[-1] = asks
        bbm = bam = 0
        for v in bids:
            if v.owner == "market":
                bbm = v.price
                break
        for v in asks:
            if v.owner == "market":
                bam = v.price
                break
        if not bbm or not bam:
            return
        if bbm != self.touch_px[1]:
            self.touch_px[1] = bbm
            self.touch_since[1] = t
        if bam != self.touch_px[-1]:
            self.touch_px[-1] = bam
            self.touch_since[-1] = t
        mid = (bbm + bam) / 2.0
        self.mid = mid
        lo = t - self.fv_win
        db, da = self.ins_bid, self.ins_ask
        while db and db[0][0] <= lo:
            db.popleft()
        while da and da[0][0] <= lo:
            da.popleft()
        fv = (db[0][1] + da[0][1]) / 2.0 - mid if (db and da) else 0.0
        self.fv = fv
        if ch_b:
            self._queue_state(1, bids)
        if ch_a:
            self._queue_state(-1, asks)
        # ---------------- A4 stuck reduce
        inv = self.inv
        if self.unwind:
            if abs(inv) >= self.cap:
                if self.stuck_since is None:
                    self.stuck_since = t
                elif t - self.stuck_since >= self.stuck_us and not self.n_ioc:
                    u = -1 if inv > 0 else 1
                    px = bam + self.exit_slip if u > 0 else bbm - self.exit_slip
                    if self._send(u, abs(inv) - self.stuck_to, px, IOCR):
                        self._c("stuck_reduce")
            else:
                self.stuck_since = None
        # ---------------- per-side quoting
        orders = self.orders
        for s in (1, -1):
            touch = bbm if s > 0 else bam
            opp = -s * fv
            guarded = self.a_guard and t < self.guard_until[s]
            reducing = self.unwind and inv * s < 0
            kd = self.kept[s]
            have_touch = False
            if kd:
                for oid in list(kd):
                    rec = orders[oid]
                    dist = s * (touch - rec[PX])
                    if rec[CXL] or rec[MOD]:
                        continue
                    aged = rec[ACC] and t - rec[TACC] >= self.age_keep
                    strong = self.keep_aged and aged and rec[QB] >= self.qb_min
                    if self.fv_gate and opp >= (self.fv_strong if strong else self.pre_cut):
                        self._cancel(oid, "kfv")
                    elif guarded and not strong:
                        self._cancel(oid, "ka")
                    elif dist > self.max_dist:
                        self._cancel(oid, "kdist")
                    elif self.young_cxl and dist <= 0 and not aged and s * fv <= 0 and not reducing:
                        self._cancel(oid, "kyoung")
                    elif dist <= 0:
                        have_touch = True
            o = self.main[s]
            if o is not None:
                rec = orders[o]
                if rec[CXL] or rec[MOD]:
                    continue
                aged = rec[ACC] and t - rec[TACC] >= self.age_keep
                strong = self.keep_aged and aged and rec[QB] >= self.qb_min
                dist = s * (touch - rec[PX])
                if self.fv_gate and opp >= (self.fv_strong if strong else self.fv_cut):
                    self._cancel(o, "fv")
                    continue
                if guarded and not strong:
                    self._cancel(o, "a")
                    continue
                if dist > 0:
                    if dist <= self.max_dist and (dist <= self.pre_ticks or strong):
                        rec[ROLE] = KEPTR
                        self.main[s] = None
                        kd[o] = True
                        self._c("demote")
                    else:
                        self._cancel(o, "reprice")
                        continue
                elif self.young_cxl and not aged and s * fv <= 0 and not reducing:
                    self._cancel(o, "young")
                    continue
                else:
                    continue
            # ---- placement
            if guarded or (self.fv_gate and opp >= self.fv_cut):
                blocked_main = True
            else:
                blocked_main = False
            if (self.touch_join and not blocked_main and not have_touch and self.main[s] is None
                    and t - self.touch_since[s] >= self.touch_age_min and t - self.last_fill[s] >= self.fill_cd):
                ok = True
                if (self.join_agree or self.young_cxl) and not reducing and s * fv <= 0:
                    ok = False
                if ok:
                    size = self.q_touch
                    if reducing:
                        size = max(size, min(abs(inv), self.unw_max))
                    self._send(s, size, touch, MAINR)
            if self.pre_ticks and not guarded and not (self.fv_gate and opp >= self.pre_cut):
                taken = set()
                for oid in kd:
                    taken.add(orders[oid][PX])
                o = self.main[s]
                if o is not None:
                    taken.add(orders[o][PX])
                for k in range(1, self.pre_ticks + 1):
                    px = touch - s * k
                    if px in taken:
                        continue
                    size = self.q_pre
                    if reducing:
                        size = max(size, min(abs(inv), self.unw_max))
                    if self._send(s, size, px, KEPTR) is None:
                        break

    # ------------------------------------------------------------------ reporting
    def diagnostics(self) -> dict[str, object]:
        span = max(self.span_us, 1)
        mo = {k: {"lots": self.mo_lots[k], "ticks_per_lot": round(self.mo_sum[k] / self.mo_lots[k], 4)}
              for k in sorted(self.mo_lots)}
        return {
            "stats": dict(sorted(self.st.items())),
            "fill_events": self.fills_n,
            "lots_strategy_ledger": self.lots,
            "markout_1s": mo,
            "time_share_abs_inv_ge_cap": self.cap_us / span,
            "mean_abs_inventory": self.abs_inv_us / span,
            "max_abs_exposure_incl_pending": self.max_abs_exposure,
            "final_inventory_strategy_ledger": self.inv,
            "cash_strategy_ledger": self.cash,
        }

