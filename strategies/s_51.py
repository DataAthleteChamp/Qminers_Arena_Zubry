"""s_41 z względnym progiem detektora (min. 5 ticków) i natychmiastowym wejściem IOC do 100 lotów w
kierunku wykrytego ruchu.
"""

from collections import deque
from math import ceil, exp, floor, log1p, sqrt

from simulator.models import OrderRequest, OrderStatus, OrderType, Side
from simulator.strategy import BaseStrategy

# --- original koziol.py parameters ---
POSITION_LIMIT = 100
QUOTE_SIZE = 32
GRID_LEVELS = 3
INVENTORY_SKEW = 0.01
EMA_SECONDS = (3, 30, 120)
ANCHOR_US = 50_000
RECOVERY_US = 200_000
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
# --- variant switches (defaults reproduce koziol.py exactly) ---
USE_PREDICTION = True  # linear 11-feature short-horizon prediction in the quote centre
USE_TREND_TARGET = True  # EMA-alignment inventory target of +-POSITION_LIMIT
TREND_SCALE = 1.0  # target = TREND_SCALE * POSITION_LIMIT * direction
MICRO_WEIGHT = 0.0  # 1.0 = Stoikov weighted mid instead of mid in the centre
MLOFI_COEF = 0.0  # ticks per unit of decayed multi-level depth imbalance
MLOFI_LEVELS = 5
MLOFI_DECAY = 0.5
SKEW_GAMMA = 0.01  # > 0: skew = max(INVENTORY_SKEW_MIN, SKEW_GAMMA * sigma^2 / 2)
INVENTORY_SKEW_MIN = 0.005
SIGMA_HALF_LIFE_S = 30.0  # EWMA of squared 1 s mid changes
VOL_MAX = 0.0  # > 0: trailing 1 s vol above this forces RECOVERY-style quoting
VOL_WINDOW_S = 20
VPIN_GATE = False  # toxic VPIN removes quotes on the side the flow is hitting
VPIN_BUCKET = 5000
VPIN_N = 20
VPIN_PCT = 0.9
VPIN_WARMUP = 40
BIG_TAKER = 0  # > 0: freeze the hit side for COOLDOWN_US after a taker >= BIG_TAKER lots
COOLDOWN_US = 250_000
KEEP_BAND = 0  # keep a resting grid order up to this many ticks behind the grid (queue priority)
# --- fast move-onset detector (overrides the EMA target for FAST_HOLD_S after a trigger) ---
FAST_K = 2.0  # > 0 enables: |mid move over FAST_LOOKBACK_S| >= FAST_K * sigma_1s * sqrt(lookback)
FAST_LOOKBACK_S = 20
FAST_MIN_TICKS = 5.0  # absolute floor on the trigger move
FAST_HOLD_S = 180
FAST_SCALE = 1.0  # target = FAST_SCALE * POSITION_LIMIT * direction while active
FAST_IOC_QTY = 100  # > 0: on trigger, IOC up to this many lots toward the new target


class TrendInventoryGridMaker(BaseStrategy):
    def __init__(self):
        super().__init__()
        self.inventory = 0
        self.orders = {}
        self.previous_ids = set()
        self.previous_bid = None
        self.previous_ask = None
        self.recent = deque()
        self.flow_totals = [0, 0, 0]
        self.history = deque()
        self.last_anchor = -ANCHOR_US
        self.prediction = 0.0
        self.emas = None
        self.ema_time = None
        self.target = 0
        self.state = "NORMAL"
        self.stable_since = None
        self.max_exposure = 0
        self.max_inventory = 0
        # variant state
        self.last_sec = -1
        self.last_sec_mid = 0.0
        self.diffs = deque(maxlen=max(VOL_WINDOW_S, 2))
        self.vol = None
        self.sigma2 = None
        self.b_buy = 0
        self.b_sell = 0
        self.imbalances = deque(maxlen=VPIN_N)
        self.signed = deque(maxlen=VPIN_N)
        self.vpin_hist = []
        self.vpin_dir = 0
        self.pull_until = {Side.BUY: -1, Side.SELL: -1}
        self.sec_mids = deque(maxlen=max(FAST_LOOKBACK_S + 1, 2))
        self.fast_dir = 0
        self.fast_until = -1
        self.fast_pending_ioc = False

    def cancel(self, order_id, order):
        if order["state"] == "live":
            order["state"] = "cancel_pending"
            self.cancel_order(order_id)

    def submit(self, side, price, quantity):
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
                side=side,
                price=max(1, price),
                quantity=quantity,
                order_type=OrderType.LIMIT,
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
        if self.max_exposure > POSITION_LIMIT:
            raise RuntimeError("Exposure exceeds position limit")

    def submit_ioc(self, side, price, quantity):
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
                side=side, price=max(1, price), quantity=quantity, order_type=OrderType.IOC
            )
        )
        self.orders[order_id] = {
            "side": side,
            "price": price,
            "remaining": quantity,
            "state": "submit_pending",
            "ioc": True,
        }

    # ---------------------------------------------------------------- variant signals
    def update_second(self, now, mid):
        sec = now // 1_000_000
        if self.last_sec < 0:
            self.last_sec = sec
            self.last_sec_mid = mid
            return
        if sec <= self.last_sec:
            return
        steps = sec - self.last_sec
        d = mid - self.last_sec_mid
        for i in range(min(steps, self.diffs.maxlen)):
            self.diffs.append(d if i == 0 else 0.0)
        if SKEW_GAMMA > 0 or FAST_K > 0:
            a = 1 - 0.5 ** (steps / SIGMA_HALF_LIFE_S)
            self.sigma2 = d * d if self.sigma2 is None else self.sigma2 + a * (d * d - self.sigma2)
        if FAST_K > 0:
            for _ in range(min(steps, self.sec_mids.maxlen)):
                self.sec_mids.append(mid)
            if len(self.sec_mids) == self.sec_mids.maxlen and self.sigma2 is not None:
                move = mid - self.sec_mids[0]
                thr = max(FAST_MIN_TICKS, FAST_K * sqrt(self.sigma2 * FAST_LOOKBACK_S))
                if abs(move) >= thr:
                    direction = 1 if move > 0 else -1
                    if direction != self.fast_dir or now >= self.fast_until:
                        self.fast_pending_ioc = FAST_IOC_QTY > 0
                    self.fast_dir = direction
                    self.fast_until = now + FAST_HOLD_S * 1_000_000
        if VOL_MAX > 0 and len(self.diffs) >= 10:
            w = list(self.diffs)[-VOL_WINDOW_S:]
            m = sum(w) / len(w)
            self.vol = sqrt(sum((x - m) ** 2 for x in w) / (len(w) - 1))
        self.last_sec = sec
        self.last_sec_mid = mid

    def on_market_trades(self, trades, now):
        per_taker = {}
        for trade in trades:
            if trade.taker_owner != "market":
                continue
            buy = trade.book_side == "ask"
            agg = per_taker.setdefault(trade.taker_order_id, [0, buy])
            agg[0] += trade.quantity
            if VPIN_GATE:
                self.add_vpin(trade.quantity, buy)
        if BIG_TAKER > 0:
            for qty, buy in per_taker.values():
                if qty >= BIG_TAKER:
                    hit = Side.SELL if buy else Side.BUY
                    self.pull_until[hit] = max(self.pull_until[hit], now + COOLDOWN_US)

    def add_vpin(self, qty, buy):
        while qty > 0:
            take = min(VPIN_BUCKET - self.b_buy - self.b_sell, qty)
            if buy:
                self.b_buy += take
            else:
                self.b_sell += take
            qty -= take
            if self.b_buy + self.b_sell >= VPIN_BUCKET:
                self.imbalances.append(abs(self.b_buy - self.b_sell))
                self.signed.append(self.b_buy - self.b_sell)
                self.b_buy = self.b_sell = 0
                if len(self.imbalances) == VPIN_N:
                    vpin = sum(self.imbalances) / (VPIN_N * VPIN_BUCKET)
                    hist = self.vpin_hist
                    toxic = False
                    if len(hist) >= VPIN_WARMUP:
                        toxic = vpin > hist[int(VPIN_PCT * (len(hist) - 1))]
                    net = sum(self.signed)
                    self.vpin_dir = (1 if net > 0 else -1) if toxic else 0
                    lo, hi = 0, len(hist)
                    while lo < hi:
                        m = (lo + hi) // 2
                        if hist[m] < vpin:
                            lo = m + 1
                        else:
                            hi = m
                    hist.insert(lo, vpin)

    @staticmethod
    def depth_imbalance(bids, asks):
        def levels(orders):
            out = []
            for order in orders:
                if out and out[-1][0] == order.price:
                    out[-1][1] += order.quantity
                elif len(out) < MLOFI_LEVELS:
                    out.append([order.price, order.quantity])
                else:
                    break
            return out

        num = 0.0
        den = 0.0
        w = 1.0
        for (_, bq), (_, aq) in zip(levels(bids), levels(asks), strict=False):
            num += w * (bq - aq)
            den += w * (bq + aq)
            w *= MLOFI_DECAY
        return num / den if den else 0.0

    # ---------------------------------------------------------------- main loop
    def on_order_book_change(self, snapshot, trades):
        now = self.now_us()
        if trades and (VPIN_GATE or BIG_TAKER > 0):
            self.on_market_trades(trades, now)
        bids = [order for order in snapshot.bids if order.owner == "market"]
        asks = [order for order in snapshot.asks if order.owner == "market"]
        if not bids or not asks:
            for order_id, order in self.orders.items():
                self.cancel(order_id, order)
            self.previous_ids = {order.order_id for order in bids + asks}
            self.previous_bid = bids[0].price if bids else None
            self.previous_ask = asks[0].price if asks else None
            self.stable_since = None
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
        self.update_second(now, mid)
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
                elapsed = (now - self.ema_time) / 1e6
                for i, decay in enumerate(EMA_SECONDS):
                    self.emas[i] += (1 - exp(-elapsed / decay)) * (mid - self.emas[i])
            self.ema_time = now
            fast = self.emas[0] - self.emas[1]
            slow = self.emas[1] - self.emas[2]
            direction = 1 if fast > 0 and slow > 0 else -1 if fast < 0 and slow < 0 else 0
            self.target = round(TREND_SCALE * POSITION_LIMIT * direction) if USE_TREND_TARGET else 0
            self.history.append((now, mid))
            while self.history and self.history[0][0] < now - 350_000:
                self.history.popleft()
        if FAST_K > 0 and now < self.fast_until:
            self.target = round(FAST_SCALE * POSITION_LIMIT * self.fast_dir)
            if self.fast_pending_ioc:
                self.fast_pending_ioc = False
                gap = self.target - self.inventory
                if gap:
                    side = Side.BUY if gap > 0 else Side.SELL
                    self.submit_ioc(
                        side, ask if side == Side.BUY else bid, min(abs(gap), FAST_IOC_QTY)
                    )

        previous_state = self.state
        if spread >= 3:
            self.state = "SHOCK"
            self.stable_since = None
        elif previous_state in ("SHOCK", "RECOVERY"):
            if spread == 1 and min(bid_quantity, ask_quantity) >= 100:
                if self.stable_since is None:
                    self.stable_since = now
                self.state = "NORMAL" if now - self.stable_since >= RECOVERY_US else "RECOVERY"
            else:
                self.stable_since = None
                self.state = "RECOVERY"
        else:
            self.state = (
                "NORMAL" if spread == 1 and min(bid_quantity, ask_quantity) >= 100 else "CAUTION"
            )
        if VOL_MAX > 0 and self.vol is not None and self.vol > VOL_MAX and self.state != "SHOCK":
            self.state = "RECOVERY"
            self.stable_since = None

        base = mid
        if MICRO_WEIGHT:
            micro = (bid * ask_quantity + ask * bid_quantity) / (bid_quantity + ask_quantity)
            base = mid + MICRO_WEIGHT * (micro - mid)
        if MLOFI_COEF:
            base += MLOFI_COEF * self.depth_imbalance(bids, asks)
        skew = INVENTORY_SKEW
        if SKEW_GAMMA > 0 and self.sigma2 is not None:
            skew = max(INVENTORY_SKEW_MIN, SKEW_GAMMA * self.sigma2 / 2)
        prediction = self.prediction if USE_PREDICTION else 0.0
        center = base + prediction - skew * (self.inventory - self.target)
        desired = {
            Side.BUY: max(1, min(bid, floor(center))),
            Side.SELL: max(ask, ceil(center)),
        }
        quantity = QUOTE_SIZE
        if self.state == "CAUTION":
            quantity = QUOTE_SIZE // 2
        elif self.state == "RECOVERY":
            quantity = QUOTE_SIZE // 2
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
        if self.vpin_dir > 0:
            desired.pop(Side.SELL, None)  # toxic buying is hitting asks
        elif self.vpin_dir < 0:
            desired.pop(Side.BUY, None)
        for side in (Side.BUY, Side.SELL):
            if now < self.pull_until[side]:
                desired.pop(side, None)

        levels = {}
        for side, price in desired.items():
            count = GRID_LEVELS if self.state in ("NORMAL", "CAUTION") else 1
            for offset in range(count):
                level = price - offset if side == Side.BUY else price + offset
                levels[(side, max(1, level))] = quantity
        for order_id, order in self.orders.items():
            if order.get("ioc"):
                continue
            if (order["side"], order["price"]) not in levels and not self.keep(order, desired):
                self.cancel(order_id, order)
        for (side, price), quantity in levels.items():
            if not any(
                order["side"] == side and order["price"] == price and not order.get("ioc")
                for order in self.orders.values()
            ):
                slots = sum(
                    1
                    for order in self.orders.values()
                    if order["side"] == side and not order.get("ioc")
                )
                if slots < GRID_LEVELS:
                    self.submit(side, price, quantity)

    @staticmethod
    def keep(order, desired):
        """Queue preservation: a resting order slightly behind the grid keeps its priority."""
        if KEEP_BAND <= 0:
            return False
        top = desired.get(order["side"])
        if top is None:
            return False
        depth = GRID_LEVELS - 1 + KEEP_BAND
        if order["side"] == Side.BUY:
            return top - depth <= order["price"] <= top
        return top <= order["price"] <= top + depth

    def on_private_order_update(self, event):
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
