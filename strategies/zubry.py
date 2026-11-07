"""Team baseline: official one-lot tutorial logic with the documented IOC reset fix.

This is a correctness baseline on synthetic playground data, not private-round alpha.
IGNORE_USER_TAKERS is a parked, unvalidated feature; keep it disabled until tested.
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

IGNORE_USER_TAKERS = False


class ZubryStrategy(BaseStrategy):
    def __init__(self) -> None:
        super().__init__()
        self._order_in_flight: bool = False
        self._current_order_side: None | Side = None

    def on_order_book_change(self, snapshot: OrderBookSnapshot, trades: list[Trade]) -> None:
        if self._order_in_flight:
            return
        side_sign = {"ask": 1, "bid": -1}
        net_flow = sum(
            trade.quantity * side_sign[trade.book_side]
            for trade in trades
            if not IGNORE_USER_TAKERS or trade.taker_owner == "market"
        )
        if net_flow == 0:
            return
        if net_flow > 0:
            if not snapshot.asks or self._current_order_side == Side.BUY:
                return
            self._current_order_side = Side.BUY
            price = snapshot.asks[0].price
        else:
            if not snapshot.bids or self._current_order_side == Side.SELL:
                return
            self._current_order_side = Side.SELL
            price = snapshot.bids[0].price
        self.send_order(
            OrderRequest(
                side=self._current_order_side,
                price=price,
                quantity=1,
                order_type=OrderType.IOC,
            )
        )
        self._order_in_flight = True

    def on_private_order_update(self, event: PrivateOrderEvent) -> None:
        if event.status == OrderStatus.FILLED:
            self._order_in_flight = False
        elif event.status in (OrderStatus.REJECTED, OrderStatus.CANCELED):
            self._order_in_flight = False
            self._current_order_side = (
                Side.BUY if self._current_order_side == Side.SELL else Side.SELL
            )
