"""V2 candidate: depth-aware passive quoting with bounded outstanding inventory.

Locally evaluated public-tape hypothesis, not a promise of private performance.
No hardcoded price anchor, future schedule, filesystem or network access.
"""

from __future__ import annotations

import math

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

IMBALANCE_WEIGHT = 0.0
INVENTORY_SKEW = 0.05
QUOTE_SIZE = 2
MAX_INVENTORY = 20
HALF_WIDTH = 0.5


class ZubryV2Strategy(BaseStrategy):
    def __init__(self) -> None:
        super().__init__()
        self.inventory = 0
        # side, price, remaining quantity, accepted, cancel in flight
        self.orders: dict[str, tuple[Side, int, int, bool, bool]] = {}

    def on_private_order_update(self, event: PrivateOrderEvent) -> None:
        order = self.orders.get(event.order_id)
        if order is None:
            if event.filled_quantity:
                raise RuntimeError("Untracked private fill: inventory cannot be inferred safely.")
            return
        side, price, remaining, accepted, canceling = order
        if event.filled_quantity:
            self.inventory += event.filled_quantity * (1 if side == Side.BUY else -1)
        if event.status in (OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.REJECTED):
            del self.orders[event.order_id]
        elif event.status in (
            OrderStatus.ACCEPTED,
            OrderStatus.PARTIALLY_FILLED,
            OrderStatus.MODIFIED,
        ):
            self.orders[event.order_id] = (side, price, event.remaining_quantity, True, canceling)

    def on_order_book_change(self, snapshot: OrderBookSnapshot, trades: list[Trade]) -> None:
        bid = None
        bid_size = 0
        for order in snapshot.bids:
            if order.owner != "market":
                continue
            if bid is None:
                bid = order.price
            if order.price != bid:
                break
            bid_size += order.quantity
        ask = None
        ask_size = 0
        for order in snapshot.asks:
            if order.owner != "market":
                continue
            if ask is None:
                ask = order.price
            if order.price != ask:
                break
            ask_size += order.quantity
        if bid is None or ask is None or bid_size + ask_size == 0:
            self.reconcile(None, None)
            return
        mid = (bid + ask) / 2
        weighted = (ask * bid_size + bid * ask_size) / (bid_size + ask_size)
        center = mid + IMBALANCE_WEIGHT * (weighted - mid) - INVENTORY_SKEW * self.inventory
        buy_price = max(1, min(bid, math.floor(center - HALF_WIDTH)))
        sell_price = max(ask, math.ceil(center + HALF_WIDTH), buy_price + 1)
        self.reconcile(
            buy_price if self.inventory < MAX_INVENTORY else None,
            sell_price if self.inventory > -MAX_INVENTORY else None,
        )

    def reconcile(self, buy_price: int | None, sell_price: int | None) -> None:
        targets = {Side.BUY: buy_price, Side.SELL: sell_price}
        for order_id, order in list(self.orders.items()):
            side, price, remaining, accepted, canceling = order
            if accepted and not canceling and targets[side] != price:
                self.cancel_order(order_id)
                self.orders[order_id] = (side, price, remaining, accepted, True)
        for side in (Side.BUY, Side.SELL):
            price = targets[side]
            if price is None or any(order[0] == side for order in self.orders.values()):
                continue
            headroom = (
                MAX_INVENTORY - self.inventory
                if side == Side.BUY
                else MAX_INVENTORY + self.inventory
            )
            quantity = min(QUOTE_SIZE, headroom)
            if quantity <= 0:
                continue
            order_id = self.send_order(
                OrderRequest(side=side, price=price, quantity=quantity, order_type=OrderType.LIMIT)
            )
            self.orders[order_id] = (side, price, quantity, False, False)
