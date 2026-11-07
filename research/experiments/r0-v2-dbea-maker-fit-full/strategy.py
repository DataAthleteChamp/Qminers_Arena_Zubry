"""Causal, inventory-limited market maker; experimental parameters are frozen per run."""

from __future__ import annotations

from math import ceil, floor

from simulator.models import (
    BookOrderView,
    OrderBookSnapshot,
    OrderRequest,
    OrderStatus,
    OrderType,
    PrivateOrderEvent,
    Side,
    Trade,
)
from simulator.strategy import BaseStrategy

IMBALANCE_WEIGHT = 1.0
ACTIVATE_AT_US = 0
QUOTE_SIZE = 5
POSITION_CAP = 80
INVENTORY_SKEW = 0.025
HALF_EDGE = 0.5
MIN_QUOTE_AGE_US = 20_000


class _Quote:
    def __init__(self, order_id: str, side: Side, price: int, quantity: int, now: int) -> None:
        self.order_id = order_id
        self.side = side
        self.price = price
        self.remaining = quantity
        self.born_us = now
        self.accepted = False
        self.cancel_pending = False


def _market_touch(orders: list[BookOrderView]) -> tuple[int, int] | None:
    price: int | None = None
    quantity = 0
    for order in orders:
        if order.owner != "market":
            continue
        if order.price <= 0 or order.quantity <= 0:
            raise ValueError("Invalid market order in public snapshot")
        if price is None:
            price = order.price
        elif order.price != price:
            break
        quantity += order.quantity
    return None if price is None else (price, quantity)


class R0V2MakerStrategy(BaseStrategy):
    def __init__(self) -> None:
        super().__init__()
        self.inventory = 0
        self._orders: dict[str, _Quote] = {}
        self._slots: dict[Side, _Quote] = {}

    def _cancel(self, quote: _Quote) -> None:
        if not quote.cancel_pending:
            self.cancel_order(quote.order_id)
            quote.cancel_pending = True

    def _manage(self, side: Side, price: int | None, now: int) -> None:
        quote = self._slots.get(side)
        sign = 1 if side == Side.BUY else -1
        capacity = POSITION_CAP - sign * self.inventory
        if quote is not None:
            if quote.cancel_pending:
                return
            if price is None or capacity < quote.remaining:
                self._cancel(quote)
            elif price != quote.price and (
                now - quote.born_us >= MIN_QUOTE_AGE_US or abs(price - quote.price) >= 2
            ):
                self._cancel(quote)
            return
        quantity = min(QUOTE_SIZE, capacity)
        if price is None or quantity <= 0:
            return
        order_id = self.send_order(
            OrderRequest(
                side=side,
                price=price,
                quantity=quantity,
                order_type=OrderType.LIMIT,
            )
        )
        quote = _Quote(order_id, side, price, quantity, now)
        self._orders[order_id] = quote
        self._slots[side] = quote

    def on_order_book_change(self, snapshot: OrderBookSnapshot, trades: list[Trade]) -> None:
        now = snapshot.timestamp_us
        if now < ACTIVATE_AT_US:
            return
        bid = _market_touch(snapshot.bids)
        ask = _market_touch(snapshot.asks)
        if bid is None or ask is None:
            self._manage(Side.BUY, None, now)
            self._manage(Side.SELL, None, now)
            return
        bid_price, bid_quantity = bid
        ask_price, ask_quantity = ask
        spread = ask_price - bid_price
        if spread <= 0:
            raise ValueError("Crossed market-only book")
        imbalance = (bid_quantity - ask_quantity) / (bid_quantity + ask_quantity)
        centre = (
            (bid_price + ask_price) / 2
            + IMBALANCE_WEIGHT * spread * imbalance / 2
            - INVENTORY_SKEW * self.inventory
        )
        buy_price = max(1, min(ask_price - 1, floor(centre - HALF_EDGE)))
        sell_price = max(bid_price + 1, ceil(centre + HALF_EDGE))
        self._manage(Side.BUY, buy_price, now)
        self._manage(Side.SELL, sell_price, now)

    def _remove(self, quote: _Quote) -> None:
        del self._orders[quote.order_id]
        del self._slots[quote.side]

    def on_private_order_update(self, event: PrivateOrderEvent) -> None:
        quote = self._orders.get(event.order_id)
        if quote is None:
            # A completed fill can be followed by rejection of its delayed cancel.
            if event.status == OrderStatus.REJECTED:
                return
            raise RuntimeError(f"Unexpected update for unknown order: {event.order_id}")
        if event.status == OrderStatus.ACCEPTED:
            quote.accepted = True
            quote.born_us = event.timestamp_us
            quote.remaining = event.remaining_quantity
        elif event.status in (OrderStatus.PARTIALLY_FILLED, OrderStatus.FILLED):
            sign = 1 if quote.side == Side.BUY else -1
            self.inventory += sign * event.filled_quantity
            quote.remaining = event.remaining_quantity
            if abs(self.inventory) > POSITION_CAP:
                raise RuntimeError("Inventory reservation invariant failed")
            if event.status == OrderStatus.FILLED:
                self._remove(quote)
        elif event.status == OrderStatus.CANCELED:
            self._remove(quote)
        elif event.status == OrderStatus.REJECTED:
            if quote.accepted and quote.cancel_pending:
                quote.cancel_pending = False
            else:
                self._remove(quote)
        else:
            raise RuntimeError(f"Unexpected order status: {event.status}")
