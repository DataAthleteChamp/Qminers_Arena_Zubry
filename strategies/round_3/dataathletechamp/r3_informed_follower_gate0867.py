"""Round 3 informed-taker follower ("D1", hold 5 s, join-touch exit) - standalone submission file.

Variant of r3_informed_follower.py with REGIME_GATE_MIN_A_PER_S = 0.867 and
CANCEL_STALE_EXIT = True; all other code and constants identical.

Mechanism (port of the D1 path of research harness 20261108-r3-follow-exit-optimization-001):
  Signal A, per market taker order (trades of one callback grouped by consecutive taker_order_id,
  direction from the side of the book that was hit, our own taker trades excluded):
      (position in a run of consecutive same-direction market taker orders >= RUN_MIN
       and filled quantity >= FILL_MIN)
      or first-to-last fill price span >= SPAN_TICKS
      or filled quantity >= BIG_FILL.
  State machine: A from flat -> target = sign * MAX_LOTS, taken by IOC at the current touch
  (+ ENTRY_CAP_TICKS); same-direction A extends the HOLD_S deadline; opposite A flips (IOC at
  touch +/- FLIP_CAP_TICKS); at the deadline the position is offered passively at the exit-side
  touch for EXIT_TOUCH_WAIT_S, then the remainder is sent as an IOC.
  Exposure invariant: position + in-flight + resting orders never exceed +/-MAX_LOTS (<= 100).

Default-off robustness flags:
  REGIME_GATE_MIN_A_PER_S  > 0: count of A orders in the last REGIME_GATE_WINDOW_S seconds divided
                           by the window; below the threshold no new position is opened, holds are
                           not extended and an opposite A closes instead of flipping.
  STRONG_FLIP_ONLY         True: flip only on strong A (span >= SPAN_TICKS or filled >= BIG_FILL);
                           weaker opposite A is ignored.
  CANCEL_STALE_EXIT        True: cancel a resting touch-exit order when the target is
                           re-established.

All parameters are module-level constants read at call time.
"""

from __future__ import annotations

from collections import deque

from simulator.models import OrderRequest, OrderStatus, OrderType, Side
from simulator.strategy import BaseStrategy

# ---- signal A
RUN_MIN = 4
FILL_MIN = 100
SPAN_TICKS = 2
BIG_FILL = 500
# ---- position and execution
MAX_LOTS = 100  # clamped to [0, 100]
HOLD_S = 5.0
ENTRY_CAP_TICKS = 0
FLIP_CAP_TICKS = 3  # flips and IOC exits: limit = touch +/- this many ticks
EXIT_MODE = "touch"  # "touch" (join exit-side touch, then IOC) | "ioc"
EXIT_TOUCH_WAIT_S = 1.0
# ---- default-off flags
STRONG_FLIP_ONLY = False
REGIME_GATE_MIN_A_PER_S = 0.867  # 0 = off; this variant: gate on (R3-fit low/mid informed tercile)
REGIME_GATE_WINDOW_S = 120.0
CANCEL_STALE_EXIT = True  # this variant: on

_HARD_LIMIT = 100
_K_IN = 1
_K_OUT = 2
_K_FLIP = 3
_K_PX = 4


def _lots() -> int:
    lots = int(MAX_LOTS)
    if lots < 0:
        return 0
    if lots > _HARD_LIMIT:
        return _HARD_LIMIT
    return lots


class InformedFollower(BaseStrategy):
    """Follow informed market taker orders with a +/-MAX_LOTS position held HOLD_S seconds."""

    def __init__(self) -> None:
        super().__init__()
        self.pos = 0
        self.orders: dict[str, list[int]] = {}  # oid -> [sign, remaining, kind]
        self.sides: dict[str, int] = {}  # oid -> sign, kept for fill accounting
        self.cancelling: set[str] = set()
        self.target = 0
        self.deadline = 0
        self.last_sign = 0
        self.run = 0
        self.wait_until = 0
        self.a_times: deque[int] = deque()
        self.last_t = -1
        # diagnostics (cheap counters)
        self.n_a = 0
        self.n_sig = 0
        self.n_sig_lost = 0
        self.n_entry = 0
        self.n_flip = 0
        self.n_weak_flip_ignored = 0
        self.n_gate_blocked = 0
        self.n_gate_flat = 0
        self.n_orders = 0
        self.max_expo = 0
        self.gate_closed_us = 0
        self.gate_seen_us = 0

    # ------------------------------------------------------------------ private feed
    def on_private_order_update(self, event) -> None:
        oid = event.order_id
        st = event.status
        if st == OrderStatus.FILLED or st == OrderStatus.PARTIALLY_FILLED:
            q = event.filled_quantity or 0
            o = self.orders.get(oid)
            s = o[0] if o is not None else self.sides.get(oid, 0)
            if q <= 0 or s == 0:
                return
            self.pos += s * q
            if o is not None:
                o[1] -= q
                if o[1] <= 0:
                    del self.orders[oid]
                    self.cancelling.discard(oid)
        elif st == OrderStatus.CANCELED or st == OrderStatus.REJECTED:
            self.orders.pop(oid, None)
            self.cancelling.discard(oid)

    # ------------------------------------------------------------------ public feed
    def on_order_book_change(self, snapshot, trades) -> None:
        t = snapshot.timestamp_us
        sig = 0
        strong = False
        gate_min = REGIME_GATE_MIN_A_PER_S
        if trades:
            cur = None
            gs = 0
            filled = 0
            pmin = 0
            pmax = 0
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
                    pmin = tr.price
                    pmax = tr.price
                filled += tr.quantity
                if tr.price < pmin:
                    pmin = tr.price
                elif tr.price > pmax:
                    pmax = tr.price
            if cur is not None:
                groups.append((gs, filled, pmax - pmin))
            for gs, filled, span in groups:
                if gs == self.last_sign:
                    self.run += 1
                else:
                    self.run = 1
                    self.last_sign = gs
                is_strong = span >= SPAN_TICKS or filled >= BIG_FILL
                if is_strong or (self.run >= RUN_MIN and filled >= FILL_MIN):
                    self.n_a += 1
                    if gate_min > 0:
                        self.a_times.append(t)
                    sig = gs
                    strong = is_strong
        gate_open = True
        if gate_min > 0:
            window_s = REGIME_GATE_WINDOW_S
            horizon = t - int(window_s * 1e6)
            at = self.a_times
            while at and at[0] <= horizon:
                at.popleft()
            gate_open = len(at) >= gate_min * window_s
            if self.last_t >= 0 and t > self.last_t:
                dt = t - self.last_t
                self.gate_seen_us += dt
                if not gate_open:
                    self.gate_closed_us += dt
        self.last_t = t
        bids = snapshot.bids
        asks = snapshot.asks
        if not bids or not asks:
            if sig:
                self.n_sig_lost += 1
            return
        bid = 0
        for o in bids:
            if o.owner == "market":
                bid = o.price
                break
        ask = 0
        for o in asks:
            if o.owner == "market":
                ask = o.price
                break
        if bid <= 0 or ask <= 0 or bid >= ask:
            return
        if sig:
            self._on_signal(t, sig, strong, gate_open)
        if self.target != 0 and t >= self.deadline:
            self.target = 0
        if self.target != self.pos or self.orders:
            self._reconcile(t, bid, ask)

    # ------------------------------------------------------------------ logic
    def _on_signal(self, t: int, s: int, strong: bool, gate_open: bool) -> None:
        self.n_sig += 1
        cur = 1 if self.target > 0 else (-1 if self.target < 0 else 0)
        hold_us = int(HOLD_S * 1e6)
        if cur == s:
            if gate_open:
                self.deadline = t + hold_us
            return
        if cur != 0 and STRONG_FLIP_ONLY and not strong:
            self.n_weak_flip_ignored += 1
            return
        if not gate_open:
            if cur == 0:
                self.n_gate_blocked += 1
            else:
                self.n_gate_flat += 1
                self.target = 0
            return
        if cur == 0:
            self.n_entry += 1
        else:
            self.n_flip += 1
        self.target = s * _lots()
        self.deadline = t + hold_us
        self.wait_until = 0

    def _reconcile(self, t: int, bid: int, ask: int) -> None:
        if self.cancelling:
            return
        for o in self.orders.values():
            if o[2] != _K_PX:
                return  # an IOC is in flight
        want = self.target - self.pos
        if want == 0:
            if self.orders and (self.pos == 0 or CANCEL_STALE_EXIT):
                self._cancel_all()
            return
        ws = 1 if want > 0 else -1
        exiting = self.target == 0 or (
            self.pos != 0
            and (self.target > 0) == (self.pos > 0)
            and abs(self.target) < abs(self.pos)
        )
        flipping = self.pos != 0 and self.target != 0 and (self.target > 0) != (self.pos > 0)
        if exiting:
            if EXIT_MODE == "touch":
                if self.orders:
                    if t >= self.wait_until:
                        self._cancel_all()
                        self.wait_until = -1
                    return
                if self.wait_until != -1:
                    self._send(ws, abs(want), bid if ws > 0 else ask, _K_PX, False)
                    self.wait_until = t + int(EXIT_TOUCH_WAIT_S * 1e6)
                    return
            elif self.orders:
                self._cancel_all()
                return
            cap = FLIP_CAP_TICKS
            self._send(ws, abs(want), ask + cap if ws > 0 else bid - cap, _K_OUT, True)
            return
        if flipping:
            if self.orders:
                self._cancel_all()
                return
            cap = FLIP_CAP_TICKS
            self._send(ws, abs(want), ask + cap if ws > 0 else bid - cap, _K_FLIP, True)
            return
        if CANCEL_STALE_EXIT and self.orders:
            self._cancel_all()
            return
        cap = ENTRY_CAP_TICKS
        self._send(ws, abs(want), ask + cap if ws > 0 else bid - cap, _K_IN, True)

    # ------------------------------------------------------------------ order helpers
    def _send(self, sign: int, qty: int, price: int, kind: int, ioc: bool) -> None:
        lots = _lots()
        buys = 0
        sells = 0
        for o in self.orders.values():
            if o[0] > 0:
                buys += o[1]
            else:
                sells += o[1]
        if sign > 0:
            room = lots - (self.pos + buys)
        else:
            room = lots + (self.pos - sells)
        if qty > room:
            qty = room
        if qty <= 0:
            return
        price = int(price)
        if price < 1:
            price = 1
        oid = self.send_order(
            OrderRequest(
                side=Side.BUY if sign > 0 else Side.SELL,
                price=price,
                quantity=int(qty),
                order_type=OrderType.IOC if ioc else OrderType.LIMIT,
            )
        )
        self.orders[oid] = [sign, int(qty), kind]
        self.sides[oid] = sign
        self.n_orders += 1
        if sign > 0:
            buys += qty
        else:
            sells += qty
        expo = max(abs(self.pos + buys), abs(self.pos - sells))
        if expo > self.max_expo:
            self.max_expo = expo

    def _cancel_all(self) -> None:
        for oid in list(self.orders):
            if oid not in self.cancelling:
                self.cancelling.add(oid)
                self.cancel_order(oid)

    def diagnostics(self) -> dict:
        seen = self.gate_seen_us
        return {
            "A_orders": self.n_a,
            "signals_acted_on_book": self.n_sig,
            "signals_lost_one_sided_book": self.n_sig_lost,
            "entries_from_flat": self.n_entry,
            "flips": self.n_flip,
            "weak_flips_ignored": self.n_weak_flip_ignored,
            "gate_blocked_entries": self.n_gate_blocked,
            "gate_flat_on_opposite": self.n_gate_flat,
            "gate_closed_frac": (self.gate_closed_us / seen) if seen > 0 else None,
            "orders_sent": self.n_orders,
            "max_exposure_incl_pending": self.max_expo,
            "final_pos": self.pos,
            "open_orders_at_end": len(self.orders),
        }
