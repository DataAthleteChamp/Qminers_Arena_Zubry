"""HPO config cfg_034.
"""

from collections import deque
from math import ceil, exp, floor, log1p
from typing import TypedDict

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
POSITION_LIMIT = 100
QUOTE_SIZE = 40  
FIFO_TOPUPS = True
GAP_GUARD = True
SHOCK_SPREAD = 3  # spread >= this -> SHOCK
MIN_L1 = 100  # min(bid, ask) L1 lots required for NORMAL
CAUTION_DIV = 1  # quote-size divisor in CAUTION / RECOVERY
GAP_QTY = 60  # best level at or below this many lots ...
GAP_TICKS = 2  # ... with the next level this many ticks behind -> fragile side
FRAGILE_SIZE = 12  # quote size on a fragile side
TOPUP_MIN = 4  # smallest top-up order
MAX_PER_LEVEL = 3  # resting orders allowed per grid level
SLOT_MULT = 3  # max resting orders per side = SLOT_MULT * GRID_LEVELS
TARGET_SCALE = 1.0  # trend target = TARGET_SCALE * POSITION_LIMIT * direction
GRID_LEVELS = 3
INVENTORY_SKEW = 0.0055  
EMA_SECONDS = (4, 45, 180)  
ANCHOR_US = 50_000
RECOVERY_US = 500000  
PREDICTION_INTERCEPT = -0.0712784484850363
PREDICTION_WEIGHTS = (
    -0.13357816725198274,
    0.010391788055318084,
    0.09995071015978531,
    -0.08450425126087342,
    0.04439024149295189,
    0.03317727910152446,
    -0.03300156560078225,
    0.2555266527668515,
    0.10418063499285538,
    0.017583044308491825,
    -0.024572154921053847,
)


class WorkingOrder(TypedDict):
    side: Side
    price: int
    remaining: int
    state: str


class TrendInventoryGridMaker(BaseStrategy):
    def __init__(self) -> None:
        super().__init__()
        self.inventory = 0
        self.orders: dict[str, WorkingOrder] = {}
        self.previous_ids: set[str] = set()
        self.previous_bid: int | None = None
        self.previous_ask: int | None = None
        self.recent: deque[tuple[int, int, int, int]] = deque()
        self.flow_totals = [0, 0, 0]
        self.history: deque[tuple[int, float]] = deque()
        self.last_anchor = -ANCHOR_US
        self.prediction = 0.0
        self.emas: list[float] | None = None
        self.ema_time: int | None = None
        self.target = 0
        self.state = "NORMAL"
        self.stable_since: int | None = None
        self.max_exposure = 0
        self.max_inventory = 0
        self.fragile_sides: set[Side] = set()

    def check_risk(self) -> None:
        buys = sum(o["remaining"] for o in self.orders.values() if o["side"] == Side.BUY)
        sells = sum(o["remaining"] for o in self.orders.values() if o["side"] == Side.SELL)
        if (
            abs(self.inventory) > POSITION_LIMIT
            or self.inventory + buys > POSITION_LIMIT
            or self.inventory - sells < -POSITION_LIMIT
        ):
            raise RuntimeError("Inventory or same-side reservation exceeds100")

    def cancel(self, order_id: str, order: WorkingOrder) -> None:
        if order["state"] == "live":
            order["state"] = "cancel_pending"
            self.cancel_order(order_id)

    def submit(self, side: Side, price: int, quantity: int) -> None:
        buys = sum(o["remaining"] for o in self.orders.values() if o["side"] == Side.BUY)
        sells = sum(o["remaining"] for o in self.orders.values() if o["side"] == Side.SELL)
        if side == Side.BUY:
            capacity = POSITION_LIMIT - self.inventory - buys
        else:
            capacity = POSITION_LIMIT + self.inventory - sells
        quantity = min(quantity, capacity)
        if quantity <= 0:
            return
        order_id = self.send_order(
            OrderRequest(
                side=side, price=max(1, price), quantity=quantity, order_type=OrderType.LIMIT
            )
        )
        self.orders[order_id] = {
            "side": side,
            "price": price,
            "remaining": quantity,
            "state": "submit_pending",
        }
        buys = sum(o["remaining"] for o in self.orders.values() if o["side"] == Side.BUY)
        sells = sum(o["remaining"] for o in self.orders.values() if o["side"] == Side.SELL)
        self.max_exposure = max(
            self.max_exposure, abs(self.inventory + buys), abs(self.inventory - sells)
        )
        self.check_risk()

    def on_order_book_change(self, snapshot: OrderBookSnapshot, trades: list[Trade]) -> None:
        now = self.now_us()
        bids = [order for order in snapshot.bids if order.owner == "market"]
        asks = [order for order in snapshot.asks if order.owner == "market"]
        if not bids or not asks:
            for order_id, order in self.orders.items():
                self.cancel(order_id, order)
            self.previous_ids = {order.order_id for order in bids + asks}
            self.previous_bid = bids[0].price if bids else None
            self.previous_ask = asks[0].price if asks else None
            self.stable_since = None
            self.check_risk()
            return
        bid, ask = bids[0].price, asks[0].price
        bid_quantity = sum(order.quantity for order in bids if order.price == bid)
        ask_quantity = sum(order.quantity for order in asks if order.price == ask)
        bid_added = sum(
            order.quantity
            for order in bids
            if order.price == bid
            and bid == self.previous_bid
            and order.order_id not in self.previous_ids
        )
        ask_added = sum(
            order.quantity
            for order in asks
            if order.price == ask
            and ask == self.previous_ask
            and order.order_id not in self.previous_ids
        )
        flow = sum(
            trade.quantity * (1 if trade.book_side == "ask" else -1)
            for trade in trades
            if trade.taker_owner == "market" and trade.maker_owner == "market"
        )
        self.previous_ids = {order.order_id for order in bids + asks}
        self.previous_bid, self.previous_ask = bid, ask
        if bid_added or ask_added or flow:
            self.recent.append((now, bid_added, ask_added, flow))
            self.flow_totals[0] += bid_added
            self.flow_totals[1] += ask_added
            self.flow_totals[2] += flow
        while self.recent and self.recent[0][0] <= now - ANCHOR_US:
            old = self.recent.popleft()
            self.flow_totals[0] -= old[1]
            self.flow_totals[1] -= old[2]
            self.flow_totals[2] -= old[3]
        mid = (bid + ask) / 2
        spread = ask - bid
        if now - self.last_anchor >= ANCHOR_US:
            self.last_anchor = now
            lag100 = next((v for t, v in reversed(self.history) if t <= now - 100_000), mid)
            lag250 = next((v for t, v in reversed(self.history) if t <= now - 250_000), mid)
            bid_depth = sum(order.quantity for order in bids)
            ask_depth = sum(order.quantity for order in asks)
            added_bid, added_ask, flow50 = self.flow_totals
            features = (
                (bid_quantity - ask_quantity) / (bid_quantity + ask_quantity),
                (bid_depth - ask_depth) / (bid_depth + ask_depth),
                log1p(bid_quantity),
                log1p(ask_quantity),
                (1 if flow50 > 0 else -1) * log1p(abs(flow50)),
                log1p(added_bid),
                log1p(added_ask),
                added_bid / (added_bid + bid_quantity) - added_ask / (added_ask + ask_quantity),
                mid - lag100,
                mid - lag250,
                spread,
            )
            self.prediction = PREDICTION_INTERCEPT + sum(
                weight * value for weight, value in zip(PREDICTION_WEIGHTS, features, strict=True)
            )
            if self.emas is None:
                self.emas = [mid, mid, mid]
            else:
                if self.ema_time is None:
                    raise RuntimeError("EMA state has no timestamp")
                elapsed = (now - self.ema_time) / 1e6
                for i, decay in enumerate(EMA_SECONDS):
                    self.emas[i] += (1 - exp(-elapsed / decay)) * (mid - self.emas[i])
            self.ema_time = now
            fast = self.emas[0] - self.emas[1]
            slow = self.emas[1] - self.emas[2]
            direction = 1 if fast > 0 and slow > 0 else -1 if fast < 0 and slow < 0 else 0
            self.target = round(TARGET_SCALE * POSITION_LIMIT * direction)
            self.history.append((now, mid))
            while self.history and self.history[0][0] < now - 350_000:
                self.history.popleft()
        previous_state = self.state
        if spread >= SHOCK_SPREAD:
            self.state = "SHOCK"
            self.stable_since = None
        elif previous_state in ("SHOCK", "RECOVERY"):
            if spread == 1 and min(bid_quantity, ask_quantity) >= MIN_L1:
                if self.stable_since is None:
                    self.stable_since = now
                self.state = "NORMAL" if now - self.stable_since >= RECOVERY_US else "RECOVERY"
            else:
                self.stable_since = None
                self.state = "RECOVERY"
        else:
            self.state = (
                "NORMAL" if spread == 1 and min(bid_quantity, ask_quantity) >= MIN_L1 else "CAUTION"
            )
        if now < START_US:
            return

        self.fragile_sides.clear()
        if GAP_GUARD:
            next_bid = next((o.price for o in bids if o.price < bid), None)
            next_ask = next((o.price for o in asks if o.price > ask), None)
            if bid_quantity <= GAP_QTY and next_bid is not None and bid - next_bid >= GAP_TICKS:
                self.fragile_sides.add(Side.BUY)
            if ask_quantity <= GAP_QTY and next_ask is not None and next_ask - ask >= GAP_TICKS:
                self.fragile_sides.add(Side.SELL)
        center = mid + self.prediction - INVENTORY_SKEW * (self.inventory - self.target)
        desired = {
            Side.BUY: max(1, min(bid, floor(center))),
            Side.SELL: max(ask, ceil(center)),
        }
        quantity = QUOTE_SIZE
        if self.state == "CAUTION":
            quantity = QUOTE_SIZE // CAUTION_DIV
        elif self.state == "RECOVERY":
            quantity = QUOTE_SIZE // CAUTION_DIV
            if self.inventory > self.target:
                desired = {Side.SELL: ask}
            elif self.inventory < self.target:
                desired = {Side.BUY: bid}
            else:
                desired = {}
        elif self.state == "SHOCK":
            desired = {}
            direction = 1 if self.prediction > 0 else -1
            if direction * self.flow_totals[2] > 0 and abs(self.prediction) >= 0.25:
                side = Side.BUY if direction > 0 else Side.SELL
                price = min(ask - 1, bid + 1) if side == Side.BUY else max(bid + 1, ask - 1)
                desired = {side: price}
        levels: dict[tuple[Side, int], int] = {}
        for side, price in desired.items():
            count = GRID_LEVELS if self.state in ("NORMAL", "CAUTION") else 1
            side_quantity = min(quantity, FRAGILE_SIZE) if side in self.fragile_sides else quantity
            for offset in range(count):
                level = price - offset if side == Side.BUY else price + offset
                levels[(side, max(1, level))] = side_quantity
        for order_id, order in self.orders.items():
            if (order["side"], order["price"]) not in levels:
                self.cancel(order_id, order)

        if GAP_GUARD:
            intended: dict[tuple[Side, int], int] = {}
            for order in self.orders.values():
                key = (order["side"], order["price"])
                if order["state"] != "cancel_pending":
                    intended[key] = intended.get(key, 0) + order["remaining"]
            for order_id, order in reversed(list(self.orders.items())):
                key = (order["side"], order["price"])
                if (
                    order["side"] in self.fragile_sides
                    and key in levels
                    and order["state"] == "live"
                    and intended.get(key, 0) > levels[key]
                ):
                    self.cancel(order_id, order)
                    intended[key] -= order["remaining"]
        for (side, price), quantity in levels.items():
            matching = [
                o for o in self.orders.values() if o["side"] == side and o["price"] == price
            ]
            if not FIFO_TOPUPS:
                if not matching:
                    slots = sum(1 for o in self.orders.values() if o["side"] == side)
                    if slots < GRID_LEVELS:
                        self.submit(side, price, quantity)
                continue
            if len(matching) >= MAX_PER_LEVEL or any(o["state"] != "live" for o in matching):
                continue
            deficit = quantity - sum(o["remaining"] for o in matching)
            reserved = sum(o["remaining"] for o in self.orders.values() if o["side"] == side)
            capacity = (
                POSITION_LIMIT - self.inventory - reserved
                if side == Side.BUY
                else POSITION_LIMIT + self.inventory - reserved
            )
            size = min(deficit, capacity)
            if size <= 0 or (matching and size < TOPUP_MIN):
                continue
            slots = sum(1 for o in self.orders.values() if o["side"] == side)
            if slots < SLOT_MULT * GRID_LEVELS:
                self.submit(side, price, size)
        self.check_risk()

    def on_private_order_update(self, event: PrivateOrderEvent) -> None:
        order = self.orders.get(event.order_id)
        if order is None:
            if event.filled_quantity:
                raise RuntimeError("Untracked fill")
            return
        if event.status == OrderStatus.ACCEPTED:
            order["state"] = "live"
        if event.filled_quantity:
            sign = 1 if order["side"] == Side.BUY else -1
            self.inventory += sign * event.filled_quantity
            self.max_inventory = max(self.max_inventory, abs(self.inventory))
        order["remaining"] = event.remaining_quantity
        if event.status in (OrderStatus.FILLED, OrderStatus.CANCELED):
            del self.orders[event.order_id]
        elif event.status == OrderStatus.REJECTED:
            if order["state"] == "cancel_pending":
                order["state"] = "live"
            else:
                del self.orders[event.order_id]
        self.check_risk()