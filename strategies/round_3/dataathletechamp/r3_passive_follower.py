"""R3 passive follower: the D1 informed-flow follower with passive execution variants.

Signal A, per market taker order (trades grouped by taker_order_id, sign from book_side):
  (4th+ consecutive same-sign market taker order and filled >= FILL_MIN)
  or |last - first fill price| >= 2 ticks or filled >= BIG_FILL.  strong = span >= 2 or filled >= BIG_FILL.
D1 state machine: A -> target +-LOTS, same-sign A extends the HOLD_S deadline, opposite A flips the
target, deadline -> target 0.
Execution (module-level flags, read at call time; default = D1):
  EXEC_MODE "ioc": D1. IOC entries at the touch (+ENTRY_CAP), IOC flips at touch -+EXIT_CAP, deadline
                   exit joins the exit-side touch for TOUCH_WAIT_S, then IOC.
            "x1" : passive-first for every need: rest |target - pos| at our touch (bid for buys, ask for
                   sells), keep orders still at/inside the touch, IOC the remainder after FALLBACK_MS.
            "x2" : x1 plus standing MAINT_QTY orders at both touches (aging to the front); excess is shrunk
                   with modify (keeps priority); a side is pulled when the insert-implied FV opposes it
                   by FV_CANCEL ticks (0 = off).
            "x3" : IOC entries (D1), passive-first flips and exits.
            "x4" : IOC entries/flips only for strong signals, passive-first otherwise (exits passive).
            "x5" : cross-and-rest (added after wave 1): entries/flips as a LIMIT at the opposite touch
                   (takes the touch, the remainder rests at the front of the new touch), IOC the
                   remainder after FALLBACK_MS; exits passive-first.
  IOC_DELAY_MS (D1 path only): defer entry/flip IOCs by this many ms (alpha-decay control; 0 = D1).
Inventory discipline: an order is sent only if pos + resting/pending buys <= LOTS and
pos - resting/pending sells >= -LOTS afterwards (worst-case fills); modifies count at the old size
until confirmed.
"""

from __future__ import annotations

from collections import deque

from simulator.models import OrderRequest, OrderStatus, OrderType, Side
from simulator.strategy import BaseStrategy

LOTS = 100
HOLD_S = 5.0
RUN_MIN = 4
FILL_MIN = 100
BIG_FILL = 500
ENTRY_CAP = 0
EXIT_CAP = 3
TOUCH_WAIT_S = 1.0
EXEC_MODE = "ioc"  # ioc | x1 | x2 | x3 | x4 | x5
FALLBACK_MS = 300
REPRICE = True
MAINT_QTY = 50
FV_CANCEL = 0.0
FV_WIN_MS = 50
FV_DEPTH = 2  # ticks beyond each touch scanned for new market inserts
IOC_DELAY_MS = 0  # D1 path control: defer entry/flip IOCs by this many ms after the signal (0 = D1)

# order record fields
_S, _REM, _KIND, _PX, _MID, _IOC, _MOD = 0, 1, 2, 3, 4, 5, 6


class PassiveFollower(BaseStrategy):
    def __init__(self) -> None:
        super().__init__()
        self.pos = 0
        self.orders = {}  # oid -> [sign, remaining, kind, price, mid_at_send, is_ioc, pending_modify_qty]
        self.cancelling = set()
        self.modifying = set()
        self.target = 0
        self.deadline = 0
        self.last_sign = 0
        self.run = 0
        self.wait_until = 0
        self.mid = 0.0
        self.need_t0 = 0
        self.need_ws = 0
        self.need_strong = False
        self.max_id = 0
        self.bins = deque()
        self.ains = deque()
        # diagnostics
        self.n_A_orders = 0
        self.n_sig_lost = 0
        self.n_entry = 0
        self.n_flip = 0
        self.n_episodes = 0
        self.n_sent = 0
        self.n_cancel = 0
        self.n_modify = 0
        self.n_blocked = 0
        self.n_fv_pull = 0
        self.max_expo = 0
        self.fill_stats = {}  # kind -> [lots, cost_ticks_vs_mid_at_send]
        self.t_total = 0
        self.t_ge90 = 0
        self.last_t = 0

    # ---------------- helpers
    def _outstanding(self, s: int) -> int:
        n = 0
        for o in self.orders.values():
            if o[_S] == s:
                n += o[_REM]
        return n

    def _send(self, sign: int, qty: int, price: int, kind: str, ioc: bool) -> None:
        if qty <= 0 or price <= 0:
            return
        buys = self._outstanding(1)
        sells = self._outstanding(-1)
        if sign > 0:
            buys += qty
        else:
            sells += qty
        expo = max(abs(self.pos + buys), abs(self.pos - sells))
        if expo > LOTS:
            self.n_blocked += 1
            return
        if expo > self.max_expo:
            self.max_expo = expo
        oid = self.send_order(
            OrderRequest(
                side=Side.BUY if sign > 0 else Side.SELL,
                price=int(price),
                quantity=int(qty),
                order_type=OrderType.IOC if ioc else OrderType.LIMIT,
            )
        )
        self.n_sent += 1
        self.orders[oid] = [sign, qty, kind, price, self.mid, ioc, 0]

    def _cancel(self, oid: str) -> None:
        if oid not in self.cancelling:
            self.cancelling.add(oid)
            self.n_cancel += 1
            self.cancel_order(oid)

    def _modify(self, oid: str, o: list, new_qty: int) -> None:
        self.modifying.add(oid)
        o[_MOD] = new_qty
        self.n_modify += 1
        self.modify_order(oid, new_qty)

    def _drop(self, oid: str) -> None:
        self.orders.pop(oid, None)
        self.cancelling.discard(oid)
        self.modifying.discard(oid)

    # ---------------- private feed
    def on_private_order_update(self, event) -> None:
        oid = event.order_id
        o = self.orders.get(oid)
        if o is None:
            return
        st = event.status
        if st == OrderStatus.FILLED or st == OrderStatus.PARTIALLY_FILLED:
            q = event.filled_quantity
            s = o[_S]
            self.pos += s * q
            o[_REM] -= q
            fs = self.fill_stats.get(o[_KIND])
            if fs is None:
                fs = [0, 0.0]
                self.fill_stats[o[_KIND]] = fs
            fs[0] += q
            fs[1] += q * s * (event.fill_price - o[_MID])
            if o[_REM] <= 0:
                self._drop(oid)
        elif st == OrderStatus.MODIFIED:
            o[_REM] = event.remaining_quantity
            o[_MOD] = 0
            self.modifying.discard(oid)
        elif st == OrderStatus.CANCELED:
            self._drop(oid)
        elif st == OrderStatus.REJECTED:
            if oid in self.modifying:
                # rejected modify: the order is still resting
                self.modifying.discard(oid)
                o[_MOD] = 0
                if event.remaining_quantity > 0:
                    o[_REM] = event.remaining_quantity
            else:
                self._drop(oid)

    # ---------------- public feed
    def on_order_book_change(self, snapshot, trades) -> None:
        bids = snapshot.bids
        asks = snapshot.asks
        t = snapshot.timestamp_us
        sig = 0
        strong = False
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
                if tr.price < pmin:
                    pmin = tr.price
                elif tr.price > pmax:
                    pmax = tr.price
            if cur is not None:
                groups.append((gs, filled, pmax - pmin))
            for gs, filled, lv in groups:
                if gs == self.last_sign:
                    self.run += 1
                else:
                    self.run = 1
                    self.last_sign = gs
                st_ = lv >= 2 or filled >= BIG_FILL
                if st_ or (self.run >= RUN_MIN and filled >= FILL_MIN):
                    self.n_A_orders += 1
                    sig = gs
                    strong = st_
        if not bids or not asks:
            if sig:
                self.n_sig_lost += 1
            return
        b0 = bids[0]
        if b0.owner == "market":
            bid = b0.price
        else:
            bid = next((o.price for o in bids if o.owner == "market"), 0)
        a0 = asks[0]
        if a0.owner == "market":
            ask = a0.price
        else:
            ask = next((o.price for o in asks if o.owner == "market"), 0)
        if bid <= 0 or ask <= 0:
            return
        if self.last_t:
            dt = t - self.last_t
            self.t_total += dt
            if self.pos >= 90 or self.pos <= -90:
                self.t_ge90 += dt
        self.last_t = t
        self.mid = 0.5 * (bid + ask)
        x2 = EXEC_MODE == "x2"
        if x2 and FV_CANCEL > 0:
            self._scan_inserts(t, bid, ask, bids, asks)
        if sig:
            self._on_signal(t, sig, strong)
        if self.target != 0 and t >= self.deadline:
            self.target = 0
            self.need_t0 = t
        if self.target != self.pos or self.orders or x2:
            if EXEC_MODE == "ioc":
                self._reconcile_d1(t, bid, ask)
            else:
                self._reconcile_px(t, bid, ask)

    def _scan_inserts(self, t: int, bid: int, ask: int, bids, asks) -> None:
        mx = self.max_id
        new_mx = mx
        lim = bid - FV_DEPTH
        for o in bids:
            if o.price < lim:
                break
            if o.owner == "market":
                i = int(o.order_id)
                if i > mx:
                    self.bins.append((t, o.price))
                    if i > new_mx:
                        new_mx = i
        lim = ask + FV_DEPTH
        for o in asks:
            if o.price > lim:
                break
            if o.owner == "market":
                i = int(o.order_id)
                if i > mx:
                    self.ains.append((t, o.price))
                    if i > new_mx:
                        new_mx = i
        self.max_id = new_mx
        old = t - FV_WIN_MS * 1000
        while self.bins and self.bins[0][0] <= old:
            self.bins.popleft()
        while self.ains and self.ains[0][0] <= old:
            self.ains.popleft()

    def _fv(self) -> float:
        if not self.bins or not self.ains:
            return 0.0
        bmax = max(p for _, p in self.bins)
        amin = min(p for _, p in self.ains)
        return 0.5 * (bmax + amin) - self.mid

    def _on_signal(self, t: int, s: int, strong: bool) -> None:
        cur = 1 if self.target > 0 else (-1 if self.target < 0 else 0)
        if cur == s:
            d = t + int(HOLD_S * 1e6)
            if d > self.deadline:
                self.deadline = d
            return
        if cur != 0:
            self.n_flip += 1
        else:
            self.n_entry += 1
        self.target = s * LOTS
        self.deadline = t + int(HOLD_S * 1e6)
        self.wait_until = 0
        self.n_episodes += 1
        self.need_t0 = t
        self.need_strong = strong

    def _classify(self) -> str:
        tg = self.target
        p = self.pos
        if tg == 0 or (p != 0 and (tg > 0) == (p > 0) and abs(tg) < abs(p)):
            return "out"
        if p != 0 and (tg > 0) != (p > 0):
            return "flip"
        return "in"

    # ---------------- D1 execution (EXEC_MODE == "ioc")
    def _reconcile_d1(self, t: int, bid: int, ask: int) -> None:
        if self.cancelling:
            return
        for o in self.orders.values():
            if o[_IOC]:
                return
        want = self.target - self.pos
        resting = list(self.orders.items())
        if want == 0:
            for oid, _ in resting:
                self._cancel(oid)
            return
        ws = 1 if want > 0 else -1
        kind = self._classify()
        if kind == "out":
            px_orders = [oid for oid, o in resting if o[_KIND] == "px"]
            others = [oid for oid, o in resting if o[_KIND] != "px"]
            if others:
                for oid in others:
                    self._cancel(oid)
                return
            if not px_orders:
                if self.wait_until != -1:
                    self._send(ws, abs(want), bid if ws > 0 else ask, "px", False)
                    self.wait_until = t + int(TOUCH_WAIT_S * 1e6)
                    return
            else:
                if t >= self.wait_until:
                    for oid in px_orders:
                        self._cancel(oid)
                    self.wait_until = -1
                return
            lim = ask + EXIT_CAP if ws > 0 else bid - EXIT_CAP
            self._send(ws, abs(want), lim, "ioc_out", True)
            return
        if resting:
            for oid, _ in resting:
                self._cancel(oid)
            return
        if IOC_DELAY_MS and t < self.need_t0 + IOC_DELAY_MS * 1000:
            return
        if kind == "flip":
            lim = ask + EXIT_CAP if ws > 0 else bid - EXIT_CAP
            self._send(ws, abs(want), lim, "ioc_flip", True)
            return
        lim = ask + ENTRY_CAP if ws > 0 else bid - ENTRY_CAP
        self._send(ws, abs(want), lim, "ioc_in", True)

    # ---------------- passive execution (EXEC_MODE x1..x4)
    def _passive_for(self, kind: str) -> bool:
        m = EXEC_MODE
        if m == "x1" or m == "x2" or m == "x5":
            return True
        if m == "x3":
            return kind != "in"
        if m == "x4":
            return kind == "out" or not self.need_strong
        return False

    def _maintain(self, s: int, desired: int, px: int, kind: str, stale_px: int = 0) -> None:
        if not stale_px:
            stale_px = px
        keep = []
        out = 0
        for oid, o in self.orders.items():
            if o[_S] != s:
                continue
            out += o[_REM]
            if oid in self.cancelling:
                continue
            if REPRICE and ((s > 0 and o[_PX] < stale_px) or (s < 0 and o[_PX] > stale_px)):
                self._cancel(oid)
                continue
            keep.append((oid, o))
        eff = 0
        for _, o in keep:
            m = o[_MOD]
            eff += m if (m and m < o[_REM]) else o[_REM]
        if eff > desired:
            excess = eff - desired
            for oid, o in reversed(keep):
                if excess <= 0:
                    break
                m = o[_MOD]
                r = m if (m and m < o[_REM]) else o[_REM]
                if r <= excess:
                    self._cancel(oid)
                    excess -= r
                elif oid not in self.modifying:
                    self._modify(oid, o, r - excess)
                    excess = 0
                else:
                    break
        elif eff < desired:
            room = LOTS - self.pos - out if s > 0 else LOTS + self.pos - out
            q = desired - eff
            if q > room:
                q = room
            if q > 0:
                self._send(s, q, px, kind, False)

    def _reconcile_px(self, t: int, bid: int, ask: int) -> None:
        for o in self.orders.values():
            if o[_IOC]:
                return
        want = self.target - self.pos
        ws = 1 if want > 0 else (-1 if want < 0 else 0)
        if ws != self.need_ws:
            self.need_ws = ws
            self.need_t0 = t
        sb = 0
        sa = 0
        if EXEC_MODE == "x2":
            sb = MAINT_QTY
            sa = MAINT_QTY
            if FV_CANCEL > 0:
                fv = self._fv()
                if fv <= -FV_CANCEL:
                    sb = 0
                    self.n_fv_pull += 1
                elif fv >= FV_CANCEL:
                    sa = 0
                    self.n_fv_pull += 1
        if ws == 0:
            self._maintain(1, sb, bid, "mm")
            self._maintain(-1, sa, ask, "mm")
            return
        kind = self._classify()
        q = abs(want)
        if self._passive_for(kind) and t < self.need_t0 + FALLBACK_MS * 1000:
            if EXEC_MODE == "x5" and kind != "out":
                # cross-and-rest: limit at the opposite touch, remainder rests at the front of the new touch
                if ws > 0:
                    self._maintain(1, q, ask, "c_" + kind, bid)
                    self._maintain(-1, 0, ask, "mm")
                else:
                    self._maintain(-1, q, bid, "c_" + kind, ask)
                    self._maintain(1, 0, bid, "mm")
                return
            if ws > 0:
                self._maintain(1, q if q > sb else sb, bid, "p_" + kind)
                self._maintain(-1, sa, ask, "mm")
            else:
                self._maintain(-1, q if q > sa else sa, ask, "p_" + kind)
                self._maintain(1, sb, bid, "mm")
            return
        # IOC phase: clear our resting orders on the need side, then IOC the remainder
        busy = False
        for oid, o in list(self.orders.items()):
            if o[_S] == ws:
                busy = True
                self._cancel(oid)
        if ws > 0:
            self._maintain(-1, sa, ask, "mm")
        else:
            self._maintain(1, sb, bid, "mm")
        if busy:
            return
        cap = ENTRY_CAP if kind == "in" else EXIT_CAP
        lim = ask + cap if ws > 0 else bid - cap
        self._send(ws, q, lim, "ioc_" + kind, True)

    # ---------------- research diagnostics (not used for trading)
    def diagnostics(self) -> dict:
        kinds = {}
        p_lots = 0
        p_cost = 0.0
        i_lots = 0
        i_cost = 0.0
        for k, v in self.fill_stats.items():
            kinds[k] = {"lots": v[0], "cost_per_lot": round(v[1] / v[0], 4) if v[0] else None}
            if k.startswith("ioc"):
                i_lots += v[0]
                i_cost += v[1]
            else:
                p_lots += v[0]
                p_cost += v[1]
        tot = p_lots + i_lots
        return {
            "exec_mode": EXEC_MODE,
            "n_A_orders": self.n_A_orders,
            "n_sig_lost": self.n_sig_lost,
            "n_entry": self.n_entry,
            "n_flip": self.n_flip,
            "n_episodes": self.n_episodes,
            "passive_lots": p_lots,
            "ioc_lots": i_lots,
            "passive_share": round(p_lots / tot, 4) if tot else None,
            "cost_per_lot_passive": round(p_cost / p_lots, 4) if p_lots else None,
            "cost_per_lot_ioc": round(i_cost / i_lots, 4) if i_lots else None,
            "cost_per_lot_all": round((p_cost + i_cost) / tot, 4) if tot else None,
            "cost_total": round(p_cost + i_cost, 1),
            "kinds": kinds,
            "time_absI_ge90": round(self.t_ge90 / self.t_total, 4) if self.t_total else None,
            "max_expo": self.max_expo,
            "n_blocked": self.n_blocked,
            "n_sent": self.n_sent,
            "n_cancel": self.n_cancel,
            "n_modify": self.n_modify,
            "n_fv_pull": self.n_fv_pull,
        }
