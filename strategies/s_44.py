"""Maker z bezpiecznikiem: kwotuje 5 lotów przy spreadzie 1 i spokojnej zmienności, a przy wykryciu
startu ruchu lub drenażu płynności (5-sekundowa średnia L1 < 35% średniej 120 s) wycofuje
kwotowania i zamyka pozycję IOC. Wraca do kwotowania po 30 s spokoju.
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

POSITION_LIMIT = 100  # hard cap on |inventory + same-side pending|
# --- passive maker (touch quotes, inventory skew) ---
MAKER = True
QUOTE_SIZE = 5
MAKER_MAX_INV = 30
INVENTORY_SKEW = 0.05
REQUIRE_SPREAD = 1  # quote only at this spread; 0 disables
VOL_REL_MAX = 1.5  # stand aside when 30 s vol > this x long-run vol; <= 0 disables
# --- volatility estimates (1 s mid grid) ---
SIGMA_HL_S = 120.0  # long-run EWMA half-life of squared 1 s mid changes
SHORT_WIN_S = 30
# --- move-onset detector (relative threshold) ---
DETECT = True
DET_LOOKBACK_S = 20
DET_K = 2.0  # trigger when |move over lookback| >= DET_K * sigma * sqrt(lookback)
DET_MIN_TICKS = 5.0
# --- liquidity-drain early warning ---
DRAIN = True
DRAIN_RATIO = 0.35  # fast EWMA of L1 total (both sides) below this x its slow EWMA
DRAIN_HL_S = 120.0
DRAIN_FAST_HL_S = 5.0
DRAIN_SPREAD = 0  # > 0: also treat spread >= this as drain (off: too frequent in deep-move markets)
# --- breaker: on detector/drain stress, pull quotes (and optionally flatten) ---
BREAKER = True
BREAKER_FLATTEN = True
BREAKER_HOLD_S = 30
# --- ride: on a detected move, take a position with the move ---
RIDE = False
RIDE_SIZE = 60
RIDE_TRAIL_K = 1.5  # exit when retrace from best >= max(RIDE_TRAIL_MIN, K * sigma * sqrt(L))
RIDE_TRAIL_MIN = 5.0
RIDE_MAX_S = 300
RIDE_COOLDOWN_S = 30
IOC_SLIP = 3  # ticks through the opposite best for IOC entries/exits


class CrashStrategy(BaseStrategy):
    def __init__(self) -> None:
        super().__init__()
        self.inventory = 0
        # id -> [side, price, remaining, accepted, canceling, is_ioc]
        self.orders: dict[str, list] = {}
        self.last_sec = -1
        self.sec_mids: deque[float] = deque(maxlen=max(DET_LOOKBACK_S, SHORT_WIN_S) + 1)
        self.sigma2: float | None = None
        self.l1_ewma: float | None = None
        self.l1_fast = 0.0
        self.last_l1_t = 0
        self.stress_until = -1
        self.ride_dir = 0
        self.ride_start = 0
        self.ride_best = 0.0
        self.ride_cool_until = -1
        self.trigger_dir = 0
        self.trigger_new = False

    # ------------------------------------------------------------ private feed
    def on_private_order_update(self, event: PrivateOrderEvent) -> None:
        o = self.orders.get(event.order_id)
        if o is None:
            if event.filled_quantity:
                raise RuntimeError("Untracked private fill")
            return
        if event.filled_quantity:
            self.inventory += event.filled_quantity * (1 if o[0] == Side.BUY else -1)
        if event.status in (OrderStatus.FILLED, OrderStatus.CANCELED, OrderStatus.REJECTED):
            del self.orders[event.order_id]
        elif event.status in (
            OrderStatus.ACCEPTED,
            OrderStatus.PARTIALLY_FILLED,
            OrderStatus.MODIFIED,
        ):
            o[2] = event.remaining_quantity
            o[3] = True

    # ------------------------------------------------------------ helpers
    @staticmethod
    def best_level(levels: list) -> tuple[int | None, int]:
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

    def pending(self, side: Side) -> int:
        return sum(o[2] for o in self.orders.values() if o[0] == side)

    def capacity(self, side: Side) -> int:
        if side == Side.BUY:
            return POSITION_LIMIT - self.inventory - self.pending(Side.BUY)
        return POSITION_LIMIT + self.inventory - self.pending(Side.SELL)

    def ioc_to(self, target: int, bid: int, ask: int) -> None:
        if any(o[5] for o in self.orders.values()):
            return  # one IOC in flight
        gap = target - self.inventory
        if gap == 0:
            return
        side = Side.BUY if gap > 0 else Side.SELL
        qty = min(abs(gap), self.capacity(side))
        if qty <= 0:
            return
        price = ask + IOC_SLIP if side == Side.BUY else max(1, bid - IOC_SLIP)
        oid = self.send_order(
            OrderRequest(side=side, price=price, quantity=qty, order_type=OrderType.IOC)
        )
        self.orders[oid] = [side, price, qty, False, False, True]

    def cancel_quotes(self) -> None:
        for oid, o in self.orders.items():
            if not o[5] and o[3] and not o[4]:
                self.cancel_order(oid)
                o[4] = True

    # ------------------------------------------------------------ signals
    def update_second(self, now: int, mid: float) -> None:
        sec = now // 1_000_000
        if self.last_sec < 0:
            self.last_sec = sec
            self.sec_mids.append(mid)
            return
        if sec <= self.last_sec:
            return
        steps = sec - self.last_sec
        d = mid - self.sec_mids[-1]
        a = 1 - 0.5 ** (steps / SIGMA_HL_S)
        self.sigma2 = d * d if self.sigma2 is None else self.sigma2 + a * (d * d - self.sigma2)
        for _ in range(min(steps, self.sec_mids.maxlen or 1)):
            self.sec_mids.append(mid)
        self.last_sec = sec
        if DETECT and len(self.sec_mids) > DET_LOOKBACK_S and self.sigma2:
            move = mid - self.sec_mids[-1 - DET_LOOKBACK_S]
            thr = max(DET_MIN_TICKS, DET_K * math.sqrt(self.sigma2 * DET_LOOKBACK_S))
            if abs(move) >= thr:
                self.trigger_dir = 1 if move > 0 else -1
                self.trigger_new = True

    def short_vol(self) -> float | None:
        m = list(self.sec_mids)[-SHORT_WIN_S - 1 :]
        if len(m) < 11:
            return None
        diffs = [b - a for a, b in zip(m, m[1:], strict=False)]
        mu = sum(diffs) / len(diffs)
        return math.sqrt(sum((x - mu) ** 2 for x in diffs) / (len(diffs) - 1))

    def drained(self, now: int, l1: int, spread: int) -> bool:
        dt = (now - self.last_l1_t) / 1e6
        self.last_l1_t = now
        if self.l1_ewma is None:
            self.l1_ewma = float(l1)
            self.l1_fast = float(l1)
            return False
        dt = max(dt, 0.0)
        self.l1_ewma += (1 - 0.5 ** (dt / DRAIN_HL_S)) * (l1 - self.l1_ewma)
        self.l1_fast += (1 - 0.5 ** (dt / DRAIN_FAST_HL_S)) * (l1 - self.l1_fast)
        return (DRAIN_SPREAD > 0 and spread >= DRAIN_SPREAD) or (
            self.l1_fast < DRAIN_RATIO * self.l1_ewma
        )

    # ------------------------------------------------------------ main loop
    def on_order_book_change(self, snapshot: OrderBookSnapshot, trades: list[Trade]) -> None:
        now = snapshot.timestamp_us
        bid, bq = self.best_level(snapshot.bids)
        ask, aq = self.best_level(snapshot.asks)
        if bid is None or ask is None:
            self.cancel_quotes()
            return
        mid = (bid + ask) / 2
        spread = ask - bid
        self.update_second(now, mid)
        drain = DRAIN and self.drained(now, bq + aq, spread)

        triggered = self.trigger_new
        self.trigger_new = False
        if BREAKER and (triggered or drain):
            self.stress_until = max(self.stress_until, now + BREAKER_HOLD_S * 1_000_000)

        # ---- ride management
        if RIDE:
            if self.ride_dir:
                self.ride_best = (
                    max(self.ride_best, mid) if self.ride_dir > 0 else min(self.ride_best, mid)
                )
                sig = math.sqrt(self.sigma2 or 1.0)
                trail = max(RIDE_TRAIL_MIN, RIDE_TRAIL_K * sig * math.sqrt(DET_LOOKBACK_S))
                retrace = (self.ride_best - mid) * self.ride_dir
                expired = now - self.ride_start > RIDE_MAX_S * 1_000_000
                reversed_ = triggered and self.trigger_dir != self.ride_dir
                if retrace >= trail or expired or reversed_:
                    self.ride_dir = 0
                    self.ride_cool_until = now + RIDE_COOLDOWN_S * 1_000_000
            if not self.ride_dir and triggered and now >= self.ride_cool_until:
                self.ride_dir = self.trigger_dir
                self.ride_start = now
                self.ride_best = mid
            if self.ride_dir:
                self.cancel_quotes()
                self.ioc_to(self.ride_dir * RIDE_SIZE, bid, ask)
                return
            if abs(self.inventory) > (MAKER_MAX_INV if MAKER else 0):
                self.cancel_quotes()
                self.ioc_to(0, bid, ask)
                return

        stressed = now < self.stress_until
        if stressed:
            self.cancel_quotes()
            if BREAKER_FLATTEN and self.inventory:
                self.ioc_to(0, bid, ask)
            return
        if not MAKER:
            self.cancel_quotes()
            return

        # ---- passive maker
        gate = REQUIRE_SPREAD > 0 and spread != REQUIRE_SPREAD
        if VOL_REL_MAX > 0 and self.sigma2:
            sv = self.short_vol()
            gate = gate or (sv is not None and sv > VOL_REL_MAX * math.sqrt(self.sigma2))
        center = mid - INVENTORY_SKEW * self.inventory
        buy = max(1, min(bid, math.floor(center - 0.5)))
        sell = max(ask, math.ceil(center + 0.5), buy + 1)
        targets: dict[Side, int | None] = {
            Side.BUY: buy if self.inventory < MAKER_MAX_INV else None,
            Side.SELL: sell if self.inventory > -MAKER_MAX_INV else None,
        }
        if gate:
            if self.inventory <= 0:
                targets[Side.SELL] = None
            if self.inventory >= 0:
                targets[Side.BUY] = None
        self.reconcile(targets)

    def reconcile(self, targets: dict[Side, int | None]) -> None:
        for oid, o in self.orders.items():
            if o[5]:
                continue
            if o[3] and not o[4] and targets[o[0]] != o[1]:
                self.cancel_order(oid)
                o[4] = True
        for side in (Side.BUY, Side.SELL):
            price = targets[side]
            if price is None or any(o[0] == side and not o[5] for o in self.orders.values()):
                continue
            sign = 1 if side == Side.BUY else -1
            qty = min(QUOTE_SIZE, MAKER_MAX_INV - sign * self.inventory, self.capacity(side))
            if qty <= 0:
                continue
            oid = self.send_order(
                OrderRequest(side=side, price=price, quantity=qty, order_type=OrderType.LIMIT)
            )
            self.orders[oid] = [side, price, qty, False, False, False]
