"""Adaptive one-instrument maker with causal regime and inventory controls."""

from __future__ import annotations

from collections import deque
from math import ceil, floor, isfinite, log, sqrt

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


WINDOW = 96
POSITION_LIMIT = 80
HARD_LIMIT = 1000
FREE_ZONE = 100
LATENCY_BUFFER = 25
QUOTE_SIZE = 3
MIN_QUOTE_AGE_US = 25_000
MAX_QUOTE_AGE_US = 500_000
EMERGENCY_SIZE = 25


class S3Strategy(BaseStrategy):
  """Inventory-aware maker; all state is derived from public/private callbacks."""

  def __init__(self) -> None:
    super().__init__()
    self.inventory = 0
    self.mid_history: deque[float] = deque(maxlen=WINDOW)
    self.return_history: deque[float] = deque(maxlen=WINDOW)
    self.flow_history: deque[int] = deque(maxlen=16)
    self.orders: dict[str, list[object]] = {}
    self.last_mid: float | None = None
    self.last_quote_us = 0

  def on_private_order_update(self, event: PrivateOrderEvent) -> None:
    order = self.orders.get(event.order_id)
    if order is None:
      if event.filled_quantity:
        raise RuntimeError("Untracked private fill")
      return
    side = order[0]
    if event.filled_quantity:
      self.inventory += event.filled_quantity * (1 if side == Side.BUY else -1)
    if event.status in (OrderStatus.ACCEPTED, OrderStatus.PARTIALLY_FILLED, OrderStatus.MODIFIED):
      order[2] = event.remaining_quantity
      order[3] = True
    elif event.status in (OrderStatus.CANCELED, OrderStatus.REJECTED, OrderStatus.FILLED):
      del self.orders[event.order_id]

  def on_order_book_change(self, snapshot: OrderBookSnapshot, trades: list[Trade]) -> None:
    market_bid = self._touch(snapshot.bids, reverse=True)
    market_ask = self._touch(snapshot.asks, reverse=False)
    if market_bid is None or market_ask is None:
      self._cancel_all()
      return
    bid, bid_size = market_bid
    ask, ask_size = market_ask
    if ask <= bid:
      self._cancel_all()
      return

    now = snapshot.timestamp_us
    mid = (bid + ask) / 2.0
    self._observe(mid, trades, bid_size, ask_size)
    if abs(self.inventory) > FREE_ZONE:
      self._desperate(now, bid, ask)
      return

    fair = self._fair_value(mid, bid, ask, bid_size, ask_size)
    regime = self._regime()
    width = 1.0 if regime == 1 else 0.0
    buy_price = min(bid, floor(fair - width))
    sell_price = max(ask, ceil(fair + width))
    if sell_price <= buy_price:
      sell_price = buy_price + 1
    self._manage_quote(Side.BUY, max(1, buy_price), now)
    self._manage_quote(Side.SELL, max(1, sell_price), now)

  def _observe(self, mid: float, trades: list[Trade], bid_size: int, ask_size: int) -> None:
    if self.last_mid is not None and mid > 0 and self.last_mid > 0:
      self.return_history.append(log(mid / self.last_mid))
    self.mid_history.append(mid)
    self.last_mid = mid
    flow = sum(
      trade.quantity if trade.book_side == "ask" else -trade.quantity
      for trade in trades
      if trade.taker_owner == "market"
    )
    flow += bid_size - ask_size
    self.flow_history.append(flow)

  def _fair_value(self, mid: float, bid: int, ask: int, bid_size: int, ask_size: int) -> float:
    imbalance = (bid_size - ask_size) / max(1, bid_size + ask_size)
    recent_flow = list(self.flow_history)[-4:]
    flow = sum(recent_flow) / max(1, len(recent_flow))
    scale = max(1.0, ask - bid)
    return mid + 0.35 * scale * imbalance + 0.02 * scale * (flow / max(1, bid_size + ask_size))

  def _regime(self) -> int:
    """Return 1 for momentum, -1 for mean reversion, 0 while warming up."""
    if len(self.mid_history) < 24 or len(self.return_history) < 20:
      return 0
    returns = list(self.return_history)
    mean = sum(returns) / len(returns)
    variance = sum((value - mean) ** 2 for value in returns) / len(returns)
    volatility = sqrt(max(variance, 1e-12))
    fourth = sum((value - mean) ** 4 for value in returns) / len(returns)
    kurtosis = fourth / max(variance * variance, 1e-18)
    hurst = self._hurst(list(self.mid_history))
    adf = self._adf(returns)
    directional = abs(self.mid_history[-1] - self.mid_history[0]) / max(
      1e-9, sum(abs(self.mid_history[index] - self.mid_history[index - 1]) for index in range(1, len(self.mid_history)))
    )
    if not all(isfinite(value) for value in (volatility, kurtosis, hurst, adf, directional)):
      return 0
    if volatility > 0.0015 or kurtosis > 8.0:
      return -1
    if hurst > 0.58 and adf > -2.0 and directional > 0.35:
      return 1
    if hurst < 0.45 or adf < -2.5:
      return -1
    return 0

  @staticmethod
  def _hurst(values: list[float]) -> float:
    returns = [values[index] - values[index - 1] for index in range(1, len(values))]
    if len(returns) < 8:
      return 0.5
    mean = sum(returns) / len(returns)
    cumulative = []
    running = 0.0
    for value in returns:
      running += value - mean
      cumulative.append(running)
    spread = max(cumulative) - min(cumulative)
    deviation = sqrt(sum((value - mean) ** 2 for value in returns) / len(returns))
    if spread <= 0 or deviation <= 0:
      return 0.5
    return max(0.0, min(1.0, log(spread / deviation) / log(len(returns))))

  @staticmethod
  def _adf(returns: list[float]) -> float:
    if len(returns) < 8:
      return 0.0
    y = returns[1:]
    x = returns[:-1]
    x_mean = sum(x) / len(x)
    y_mean = sum(y) / len(y)
    denominator = sum((value - x_mean) ** 2 for value in x)
    if denominator <= 1e-18:
      return 0.0
    beta = sum((x[index] - x_mean) * (y[index] - y_mean) for index in range(len(x))) / denominator
    residual = [y[index] - y_mean - beta * (x[index] - x_mean) for index in range(len(x))]
    error = sqrt(sum(value * value for value in residual) / max(1, len(residual) - 1))
    return (beta - 1.0) * sqrt(denominator) / max(error, 1e-12)

  def _desperate(self, now: int, bid: int, ask: int) -> None:
    # Impulse control: cancel orders that increase risk, then cross the spread.
    side = Side.SELL if self.inventory > 0 else Side.BUY
    self._cancel_same_side(Side.BUY if side == Side.SELL else Side.SELL)
    if any(order[0] == side and order[6] and not order[4] for order in self.orders.values()):
      return
    quantity = min(EMERGENCY_SIZE, abs(self.inventory))
    quantity = self._pre_trade_quantity(side, quantity)
    if quantity <= 0:
      return
    price = bid if side == Side.SELL else ask
    self._send(side, price, quantity, OrderType.IOC, now)

  def _manage_quote(self, side: Side, price: int, now: int) -> None:
    quote = next((order for order in self.orders.values() if order[0] == side and not order[6]), None)
    if quote is not None:
      if quote[4]:
        return
      age = now - int(quote[1])
      if age >= MAX_QUOTE_AGE_US or age >= MIN_QUOTE_AGE_US and quote[2] and quote[3] != price:
        self.cancel_order(str(quote[5]))
        quote[4] = True
      return
    quantity = min(QUOTE_SIZE, self._capacity(side))
    if abs(self.inventory) + self._reserved(side) + LATENCY_BUFFER > HARD_LIMIT:
      return
    if quantity > 0:
      self._send(side, price, quantity, OrderType.LIMIT, now)

  def _send(self, side: Side, price: int, quantity: int, order_type: OrderType, now: int) -> None:
    quantity = self._pre_trade_quantity(side, quantity)
    if quantity <= 0:
      return
    # Keep the latency buffer free for a reducing IOC while orders are in flight.
    if order_type == OrderType.LIMIT and abs(self.inventory) + self._reserved(side) + quantity + LATENCY_BUFFER > HARD_LIMIT:
      return
    order_id = self.send_order(OrderRequest(side=side, price=max(1, price), quantity=quantity, order_type=order_type))
    self.orders[order_id] = [side, now, quantity, False, False, order_id, order_type == OrderType.IOC]

  def _pre_trade_quantity(self, side: Side, quantity: int) -> int:
    """Apply the exchange hard wall to current inventory and pending same-side R."""
    sign = 1 if side == Side.BUY else -1
    reserved = self._reserved(side)
    hard_capacity = HARD_LIMIT - abs(self.inventory) - reserved
    if sign * self.inventory < 0:
      hard_capacity = HARD_LIMIT - reserved + abs(self.inventory)
    return max(0, min(quantity, hard_capacity))

  def _capacity(self, side: Side) -> int:
    sign = 1 if side == Side.BUY else -1
    return max(0, POSITION_LIMIT - sign * self.inventory - self._reserved(side))

  def _reserved(self, side: Side) -> int:
    return sum(int(order[2]) for order in self.orders.values() if order[0] == side and not order[4])

  def _cancel_same_side(self, side: Side) -> None:
    for order in list(self.orders.values()):
      if order[0] == side and not order[4]:
        self.cancel_order(str(order[5]))
        order[4] = True

  def _cancel_all(self) -> None:
    self._cancel_same_side(Side.BUY)
    self._cancel_same_side(Side.SELL)

  @staticmethod
  def _touch(orders: list[BookOrderView], reverse: bool) -> tuple[int, int] | None:
    market = [order for order in orders if order.owner == "market" and order.quantity > 0]
    if not market:
      return None
    price = (max if reverse else min)(order.price for order in market)
    return price, sum(order.quantity for order in market if order.price == price)

    def on_order_book_change(self, snapshot: OrderBookSnapshot, trades: list[Trade]) -> None:
        """React to the public book after every market event; `trades` are those since the previous call."""

    def on_private_order_update(self, event: PrivateOrderEvent) -> None:
        """React to a state change of one of your own orders."""
