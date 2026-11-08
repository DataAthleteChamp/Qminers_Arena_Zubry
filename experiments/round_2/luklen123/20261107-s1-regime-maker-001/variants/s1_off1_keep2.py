"""S1: regime-gated passive maker with big-taker side pull (Round 2 candidate).

Mechanisms (see knowledge/round_2/luklen123/round2-public-tape-profile.md):
- Quote at the touch (inventory-skewed midpoint, like zubry_v2) only while the
  market spread is REQUIRE_SPREAD ticks and trailing 1 s mid volatility is
  below VOL_MAX; otherwise stand aside (optionally keep the inventory-reducing quote).
- After a market taker order of at least BIG_TAKER lots, pull our quote on the
  side it hit for COOLDOWN_S seconds. Disabled by default: it cost PnL on both tapes.
- Optional IOC flattening while the regime is stressed (default disabled).
No hardcoded price anchor, schedule, filesystem or network access.
"""

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

QUOTE_SIZE = 2
MAX_INVENTORY = 20
INVENTORY_SKEW = 0.05
HALF_WIDTH = 0.5

REQUIRE_SPREAD = 1  # quote only when market spread equals this; 0 disables the gate
VOL_WINDOW_S = 60  # trailing window of 1 s mid changes
VOL_MAX = 3.0  # ticks; std of 1 s mid changes; <= 0 disables the gate
BIG_TAKER = 0  # lots per taker; <= 0 disables the pull (200 lost on R1 and R2, see notes)
COOLDOWN_S = 2.0
KEEP_REDUCING_QUOTE = True  # while gated, still quote the side that reduces inventory
FLATTEN_IN_STRESS = False  # while gated, IOC-close inventory beyond FLATTEN_ABOVE
FLATTEN_ABOVE = 0
QUOTE_OFFSET = 1  # ticks behind the computed touch quote (pre-position in the queue)
KEEP_BEHIND = 2  # keep a resting quote up to this many ticks behind its target (keeps priority)


class S1Strategy(BaseStrategy):
    def __init__(self) -> None:
        super().__init__()
        self.inventory = 0
        # order_id -> side, price, remaining, accepted, cancel in flight, is_ioc
        self.orders: dict[str, tuple[Side, int, int, bool, bool, bool]] = {}
        self.last_sec = -1
        self.last_sec_mid = 0.0
        self.diffs: deque[float] = deque()
        self.sum_d = 0.0
        self.sum_d2 = 0.0
        self.pull_until = {Side.BUY: -1, Side.SELL: -1}
        self.taker_qty: dict[str, int] = {}

    # ---------------------------------------------------------------- private feed
    def on_private_order_update(self, event: PrivateOrderEvent) -> None:
        order = self.orders.get(event.order_id)
        if order is None:
            if event.filled_quantity:
                raise RuntimeError("Untracked private fill: inventory cannot be inferred safely.")
            return
        side, price, remaining, accepted, canceling, is_ioc = order
        if event.filled_quantity:
            self.inventory += event.filled_quantity * (1 if side == Side.BUY else -1)
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

    # ---------------------------------------------------------------- public feed
    def on_order_book_change(self, snapshot: OrderBookSnapshot, trades: list[Trade]) -> None:
        now = snapshot.timestamp_us
        self.track_takers(trades, now)

        bid, bid_size = self.best_market_level(snapshot.bids)
        ask, ask_size = self.best_market_level(snapshot.asks)
        if bid is None or ask is None or bid_size + ask_size == 0:
            self.reconcile(None, None)
            return
        mid = (bid + ask) / 2
        vol = self.update_vol(now, mid)

        stressed = (REQUIRE_SPREAD > 0 and ask - bid != REQUIRE_SPREAD) or (
            VOL_MAX > 0 and vol is not None and vol > VOL_MAX
        )

        center = mid - INVENTORY_SKEW * self.inventory
        buy_price: int | None = max(1, min(bid, math.floor(center - HALF_WIDTH)))
        sell_price: int | None = max(ask, math.ceil(center + HALF_WIDTH), buy_price + 1)
        if QUOTE_OFFSET:
            buy_price = max(1, buy_price - QUOTE_OFFSET)
            sell_price += QUOTE_OFFSET

        if self.inventory >= MAX_INVENTORY:
            buy_price = None
        if self.inventory <= -MAX_INVENTORY:
            sell_price = None
        if now < self.pull_until[Side.BUY]:
            buy_price = None
        if now < self.pull_until[Side.SELL]:
            sell_price = None

        if stressed:
            if FLATTEN_IN_STRESS and abs(self.inventory) > FLATTEN_ABOVE:
                self.flatten(bid, ask)
            if not (KEEP_REDUCING_QUOTE and self.inventory > 0):
                sell_price = None
            if not (KEEP_REDUCING_QUOTE and self.inventory < 0):
                buy_price = None

        self.reconcile(buy_price, sell_price)

    # ---------------------------------------------------------------- signals
    def track_takers(self, trades: list[Trade], now: int) -> None:
        if BIG_TAKER <= 0 or not trades:
            return
        for trade in trades:
            if trade.taker_owner != "market":
                continue
            qty = self.taker_qty.get(trade.taker_order_id, 0) + trade.quantity
            self.taker_qty[trade.taker_order_id] = qty
            if qty >= BIG_TAKER:
                # taker sold into bids -> price likely continues down -> stop buying
                hit = Side.BUY if trade.book_side == "bid" else Side.SELL
                self.pull_until[hit] = max(self.pull_until[hit], now + int(COOLDOWN_S * 1_000_000))
        if len(self.taker_qty) > 64:
            self.taker_qty.clear()

    def update_vol(self, now: int, mid: float) -> float | None:
        sec = now // 1_000_000
        if self.last_sec < 0:
            self.last_sec = sec
            self.last_sec_mid = mid
            return None
        if sec > self.last_sec:
            steps = min(sec - self.last_sec, VOL_WINDOW_S)
            # the whole change since the last sample is assigned to one step; the rest are flat
            for i in range(steps):
                d = mid - self.last_sec_mid if i == 0 else 0.0
                self.diffs.append(d)
                self.sum_d += d
                self.sum_d2 += d * d
                if len(self.diffs) > VOL_WINDOW_S:
                    old = self.diffs.popleft()
                    self.sum_d -= old
                    self.sum_d2 -= old * old
            self.last_sec = sec
            self.last_sec_mid = mid
        n = len(self.diffs)
        if n < 10:
            return None
        var = max(0.0, (self.sum_d2 - self.sum_d * self.sum_d / n) / (n - 1))
        return math.sqrt(var)

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

    # ---------------------------------------------------------------- execution
    def flatten(self, bid: int, ask: int) -> None:
        if any(o[5] for o in self.orders.values()):
            return  # one IOC in flight at a time
        excess = abs(self.inventory) - FLATTEN_ABOVE
        if excess <= 0:
            return
        side = Side.SELL if self.inventory > 0 else Side.BUY
        price = bid if side == Side.SELL else ask
        order_id = self.send_order(
            OrderRequest(side=side, price=price, quantity=excess, order_type=OrderType.IOC)
        )
        self.orders[order_id] = (side, price, excess, False, False, True)

    @staticmethod
    def keep(side: Side, price: int, target: int | None) -> bool:
        """Keep a resting quote inside [target - KEEP_BEHIND, target + QUOTE_OFFSET] (buy side;
        mirrored for sells), so it holds queue priority while the touch moves toward it."""
        if target is None:
            return False
        if side == Side.BUY:
            return target - KEEP_BEHIND <= price <= target + QUOTE_OFFSET
        return target - QUOTE_OFFSET <= price <= target + KEEP_BEHIND

    def reconcile(self, buy_price: int | None, sell_price: int | None) -> None:
        targets = {Side.BUY: buy_price, Side.SELL: sell_price}
        for order_id, order in list(self.orders.items()):
            side, price, remaining, accepted, canceling, is_ioc = order
            if is_ioc:
                continue
            if accepted and not canceling and not self.keep(side, price, targets[side]):
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
