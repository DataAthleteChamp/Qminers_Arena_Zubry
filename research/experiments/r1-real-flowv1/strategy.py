"""Flow-following taker with timed exit, tuned to the round-0 tutorial tape (data/round0/sample.csv).

Hypothesis: on this tape an external aggressive order (Lifespan F) is followed by a
same-direction mid move (+3 ticks in 1 s, ~+8 in 5 s). We buy/sell with IOC at the
touch right after the flow, hold HOLD_US, then flatten with IOC at the opposite touch.

This is a tape-specific mechanism. It FAILED the frozen test on sample_v2.csv
(see research/round0/V2_DECISION.md), so treat it as a tutorial-tape baseline, not alpha.
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

LOT = 5  # lots per entry / per exit clip
POSITION_CAP = 40  # internal cap incl. in-flight orders (penalty-free limit is 100)
HOLD_US = 5_000_000  # holding time before the timed exit
RETRY_US = 50_000  # min gap between exit attempts (avoids spamming a stale touch)


class ZubryFlowStrategy(BaseStrategy):
    def __init__(self) -> None:
        super().__init__()
        self.inventory = 0  # from fills only
        self._pending: dict[str, tuple[Side, int]] = {}  # in-flight IOC id -> (side, remaining)
        self._entry_us = 0  # time of the most recent entry signal
        self._last_exit_try_us = -RETRY_US

    def _pending_signed(self) -> int:
        return sum(q if s == Side.BUY else -q for s, q in self._pending.values())

    def _send_ioc(self, side: Side, price: int, qty: int) -> None:
        order_id = self.send_order(
            OrderRequest(side=side, price=price, quantity=qty, order_type=OrderType.IOC)
        )
        self._pending[order_id] = (side, qty)

    def on_order_book_change(self, snapshot: OrderBookSnapshot, trades: list[Trade]) -> None:
        if not snapshot.bids or not snapshot.asks:
            return
        now = self.now_us()
        best_bid = snapshot.bids[0].price
        best_ask = snapshot.asks[0].price

        # 1. Signal: net signed volume of EXTERNAL takers (book_side 'ask' = taker bought).
        flow = 0
        for t in trades:
            if t.taker_owner == "market":
                flow += t.quantity if t.book_side == "ask" else -t.quantity

        # 2. Entry in the direction of the flow, respecting worst-case position incl. in-flight.
        if flow != 0:
            self._entry_us = now
            exposure = self.inventory + self._pending_signed()
            if flow > 0 and exposure + LOT <= POSITION_CAP:
                self._send_ioc(Side.BUY, best_ask, LOT)
            elif flow < 0 and exposure - LOT >= -POSITION_CAP:
                self._send_ioc(Side.SELL, best_bid, LOT)
            return

        # 3. Timed exit: flatten (one clip at a time) once the hold has elapsed.
        if (
            self.inventory != 0
            and not self._pending
            and now - self._entry_us >= HOLD_US
            and now - self._last_exit_try_us >= RETRY_US
        ):
            self._last_exit_try_us = now
            qty = min(abs(self.inventory), LOT)
            if self.inventory > 0:
                self._send_ioc(Side.SELL, best_bid, qty)
            else:
                self._send_ioc(Side.BUY, best_ask, qty)

    def on_private_order_update(self, event: PrivateOrderEvent) -> None:
        entry = self._pending.get(event.order_id)
        if entry is None:
            return
        side, _ = entry
        if event.status in (OrderStatus.PARTIALLY_FILLED, OrderStatus.FILLED):
            # filled_quantity is per match, so adding it is exact (no double count).
            self.inventory += event.filled_quantity if side == Side.BUY else -event.filled_quantity
        if event.status in (OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.REJECTED):
            # Terminal states always free the slot; otherwise the bot would hang forever.
            del self._pending[event.order_id]
