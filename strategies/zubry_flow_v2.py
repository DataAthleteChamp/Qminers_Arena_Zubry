"""Penalty-aware flow taker (v2 of zubry_flow.py).

Same tape-specific signal as v1: external aggressive flow (Lifespan F) predicts a
same-direction move on data/round0/sample.csv. It did NOT transfer to sample_v2.csv.
What v2 adds is the penalty/latency discipline from the penalty-aware research note:

* Exposure ledger: every IOC in flight counts at FULL size until a terminal state.
  Worst case is judged one-sided (buys and sells never net each other out).
* Safe budgets: new orders are clipped to the headroom left under MAX_INV (<= 100).
* The penalty is a flat 10,000 PnL/s once |inventory| > 100, not per lot. So the
  sizing target is "never be there", and RECOVER mode only sells/buys the minimum
  number of lots that returns to +/-100.
* Deliberate breach is behind ENABLE_BREACH (off) with the incremental-EV gate
  A > 10,000 * tau_p90 + U. It is preserved as a mechanism, not claimed as alpha.
* Inventory changes only on private fills, never on sent orders.
"""

from __future__ import annotations

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

# --- risk constants from the rules (microseconds) ---
SAFE_POS = 100
HARD_ACCEPTANCE_POS = 1000
PENALTY_PER_US = 0.01  # 10,000 per second

# --- strategy parameters (few on purpose) ---
LOT = 5
MAX_INV = 40  # internal worst-case cap incl. in-flight; must stay <= SAFE_POS
HOLD_US = 5_000_000
RETRY_US = 50_000
ENTRY_SLACK = 0  # ticks; IOC fills at resting prices, slack only buys fill probability
EXIT_SLACK = 2  # a missed exit costs time; slack is free while depth is sufficient

# --- flagged mechanism: deliberate breach (disabled) ---
ENABLE_BREACH = False
BREACH_MODEL_RESERVE = 100.0  # U, PnL units
BREACH_EDGE_PER_LOT = 0.0  # A per lot; 0 = no credible edge estimate, so gate never opens
BREACH_P90_US = 50_000  # assumed p90 extra time outside the band


def minimum_recovery_lots(inventory: int) -> tuple[int, int]:
    """(side_sign, qty) of the fewest lots that return to +/-SAFE_POS; +1 means BUY."""
    if inventory > SAFE_POS:
        return -1, inventory - SAFE_POS
    if inventory < -SAFE_POS:
        return 1, -SAFE_POS - inventory
    return 0, 0


def hard_limit_allows(inventory: int, same_side_resting: int, qty: int, sign: int) -> bool:
    """README acceptance rule evaluated on our worst-case state."""
    return abs(inventory + sign * (same_side_resting + qty)) <= HARD_ACCEPTANCE_POS


def breach_gate(incremental_pnl: float, p90_us: float, reserve: float) -> bool:
    """Admit a breach only if A - 10,000 * tau_p90 - U > 0."""
    return incremental_pnl - PENALTY_PER_US * p90_us - reserve > 0.0


class ZubryFlowV2Strategy(BaseStrategy):
    def __init__(self) -> None:
        super().__init__()
        if MAX_INV > SAFE_POS:
            raise ValueError("MAX_INV must not exceed the penalty-free band")
        self.inventory = 0  # actual filled inventory
        self._pending: dict[str, tuple[Side, int]] = {}  # id -> (side, remaining qty)
        self._entry_us = 0
        self._last_try_us = -RETRY_US

    # ---------------- ledger ----------------
    def _flight(self) -> tuple[int, int]:
        buy = sum(q for s, q in self._pending.values() if s == Side.BUY)
        sell = sum(q for s, q in self._pending.values() if s == Side.SELL)
        return buy, sell

    def _budgets(self) -> tuple[int, int]:
        """Extra BUY / SELL lots that cannot push the worst case beyond MAX_INV."""
        buy, sell = self._flight()
        high = self.inventory + buy
        low = self.inventory - sell
        return max(0, MAX_INV - high), max(0, MAX_INV + low)

    def _send_ioc(self, side: Side, price: int, qty: int) -> None:
        sign = 1 if side == Side.BUY else -1
        buy, sell = self._flight()
        same_side = buy if sign == 1 else sell
        if qty <= 0 or price <= 0 or not hard_limit_allows(self.inventory, same_side, qty, sign):
            return
        order_id = self.send_order(
            OrderRequest(side=side, price=price, quantity=qty, order_type=OrderType.IOC)
        )
        self._pending[order_id] = (side, qty)

    # ---------------- market data ----------------
    def on_order_book_change(self, snapshot: OrderBookSnapshot, trades: list[Trade]) -> None:
        if not snapshot.bids or not snapshot.asks:
            return
        now = self.now_us()
        best_bid = snapshot.bids[0].price
        best_ask = snapshot.asks[0].price

        # RECOVER: actual inventory is outside the band, so the penalty clock is running.
        # Reduce only to +/-100 (not to zero) and only through filled lots.
        if abs(self.inventory) > SAFE_POS:
            if now - self._last_try_us >= RETRY_US:
                sign, need = minimum_recovery_lots(self.inventory)
                inflight_buy, inflight_sell = self._flight()
                already = inflight_buy if sign == 1 else inflight_sell
                need -= already  # do not stack a second recovery on one still in flight
                if need > 0:
                    self._last_try_us = now
                    if sign == 1:
                        self._send_ioc(Side.BUY, best_ask + EXIT_SLACK, need)
                    else:
                        self._send_ioc(Side.SELL, max(1, best_bid - EXIT_SLACK), need)
            return

        # Signal: net external taker volume (book_side 'ask' means the taker bought).
        flow = 0
        for t in trades:
            if t.taker_owner == "market":
                flow += t.quantity if t.book_side == "ask" else -t.quantity

        if flow != 0:
            self._entry_us = now
            budget_buy, budget_sell = self._budgets()
            if flow > 0:
                qty = min(LOT, budget_buy)
                if qty > 0:
                    self._send_ioc(Side.BUY, best_ask + ENTRY_SLACK, qty)
            else:
                qty = min(LOT, budget_sell)
                if qty > 0:
                    self._send_ioc(Side.SELL, max(1, best_bid - ENTRY_SLACK), qty)
            return

        # Timed exit: one clip at a time, throttled, never while an IOC is in flight.
        if (
            self.inventory != 0
            and not self._pending
            and now - self._entry_us >= HOLD_US
            and now - self._last_try_us >= RETRY_US
        ):
            self._last_try_us = now
            qty = min(abs(self.inventory), LOT)
            if self.inventory > 0:
                self._send_ioc(Side.SELL, max(1, best_bid - EXIT_SLACK), qty)
            else:
                self._send_ioc(Side.BUY, best_ask + EXIT_SLACK, qty)

    # ---------------- private feed ----------------
    def on_private_order_update(self, event: PrivateOrderEvent) -> None:
        entry = self._pending.get(event.order_id)
        if entry is None:
            return
        side, remaining = entry
        if event.status in (OrderStatus.PARTIALLY_FILLED, OrderStatus.FILLED):
            # filled_quantity is per match; inventory moves only on real fills.
            self.inventory += event.filled_quantity if side == Side.BUY else -event.filled_quantity
            remaining -= event.filled_quantity
            self._pending[event.order_id] = (side, max(0, remaining))
        if event.status in (OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.REJECTED):
            # Terminal states always release the exposure; otherwise the ledger leaks forever.
            del self._pending[event.order_id]
