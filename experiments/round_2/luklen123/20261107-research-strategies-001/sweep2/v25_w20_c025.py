"""Sweep2 variant v25_w20_c025.
"""

from __future__ import annotations

import bisect
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

# --- quoting core (zubry_v2 style touch maker) ---
QUOTE_SIZE = 2
MAX_INVENTORY = 20
INVENTORY_SKEW = 0.05
HALF_WIDTH = 0.5
# --- regime gate: spread and trailing 1 s mid volatility ---
REQUIRE_SPREAD = 1  # quote only at this spread; 0 disables
VOL_WINDOW_S = 20  
VOL_MAX = 2.5  # ticks; <= 0 disables
KEEP_REDUCING_QUOTE = True  # while gated, keep the inventory-reducing quote
FLATTEN_IN_STRESS = False  # while gated, IOC-reduce inventory to FLATTEN_ABOVE
FLATTEN_ABOVE = 0
# --- block-taker freeze ---
BIG_TAKER = 500  # lots in one market taker order; <= 0 disables
COOLDOWN_S = 0.25  
# --- threshold (bang-bang) inventory control ---
BANG_BANG = False
BB_NEUTRAL = 5  # above: quote only the reducing side
BB_REDUCE = 15  # IOC liquidation target
BB_HARD = 25  # above: IOC-liquidate down to BB_REDUCE
# --- FIFO queue-position guard ---
QUEUE_GUARD = False
QG_L1_MIN = 150  # level volume below which a deep-queued quote is pulled
QG_QPOS_MAX = 30  # market volume ahead of our quote that counts as deep
# --- stop-loss scratch ---
STOP_TICKS = 0  # IOC-close when touch moves this far against avg entry; 0 disables
# --- VPIN toxicity gate (volume buckets, online percentile) ---
VPIN_GATE = False
VPIN_BUCKET = 5000
VPIN_N = 20
VPIN_PCT = 0.9
VPIN_WARMUP = 40  # VPIN observations before the gate may fire
# --- bipower-variation jump gate ---
JUMP_GATE = False
JUMP_K = 60
JUMP_Z = 2.33
# --- large-taker intensity gate (Hawkes-style self-excitation proxy) ---
TOX_GATE = False
TOX_SIZE = 183
TOX_HALF_LIFE_S = 10.0
TOX_PCT = 0.9
TOX_WARMUP_S = 120

_MU43 = 2 ** (2 / 3) * math.gamma(7 / 6) / math.gamma(1 / 2)
_JUMP_THETA = (math.pi / 2) ** 2 + math.pi - 5


class ResearchMaker(BaseStrategy):
    def __init__(self) -> None:
        super().__init__()
        self.inventory = 0
        self.avg_entry = 0.0
        # order_id -> side, price, remaining, accepted, cancel in flight, is_ioc
        self.orders: dict[str, tuple[Side, int, int, bool, bool, bool]] = {}
        self.pull_until = {Side.BUY: -1, Side.SELL: -1}
        self.qg_block: dict[Side, int | None] = {Side.BUY: None, Side.SELL: None}
        # 1 s grid
        self.last_sec = -1
        self.last_sec_mid = 0.0
        self.diffs: deque[float] = deque(maxlen=max(VOL_WINDOW_S, JUMP_K, 3))
        self.vol: float | None = None
        self.jump = False
        # VPIN
        self.b_buy = 0
        self.b_sell = 0
        self.imbalances: deque[int] = deque(maxlen=VPIN_N)
        self.vpin_hist: list[float] = []
        self.vpin_toxic = False
        # large-taker intensity
        self.tox_level = 0.0
        self.tox_t = 0
        self.tox_hist: list[float] = []
        self.tox_toxic = False

    # ------------------------------------------------------------ private feed
    def on_private_order_update(self, event: PrivateOrderEvent) -> None:
        order = self.orders.get(event.order_id)
        if order is None:
            if event.filled_quantity:
                raise RuntimeError("Untracked private fill: inventory cannot be inferred safely.")
            return
        side, price, remaining, accepted, canceling, is_ioc = order
        if event.filled_quantity:
            self.on_fill(side, event.filled_quantity, event.fill_price or price)
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
                is_ioc,
            )

    def on_fill(self, side: Side, qty: int, price: int) -> None:
        signed = qty if side == Side.BUY else -qty
        new = self.inventory + signed
        if self.inventory == 0 or (self.inventory > 0) == (signed > 0):
            self.avg_entry = (self.avg_entry * abs(self.inventory) + price * qty) / abs(new)
        elif new != 0 and (new > 0) != (self.inventory > 0):
            self.avg_entry = float(price)
        self.inventory = new

    # ------------------------------------------------------------ public feed
    def on_order_book_change(self, snapshot: OrderBookSnapshot, trades: list[Trade]) -> None:
        now = snapshot.timestamp_us
        if trades:
            self.on_trades(trades, now)
        bid, bid_size = self.best_market_level(snapshot.bids)
        ask, ask_size = self.best_market_level(snapshot.asks)
        if bid is None or ask is None or bid_size + ask_size == 0:
            self.reconcile(None, None)
            return
        mid = (bid + ask) / 2
        self.update_grid(now, mid)

        stressed = (
            (REQUIRE_SPREAD > 0 and ask - bid != REQUIRE_SPREAD)
            or (VOL_MAX > 0 and self.vol is not None and self.vol > VOL_MAX)
            or self.jump
            or self.vpin_toxic
            or self.tox_toxic
        )

        if STOP_TICKS > 0 and self.inventory != 0:
            if (self.inventory > 0 and bid <= self.avg_entry - STOP_TICKS) or (
                self.inventory < 0 and ask >= self.avg_entry + STOP_TICKS
            ):
                self.reduce_ioc(bid, ask, 0)
        if BANG_BANG and abs(self.inventory) > BB_HARD:
            self.reduce_ioc(bid, ask, BB_REDUCE)
        if stressed and FLATTEN_IN_STRESS and abs(self.inventory) > FLATTEN_ABOVE:
            self.reduce_ioc(bid, ask, FLATTEN_ABOVE)

        center = mid - INVENTORY_SKEW * self.inventory
        buy_price: int | None = max(1, min(bid, math.floor(center - HALF_WIDTH)))
        sell_price: int | None = max(ask, math.ceil(center + HALF_WIDTH), buy_price + 1)

        if self.inventory >= MAX_INVENTORY:
            buy_price = None
        if self.inventory <= -MAX_INVENTORY:
            sell_price = None
        if BANG_BANG and self.inventory > BB_NEUTRAL:
            buy_price = None
        if BANG_BANG and self.inventory < -BB_NEUTRAL:
            sell_price = None
        if now < self.pull_until[Side.BUY]:
            buy_price = None
        if now < self.pull_until[Side.SELL]:
            sell_price = None
        if stressed:
            if not (KEEP_REDUCING_QUOTE and self.inventory > 0):
                sell_price = None
            if not (KEEP_REDUCING_QUOTE and self.inventory < 0):
                buy_price = None
        if QUEUE_GUARD:
            buy_price = self.queue_guard(Side.BUY, snapshot.bids, buy_price)
            sell_price = self.queue_guard(Side.SELL, snapshot.asks, sell_price)

        self.reconcile(buy_price, sell_price)

    # ------------------------------------------------------------ signals
    def on_trades(self, trades: list[Trade], now: int) -> None:
        per_taker: dict[str, list] = {}
        for trade in trades:
            if trade.taker_owner != "market":
                continue
            buy = trade.book_side == "ask"
            agg = per_taker.setdefault(trade.taker_order_id, [0, buy])
            agg[0] += trade.quantity
            if VPIN_GATE:
                self.add_vpin(trade.quantity, buy)
        for qty, buy in per_taker.values():
            if BIG_TAKER > 0 and qty >= BIG_TAKER:
                hit = Side.SELL if buy else Side.BUY
                until = now + int(COOLDOWN_S * 1_000_000)
                self.pull_until[hit] = max(self.pull_until[hit], until)
            if TOX_GATE and qty >= TOX_SIZE:
                self.decay_tox(now)
                self.tox_level += 1.0

    def add_vpin(self, qty: int, buy: bool) -> None:
        while qty > 0:
            room = VPIN_BUCKET - self.b_buy - self.b_sell
            take = min(room, qty)
            if buy:
                self.b_buy += take
            else:
                self.b_sell += take
            qty -= take
            if self.b_buy + self.b_sell >= VPIN_BUCKET:
                self.imbalances.append(abs(self.b_buy - self.b_sell))
                self.b_buy = self.b_sell = 0
                if len(self.imbalances) == VPIN_N:
                    vpin = sum(self.imbalances) / (VPIN_N * VPIN_BUCKET)
                    hist = self.vpin_hist
                    if len(hist) >= VPIN_WARMUP:
                        self.vpin_toxic = vpin > hist[int(VPIN_PCT * (len(hist) - 1))]
                    bisect.insort(hist, vpin)

    def decay_tox(self, now: int) -> None:
        dt = (now - self.tox_t) / 1_000_000
        if dt > 0:
            self.tox_level *= 0.5 ** (dt / TOX_HALF_LIFE_S)
            self.tox_t = now

    def update_grid(self, now: int, mid: float) -> None:
        sec = now // 1_000_000
        if self.last_sec < 0:
            self.last_sec = sec
            self.last_sec_mid = mid
            self.tox_t = now
            return
        if sec <= self.last_sec:
            return
        steps = min(sec - self.last_sec, self.diffs.maxlen or 1)
        for i in range(steps):
            self.diffs.append(mid - self.last_sec_mid if i == 0 else 0.0)
        self.last_sec = sec
        self.last_sec_mid = mid
        d = list(self.diffs)
        if VOL_MAX > 0:
            w = d[-VOL_WINDOW_S:]
            n = len(w)
            if n >= 10:
                m = sum(w) / n
                self.vol = math.sqrt(sum((x - m) ** 2 for x in w) / (n - 1))
        if JUMP_GATE:
            self.jump = self.jump_z(d[-JUMP_K:]) > JUMP_Z
        if TOX_GATE:
            self.decay_tox(now)
            hist = self.tox_hist
            if len(hist) >= TOX_WARMUP_S:
                self.tox_toxic = self.tox_level > hist[int(TOX_PCT * (len(hist) - 1))]
            bisect.insort(hist, self.tox_level)

    @staticmethod
    def jump_z(r: list[float]) -> float:
        k = len(r)
        if k < 10:
            return 0.0
        a = [abs(x) for x in r]
        rv = sum(x * x for x in r)
        if rv <= 0:
            return 0.0
        bv = (math.pi / 2) * (k / (k - 1)) * sum(a[i] * a[i - 1] for i in range(1, k))
        if bv <= 0:
            return math.inf
        tq = (
            k
            * _MU43**-3
            * (k / (k - 2))
            * sum((a[i] * a[i - 1] * a[i - 2]) ** (4 / 3) for i in range(2, k))
        )
        denom = math.sqrt(_JUMP_THETA / k * max(1.0, tq / (bv * bv)))
        return ((rv - bv) / rv) / denom

    def queue_guard(self, side: Side, levels: list, target: int | None) -> int | None:
        """Pull a deep-queued quote when its level drains; do not rejoin that level."""
        block = self.qg_block[side]
        if target is None or (block is not None and target != block):
            self.qg_block[side] = None
            block = None
        for order_id, order in self.orders.items():
            o_side, price, _, accepted, canceling, is_ioc = order
            if o_side != side or is_ioc or not accepted or canceling:
                continue
            total = 0
            ahead = 0
            seen = False
            for view in levels:
                if view.price != price:
                    if total:
                        break
                    continue
                total += view.quantity
                if view.order_id == order_id:
                    seen = True
                elif not seen and view.owner == "market":
                    ahead += view.quantity
            if seen and total < QG_L1_MIN and ahead > QG_QPOS_MAX:
                self.qg_block[side] = price
                return None
        if block is not None and target == block:
            return None
        return target

    @staticmethod
    def best_market_level(levels: list) -> tuple[int | None, int]:
        best = None
        size = 0
        for order in levels:
            if order.owner != "market":
                continue
            if best is None:
                best = order.price
            if order.price != best:
                break
            size += order.quantity
        return best, size

    # ------------------------------------------------------------ execution
    def reduce_ioc(self, bid: int, ask: int, target_abs: int) -> None:
        if any(o[5] for o in self.orders.values()):
            return  # one IOC in flight at a time
        excess = abs(self.inventory) - target_abs
        if excess <= 0:
            return
        side = Side.SELL if self.inventory > 0 else Side.BUY
        price = bid if side == Side.SELL else ask
        order_id = self.send_order(
            OrderRequest(side=side, price=price, quantity=excess, order_type=OrderType.IOC)
        )
        self.orders[order_id] = (side, price, excess, False, False, True)

    def reconcile(self, buy_price: int | None, sell_price: int | None) -> None:
        targets = {Side.BUY: buy_price, Side.SELL: sell_price}
        for order_id, order in list(self.orders.items()):
            side, price, remaining, accepted, canceling, is_ioc = order
            if is_ioc:
                continue
            if accepted and not canceling and targets[side] != price:
                self.cancel_order(order_id)
                self.orders[order_id] = (side, price, remaining, accepted, True, is_ioc)
        for side in (Side.BUY, Side.SELL):
            target_price = targets[side]
            if target_price is None or any(o[0] == side and not o[5] for o in self.orders.values()):
                continue
            pending_ioc = sum(o[2] for o in self.orders.values() if o[5] and o[0] == side)
            sign = 1 if side == Side.BUY else -1
            headroom = MAX_INVENTORY - sign * self.inventory - pending_ioc
            quantity = min(QUOTE_SIZE, headroom)
            if quantity <= 0:
                continue
            order_id = self.send_order(
                OrderRequest(
                    side=side, price=target_price, quantity=quantity, order_type=OrderType.LIMIT
                )
            )
            self.orders[order_id] = (side, target_price, quantity, False, False, False)
