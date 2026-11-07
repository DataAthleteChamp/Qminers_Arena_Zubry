"""Standalone experimental maker: actual engine, no source/data file access."""

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

START_US = 0
QUOTE_SIZE = 200
CAP = 100
SKEW = 0.005
WIDTH = 0.0
DEPTH_WEIGHT = 1.0
FLOW_WEIGHT = 0.0
QI_GATE = 2.0
HYSTERESIS = 0
MIN_REST_US = 0
MAX_ORDERS_PER_SIDE = 3
TOPUP_REMAINDER = 200


class Maker(BaseStrategy):
    def __init__(self) -> None:
        super().__init__()
        self.q = 0
        # side, price, remaining, accepted, canceling, submitted timestamp
        self.orders: dict[str, tuple[Side, int, int, bool, bool, int]] = {}
        self.flow = 0.0
        self.flow_t = 0

    def on_private_order_update(self, event: PrivateOrderEvent) -> None:
        info = self.orders.get(event.order_id)
        if info is None:
            if event.filled_quantity:
                raise RuntimeError("Untracked fill")
            return
        side, price, left, accepted, canceling, created = info
        if event.filled_quantity:
            self.q += event.filled_quantity * (1 if side == Side.BUY else -1)
        if event.status in (OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.REJECTED):
            del self.orders[event.order_id]
        elif event.status in (
            OrderStatus.ACCEPTED,
            OrderStatus.PARTIALLY_FILLED,
            OrderStatus.MODIFIED,
        ):
            self.orders[event.order_id] = (
                side,
                price,
                event.remaining_quantity,
                True,
                canceling,
                created,
            )

    def on_order_book_change(self, snapshot: OrderBookSnapshot, trades: list[Trade]) -> None:
        t = snapshot.timestamp_us
        flow = sum(
            trade.quantity * (1 if trade.book_side == "ask" else -1)
            for trade in trades
            if trade.taker_owner == "market" and trade.maker_owner == "market"
        )
        if flow:
            self.flow = self.flow * math.exp(-(t - self.flow_t) / 200000.0) + flow
            self.flow_t = t
        bid = ask = None
        bq = aq = 0
        for order in snapshot.bids:
            if order.owner != "market":
                continue
            if bid is None:
                bid = order.price
            if order.price != bid:
                break
            bq += order.quantity
        for order in snapshot.asks:
            if order.owner != "market":
                continue
            if ask is None:
                ask = order.price
            if order.price != ask:
                break
            aq += order.quantity
        if t < START_US:
            return
        if bid is None or ask is None or not bq + aq:
            self.update(None, None, t)
            return
        qi = (bq - aq) / (bq + aq)
        impulse = max(-2.0, min(2.0, self.flow * math.exp(-(t - self.flow_t) / 200000.0) / 264.0))
        center = (
            (bid + ask) / 2
            + DEPTH_WEIGHT * qi * (ask - bid) / 2
            + FLOW_WEIGHT * impulse
            - SKEW * self.q
        )
        buy = max(1, min(bid, math.floor(center - WIDTH)))
        sell = max(ask, math.ceil(center + WIDTH), buy + 1)
        self.update(
            buy if self.q < CAP and qi > -QI_GATE else None,
            sell if self.q > -CAP and qi < QI_GATE else None,
            t,
        )

    def update(self, buy: int | None, sell: int | None, t: int) -> None:
        targets = {Side.BUY: buy, Side.SELL: sell}
        for oid, info in list(self.orders.items()):
            side, price, left, accepted, canceling, created = info
            target = targets[side]
            if accepted and not canceling and (target is None or target != price):
                self.cancel_order(oid)
                self.orders[oid] = (side, price, left, True, True, created)
        for side in (Side.BUY, Side.SELL):
            target = targets[side]
            if target is None:
                continue
            active = [info for info in self.orders.values() if info[0] == side]
            if len(active) >= MAX_ORDERS_PER_SIDE or any(not info[3] or info[4] for info in active):
                continue
            remaining = sum(info[2] for info in active)
            if active and (
                remaining > TOPUP_REMAINDER or any(info[1] != target for info in active)
            ):
                continue
            capacity = CAP - self.q - remaining if side == Side.BUY else CAP + self.q - remaining
            desired = max(0, QUOTE_SIZE - remaining)
            size = min(desired, capacity)
            if size <= 0 or (active and size < 10):
                continue
            oid = self.send_order(
                OrderRequest(side=side, price=target, quantity=size, order_type=OrderType.LIMIT)
            )
            self.orders[oid] = (side, target, size, False, False, t)
