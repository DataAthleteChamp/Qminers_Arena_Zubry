"""Passive maker with reservation-price skew and multi-level OBI side withdrawal.

Pivot after the taker post-mortem on round1 (flow takers lost ~0.39 tick/lot): earn the
spread as a maker instead of paying it. One LIMIT quote per side near the touch.

* Reservation centre: mid - GAMMA * inventory (Avellaneda-Stoikov style skew, ticks/lot).
* OBI_3 over the first three EXTERNAL price levels. OBI > +OBI_LIMIT withdraws the ask,
  OBI < -OBI_LIMIT withdraws the bid (adverse-selection guard). OBI_LIMIT > 1 disables it.
* Inventory cap MAX_INV counts the resting quote at full size (worst case), well inside
  the penalty-free +/-100 band.
* Hysteresis: a quote is only replaced when the target price changed AND it has rested
  MIN_QUOTE_AGE_US (or the move is >= 2 ticks), because cancel+send loses FIFO priority.
* Ledger/race handling is taken from r0_v2_maker.py (a delayed cancel may be REJECTED
  after the order already filled).
"""

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

QUOTE_SIZE = 4
MAX_INV = 40
GAMMA = 0.045  # ticks of reservation shift per lot of inventory
HALF_EDGE = 0.5
OBI_LEVELS = 3
OBI_LIMIT = 0.65  # set above 1.0 to disable the guard
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


def _levels(orders: list[BookOrderView], depth: int) -> list[tuple[int, int]]:
    """Aggregate EXTERNAL orders into the first `depth` price levels, best first."""
    out: list[tuple[int, int]] = []
    for order in orders:
        if order.owner != "market":
            continue
        if order.price <= 0 or order.quantity <= 0:
            raise ValueError("Invalid market order in public snapshot")
        if out and out[-1][0] == order.price:
            out[-1] = (order.price, out[-1][1] + order.quantity)
        elif len(out) < depth:
            out.append((order.price, order.quantity))
        else:
            break
    return out


class MakerObiStrategy(BaseStrategy):
    def __init__(self) -> None:
        super().__init__()
        if MAX_INV > 100:
            raise ValueError("MAX_INV must stay inside the penalty-free band")
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
        capacity = MAX_INV - sign * self.inventory
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
            OrderRequest(side=side, price=price, quantity=quantity, order_type=OrderType.LIMIT)
        )
        quote = _Quote(order_id, side, price, quantity, now)
        self._orders[order_id] = quote
        self._slots[side] = quote

    def on_order_book_change(self, snapshot: OrderBookSnapshot, trades: list[Trade]) -> None:
        now = snapshot.timestamp_us
        bids = _levels(snapshot.bids, OBI_LEVELS)
        asks = _levels(snapshot.asks, OBI_LEVELS)
        if not bids or not asks:
            self._manage(Side.BUY, None, now)
            self._manage(Side.SELL, None, now)
            return
        bid_price, ask_price = bids[0][0], asks[0][0]
        if ask_price - bid_price <= 0:
            raise ValueError("Crossed market-only book")

        bid_vol = sum(q for _, q in bids)
        ask_vol = sum(q for _, q in asks)
        obi = (bid_vol - ask_vol) / (bid_vol + ask_vol)

        centre = (bid_price + ask_price) / 2 - GAMMA * self.inventory
        buy_price: int | None = max(1, min(ask_price - 1, floor(centre - HALF_EDGE)))
        sell_price: int | None = max(bid_price + 1, ceil(centre + HALF_EDGE))
        if obi > OBI_LIMIT:
            sell_price = None  # buying pressure: do not sell ahead of the move up
        elif obi < -OBI_LIMIT:
            buy_price = None  # selling pressure: do not catch the falling knife
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
            self.inventory += sign * event.filled_quantity  # per-match quantity
            quote.remaining = event.remaining_quantity
            if abs(self.inventory) > MAX_INV:
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
