"""Experimental standalone R1 maker with default-disabled causal risk overlays."""

from __future__ import annotations

import math
from collections import deque

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
QI_GATE = 2.0
MAX_ORDERS_PER_SIDE = 8
TOPUP_REMAINDER = 200
IOC_MODE = 0

RISK_MODEL = 2
OVERLAY_MODE = 1
RISK_REVIEW_US = 50_000
RISK_MEAN: list[float] = [
    1.0377238379360605,
    2.4491017964071857,
    5.411861560221082,
    1.1757912745936698,
    0.5557149901851868,
    4.201221834614089,
    6.302580944321535,
    0.6563754038918685,
]
RISK_STD: list[float] = [
    0.42531305480676923,
    4.106262983049054,
    1.5478855546328731,
    0.5226887231841537,
    0.3081655376285553,
    1.4452315421238802,
    1.2039781033759818,
    0.23135914670645938,
]
RISK_BETA_VOL: list[float] = [-3.565533017825524, 0.9743829472798757]
RISK_BETA_FULL: list[float] = [
    -4.216930808185027,
    0.6397262984707137,
    0.2962471204951739,
    -0.6657312609708251,
    0.421820051941998,
    -0.6395750087024749,
    -0.2221196121110202,
    -0.08537663788415942,
    0.6187483651955563,
]

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
        if RISK_MODEL not in (0, 1, 2) or OVERLAY_MODE not in (0, 1, 2):
            raise ValueError("Unknown risk model/overlay")
        if bool(RISK_MODEL) != bool(OVERLAY_MODE):
            raise ValueError("Risk model and overlay must both be enabled or disabled")
        if RISK_MODEL and (
            len(RISK_MEAN) != 8
            or len(RISK_STD) != 8
            or len(RISK_BETA_FULL) != 9
            or len(RISK_BETA_VOL) != 2
            or any(value <= 0 for value in RISK_STD)
        ):
            raise ValueError("Risk model is missing frozen prior-fit parameters")
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
        self.next_risk_clock = 25_000
        self.risk_previous_mid: float | None = None
        self.risk_grid_mid: float | None = None
        self.risk_returns: deque[float | None] = deque(maxlen=60)
        self.risk_mids: deque[float | None] = deque(maxlen=4)
        self.risk_sigma: float | None = None
        self.risk_gap = True
        self.risk_bbo: tuple[int, int, int, int] | None = None
        self.risk_ofi = 0.0
        self.risk_ofi_t = 0
        self.risk_review_t = -RISK_REVIEW_US
        self.risk_score: float | None = None
        self.buy_cap = CAP
        self.sell_cap = CAP
        self.extra_width = 0

    def check_risk(self) -> None:
        buys = sum(info[2] for info in self.orders.values() if info[0] == Side.BUY)
        sells = sum(info[2] for info in self.orders.values() if info[0] == Side.SELL)
        if abs(self.q) > CAP or self.q + buys > CAP or self.q - sells < -CAP:
            raise RuntimeError("Hard inventory/reservation invariant violated")

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
        self.check_risk()

    def observe_risk(self, bid: int | None, ask: int | None, bq: int, aq: int, t: int) -> None:
        if not RISK_MODEL:
            return
        if t < self.risk_ofi_t:
            raise RuntimeError("Risk clock moved backwards")
        while self.next_risk_clock < t:
            old, current = self.risk_grid_mid, self.risk_previous_mid
            self.risk_returns.append(
                current - old
                if old is not None and current is not None and not self.risk_gap
                else None
            )
            self.risk_mids.append(current)
            self.risk_grid_mid = current
            valid = [value for value in self.risk_returns if value is not None]
            if len(valid) == 60:
                mean = sum(valid) / 60
                self.risk_sigma = math.sqrt(max(0.0, sum(r * r for r in valid) / 60 - mean**2))
            else:
                self.risk_sigma = None
            self.risk_gap = False
            self.next_risk_clock += 1_000_000
        self.risk_ofi *= math.exp(-(t - self.risk_ofi_t) / 200_000)
        self.risk_ofi_t = t
        if bid is None or ask is None or not bq or not aq:
            self.risk_previous_mid = None
            self.risk_bbo = None
            self.risk_gap = True
            self.risk_sigma = None
            self.risk_score = None
            return
        previous = self.risk_bbo
        if previous is not None:
            ob, oa, oqb, oqa = previous
            self.risk_ofi += (
                (bq if bid >= ob else 0)
                - (oqb if bid <= ob else 0)
                - (aq if ask <= oa else 0)
                + (oqa if ask >= oa else 0)
            )
        self.risk_bbo = (bid, ask, bq, aq)
        self.risk_previous_mid = (bid + ask) / 2

    def score_risk(
        self, bid: int, ask: int, bq: int, aq: int, qi: float, concentration: float, t: int
    ) -> float | None:
        sigma = self.risk_sigma
        if sigma is None or len(self.risk_mids) < 4:
            return None
        first, last = self.risk_mids[0], self.risk_mids[-1]
        if first is None or last is None:
            return None
        vol = (math.log1p(sigma) - RISK_MEAN[0]) / RISK_STD[0]
        if RISK_MODEL == 1:
            eta = RISK_BETA_VOL[0] + RISK_BETA_VOL[1] * vol
        elif RISK_MODEL == 2:
            features = [
                math.log1p(sigma),
                abs(last - first),
                math.log1p(min(bq, aq)),
                ask - bid,
                abs(qi),
                math.log1p(abs(self.ridge_flow[0] * math.exp(-(t - self.flow_t) / 200_000))),
                math.log1p(abs(self.risk_ofi)),
                concentration,
            ]
            eta = RISK_BETA_FULL[0] + sum(
                RISK_BETA_FULL[i + 1] * (value - RISK_MEAN[i]) / RISK_STD[i]
                for i, value in enumerate(features)
            )
        else:
            raise ValueError("Risk scoring requires an enabled model")
        if eta >= 0:
            return 1 / (1 + math.exp(-eta))
        exponential = math.exp(eta)
        return exponential / (1 + exponential)

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
            self.flow = self.flow * math.exp(-(t - self.flow_t) / 200_000) + flow
            self.flow_t = t
        bid = ask = None
        bq = aq = 0
        largest_bid = largest_ask = 0
        for order in snapshot.bids:
            if order.owner != "market":
                continue
            if bid is None:
                bid = order.price
            if order.price != bid:
                break
            bq += order.quantity
            largest_bid = max(largest_bid, order.quantity)
        for order in snapshot.asks:
            if order.owner != "market":
                continue
            if ask is None:
                ask = order.price
            if order.price != ask:
                break
            aq += order.quantity
            largest_ask = max(largest_ask, order.quantity)
        self.observe_risk(bid, ask, bq, aq, t)
        if t < START_US:
            return
        if bid is None or ask is None or not bq + aq:
            self.update(None, None, t)
            return
        qi = (bq - aq) / (bq + aq)
        if RISK_MODEL and (
            self.risk_sigma is None
            or self.risk_score is None
            or t - self.risk_review_t >= RISK_REVIEW_US
        ):
            self.risk_score = self.score_risk(
                bid, ask, bq, aq, qi, max(largest_bid / bq, largest_ask / aq), t
            )
            self.risk_review_t = t
            if OVERLAY_MODE == 1:
                self.buy_cap = self.sell_cap = (
                    35
                    if self.risk_score is None or self.risk_score >= 0.15
                    else 70
                    if self.risk_score >= 0.03
                    else CAP
                )
            elif OVERLAY_MODE == 2:
                self.extra_width = int(self.risk_score is None or self.risk_score >= 0.15)
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
        center = (bid + ask) / 2 + 2 * self.prediction - SKEW * self.q
        base_buy = max(1, min(bid, math.floor(center - WIDTH)))
        base_sell = max(ask, math.ceil(center + WIDTH), base_buy + 1)
        buy = max(1, base_buy - self.extra_width)
        sell = base_sell + self.extra_width
        self.update(
            buy if self.q < self.buy_cap and qi > -QI_GATE else None,
            sell if self.q > -self.sell_cap and qi < QI_GATE else None,
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
        if OVERLAY_MODE == 1:
            for side in (Side.BUY, Side.SELL):
                cap = self.buy_cap if side == Side.BUY else self.sell_cap
                desired = max(0, cap - self.q if side == Side.BUY else cap + self.q)
                intended = sum(
                    info[2] for info in self.orders.values() if info[0] == side and not info[4]
                )
                # This is cancel intent only; all quantities remain reserved below.
                for oid, info in sorted(
                    self.orders.items(), key=lambda item: item[1][5], reverse=True
                ):
                    if intended <= desired:
                        break
                    s, price, left, accepted, canceling, created = info
                    if s != side or not accepted or canceling or oid in self.ioc_ids:
                        continue
                    self.cancel_order(oid)
                    self.orders[oid] = (s, price, left, True, True, created)
                    intended -= left
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
            soft_cap = self.buy_cap if side == Side.BUY else self.sell_cap
            capacity = (
                min(CAP, soft_cap) - self.q - reserved
                if side == Side.BUY
                else min(CAP, soft_cap) + self.q - reserved
            )
            desired = max(0, QUOTE_SIZE - remaining)
            size = min(desired, capacity)
            if size <= 0 or (active and size < 10):
                continue
            oid = self.send_order(
                OrderRequest(side=side, price=target, quantity=size, order_type=OrderType.LIMIT)
            )
            self.orders[oid] = (side, target, size, False, False, t)
        self.check_risk()

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
        self.check_risk()
