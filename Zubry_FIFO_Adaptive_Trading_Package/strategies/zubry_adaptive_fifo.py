"""Experimental adaptive maker sizing for Qminers Algo Trade Arena.

Research candidate, not yet tested in the official Qminers simulator.
Paired independent FIFO replay found adaptive sizing generally LESS profitable
than fixed size 200 on Round 0 public data. Use as an ablation candidate only.
"""
from __future__ import annotations

import math
from simulator.models import (
    OrderBookSnapshot, OrderRequest, OrderStatus, OrderType,
    PrivateOrderEvent, Side, Trade,
)
from simulator.strategy import BaseStrategy

BASE_SIZE = 200
SAFE_LIMIT = 100
INVENTORY_PRICE_SKEW = 0.05
IMBALANCE_SIZE_COEFF = 0.65
MAX_DYNAMIC_SIZE = 250
MIN_DYNAMIC_SIZE = 2


class ZubryAdaptiveFIFO(BaseStrategy):
    def __init__(self) -> None:
        super().__init__()
        self.inventory = 0
        # ID -> side, price, remaining, accepted, cancel_requested
        self.orders: dict[str, tuple[Side, int, int, bool, bool]] = {}

    def on_private_order_update(self, event: PrivateOrderEvent) -> None:
        data = self.orders.get(event.order_id)
        if data is None:
            if event.filled_quantity:
                raise RuntimeError("Untracked fill: unsafe inventory state")
            return
        side, price, remaining, accepted, canceling = data
        if event.filled_quantity:
            self.inventory += event.filled_quantity * (1 if side == Side.BUY else -1)
        if event.status in (OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.REJECTED):
            del self.orders[event.order_id]
        elif event.status in (OrderStatus.ACCEPTED, OrderStatus.PARTIALLY_FILLED, OrderStatus.MODIFIED):
            self.orders[event.order_id] = (
                side, price, event.remaining_quantity, True, canceling
            )

    def on_order_book_change(self, snapshot: OrderBookSnapshot, trades: list[Trade]) -> None:
        bid = None
        ask = None
        bq = 0
        aq = 0
        # Market-owned best levels, like original V2. Bypass own quote for reference.
        for o in snapshot.bids:
            if o.owner != "market":
                continue
            if bid is None:
                bid = o.price
            if o.price != bid:
                break
            bq += o.quantity
        for o in snapshot.asks:
            if o.owner != "market":
                continue
            if ask is None:
                ask = o.price
            if o.price != ask:
                break
            aq += o.quantity
        if bid is None or ask is None or not (bq + aq):
            self.reconcile(None, None, 0, 0)
            return

        imbalance = (bq - aq) / (bq + aq)
        mid = (bid + ask) * 0.5
        center = mid - INVENTORY_PRICE_SKEW * self.inventory
        p_buy = max(1, min(bid, math.floor(center - 0.5)))
        p_sell = max(ask, math.ceil(center + 0.5), p_buy + 1)
        q_buy = max(MIN_DYNAMIC_SIZE, min(MAX_DYNAMIC_SIZE,
                    int(round(BASE_SIZE * max(0.25, min(1.60, 1.0 + IMBALANCE_SIZE_COEFF * imbalance))))))
        q_sell = max(MIN_DYNAMIC_SIZE, min(MAX_DYNAMIC_SIZE,
                     int(round(BASE_SIZE * max(0.25, min(1.60, 1.0 - IMBALANCE_SIZE_COEFF * imbalance))))))
        self.reconcile(p_buy, p_sell, q_buy, q_sell)

    def reconcile(self, p_buy: int | None, p_sell: int | None, q_buy: int, q_sell: int) -> None:
        targets = {Side.BUY: p_buy, Side.SELL: p_sell}
        sizes = {Side.BUY: q_buy, Side.SELL: q_sell}
        # Keep live and in-flight orders in the risk ledger until final status.
        for order_id, order in list(self.orders.items()):
            side, price, remaining, accepted, canceling = order
            if accepted and not canceling and targets[side] != price:
                self.cancel_order(order_id)
                self.orders[order_id] = (side, price, remaining, accepted, True)
        for side in (Side.BUY, Side.SELL):
            price = targets[side]
            if price is None or any(order[0] == side for order in self.orders.values()):
                continue
            # One order on each side, but calculate reserved same-side volume
            # to guard future versions that add extra orders.
            reserved = sum(o[2] for o in self.orders.values() if o[0] == side)
            headroom = (SAFE_LIMIT - self.inventory if side == Side.BUY
                        else SAFE_LIMIT + self.inventory)
            q = min(sizes[side], max(0, headroom - reserved))
            if q <= 0:
                continue
            order_id = self.send_order(
                OrderRequest(side=side, price=price, quantity=q,
                             order_type=OrderType.LIMIT)
            )
            self.orders[order_id] = (side, price, q, False, False)
