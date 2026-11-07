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
SKEW = 0.001
WIDTH = 0.0
DEPTH_WEIGHT = 0.0
FLOW_WEIGHT = 0.0
QI_GATE = 2.0
HYSTERESIS = 0
MIN_REST_US = 0
MAX_ORDERS_PER_SIDE = 8
TOPUP_REMAINDER = 200


IOC_MODE = 0
RIDGE_BETA = [
    0.00793104957762508,
    0.24483025823132065,
    -0.07252210584306798,
    0.1502022846980176,
    0.09800651918880035,
    -0.037122189565358524,
]
RIDGE_MEAN = [
    0.0004431746191048556,
    0.00727932466357482,
    1.6712132713922274,
    8.254508058000276,
    24.597632549434433,
]
RIDGE_STD = [
    0.6336693999092285,
    0.3923486299038159,
    264.2145921407855,
    604.2664502859786,
    1045.861700983837,
]


class Maker(BaseStrategy):
    def __init__(self) -> None:
        super().__init__()
        self.q = 0
        # side, price, remaining, accepted, canceling, submitted timestamp
        self.orders: dict[str, tuple[Side, int, int, bool, bool, int]] = {}
        self.flow = 0.0
        self.ridge_flow = [0.0, 0.0, 0.0]
        self.prediction = 0.0
        self.ioc_ids: set[str] = set()
        self.ioc_episode = False
        self.ioc_requests = 0
        self.ioc_filled = 0
        self.flow_t = 0

    def on_private_order_update(self, event: PrivateOrderEvent) -> None:
        if event.order_id in self.ioc_ids:
            self.ioc_filled += event.filled_quantity
            if event.status in (OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.REJECTED):
                self.ioc_ids.discard(event.order_id)
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
            elapsed = (t - self.flow_t) / 1e6
            for i, tau in enumerate((0.2, 1.0, 3.0)):
                self.ridge_flow[i] = self.ridge_flow[i] * math.exp(-elapsed / tau) + flow
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
        bd = sum(item.quantity for item in snapshot.bids if item.owner == "market")
        ad = sum(item.quantity for item in snapshot.asks if item.owner == "market")
        features = [qi, (bd - ad) / (bd + ad)] + [
            self.ridge_flow[i] * math.exp(-(t - self.flow_t) / (tau * 1e6))
            for i, tau in enumerate((0.2, 1.0, 3.0))
        ]
        self.prediction = RIDGE_BETA[0] + sum(
            RIDGE_BETA[i + 1] * (value - RIDGE_MEAN[i]) / RIDGE_STD[i]
            for i, value in enumerate(features)
        )
        self.try_ioc(bid, ask, self.prediction, t)
        center = (bid + ask) / 2 + max(-2.0, min(2.0, 2.0 * self.prediction)) - SKEW * self.q
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
            if oid in self.ioc_ids:
                continue
            side, price, left, accepted, canceling, created = info
            target = targets[side]
            if accepted and not canceling and (target is None or target != price):
                self.cancel_order(oid)
                self.orders[oid] = (side, price, left, True, True, created)
        for side in (Side.BUY, Side.SELL):
            target = targets[side]
            if target is None:
                continue
            active = [
                info
                for oid, info in self.orders.items()
                if info[0] == side and oid not in self.ioc_ids
            ]
            if len(active) >= MAX_ORDERS_PER_SIDE or any(not info[3] or info[4] for info in active):
                continue
            remaining = sum(info[2] for info in active)
            if active and (
                remaining > TOPUP_REMAINDER or any(info[1] != target for info in active)
            ):
                continue
            reserved = sum(info[2] for info in self.orders.values() if info[0] == side)
            capacity = CAP - self.q - reserved if side == Side.BUY else CAP + self.q - reserved
            desired = max(0, QUOTE_SIZE - remaining)
            size = min(desired, capacity)
            if size <= 0 or (active and size < 10):
                continue
            oid = self.send_order(
                OrderRequest(side=side, price=target, quantity=size, order_type=OrderType.LIMIT)
            )
            self.orders[oid] = (side, target, size, False, False, t)

    def try_ioc(self, bid: int, ask: int, prediction: float, t: int) -> None:
        if IOC_MODE == 0:
            return
        buys = sum(info[2] for info in self.orders.values() if info[0] == Side.BUY)
        sells = sum(info[2] for info in self.orders.values() if info[0] == Side.SELL)
        side: Side | None = None
        if IOC_MODE in (1, 2):
            long_ok = self.q > 0 and self.q + buys >= CAP and self.q - sells >= 1
            short_ok = self.q < 0 and self.q - sells <= -CAP and -self.q - buys >= 1
            if long_ok and (IOC_MODE == 2 or prediction < 0):
                side = Side.SELL
            elif short_ok and (IOC_MODE == 2 or prediction > 0):
                side = Side.BUY
        elif IOC_MODE == 3:
            if prediction > (ask - bid) + 0.25:
                side = Side.BUY
            elif prediction < -(ask - bid) - 0.25:
                side = Side.SELL
        else:
            raise RuntimeError("Invalid IOC mode")
        capacity = (
            CAP - self.q - buys
            if side == Side.BUY
            else CAP + self.q - sells
            if side == Side.SELL
            else 0
        )
        if side is None or capacity < 1:
            self.ioc_episode = False
            return
        if self.ioc_episode or self.ioc_ids:
            return
        self.ioc_episode = True
        price = ask if side == Side.BUY else bid
        oid = self.send_order(
            OrderRequest(side=side, price=price, quantity=1, order_type=OrderType.IOC)
        )
        self.orders[oid] = (side, price, 1, False, False, t)
        self.ioc_ids.add(oid)
        self.ioc_requests += 1
