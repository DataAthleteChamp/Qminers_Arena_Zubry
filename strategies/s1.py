"""Transient order-flow reversal and adaptive micro-price mean reversion."""

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


WINDOW = 256
MIN_HISTORY = 64
ENTRY_Z = 2.0
EXIT_Z = 0.25
MAX_INVENTORY = 20
ORDER_SIZE = 2
ORDER_TIMEOUT_US = 30_000_000
FILTER_CONFIRMATION_ONLY = True
FLOW_QUANTILE = 0.99
REQUIRE_OBI_CONFIRMATION = False


class S1Strategy(BaseStrategy):
  """Use only historical public callbacks to place passive reversal orders."""

  def __init__(self) -> None:
    super().__init__()
    self.inventory = 0
    self.obi_history: list[float] = []
    self.ofi_history: list[float] = []
    self.previous_bid: tuple[int, int] | None = None
    self.previous_ask: tuple[int, int] | None = None
    self.filter_mean = 0.0
    self.filter_drift = 0.0
    self.filter_variance = 1.0
    self.filter_ready = False
    self.last_microprice: float | None = None
    self.orders: dict[str, tuple[Side, int, int, bool]] = {}

  def on_order_book_change(self, snapshot: OrderBookSnapshot, trades: list[Trade]) -> None:
    book = self._market_book(snapshot)
    if book is None:
      return
    bid, bid_size, ask, ask_size, obi, microprice = book
    flow = self._order_flow(trades, bid, bid_size, ask, ask_size)
    self._append(self.obi_history, obi)
    self._append(self.ofi_history, flow)
    innovation_z = self._update_filter(microprice - (bid + ask) / 2.0)
    self.previous_bid = (bid, bid_size)
    self.previous_ask = (ask, ask_size)
    self.last_microprice = microprice

    if len(self.obi_history) < MIN_HISTORY or innovation_z is None:
      return
    obi_z = self._z_score(self.obi_history)
    flow_low, flow_high = self._quantiles(self.ofi_history, FLOW_QUANTILE)
    signal = 0
    if flow > flow_high and (not REQUIRE_OBI_CONFIRMATION or obi_z > ENTRY_Z):
      signal = -1
    elif flow < flow_low and (not REQUIRE_OBI_CONFIRMATION or obi_z < -ENTRY_Z):
      signal = 1
    if abs(innovation_z) > ENTRY_Z:
      filter_signal = -1 if innovation_z > 0 else 1
      if signal == filter_signal:
        signal = filter_signal
      elif FILTER_CONFIRMATION_ONLY:
        signal = 0
      else:
        signal = filter_signal

    self._manage_order(snapshot.timestamp_us, signal, bid, ask, innovation_z, obi_z)

  def on_private_order_update(self, event: PrivateOrderEvent) -> None:
    order = self.orders.get(event.order_id)
    if order is None:
      return
    side, submitted_at, remaining, canceling = order
    if event.filled_quantity:
      self.inventory += event.filled_quantity * (1 if side == Side.BUY else -1)
    if event.status in (OrderStatus.CANCELED, OrderStatus.REJECTED, OrderStatus.FILLED):
      del self.orders[event.order_id]
    elif event.status in (OrderStatus.ACCEPTED, OrderStatus.PARTIALLY_FILLED, OrderStatus.MODIFIED):
      self.orders[event.order_id] = (
        side,
        submitted_at,
        event.remaining_quantity,
        canceling,
      )

  def _market_book(
    self, snapshot: OrderBookSnapshot
  ) -> tuple[int, int, int, int, float, float] | None:
    bid_levels: dict[int, int] = {}
    ask_levels: dict[int, int] = {}
    for order in snapshot.bids:
      if order.owner == "market":
        bid_levels[order.price] = bid_levels.get(order.price, 0) + order.quantity
    for order in snapshot.asks:
      if order.owner == "market":
        ask_levels[order.price] = ask_levels.get(order.price, 0) + order.quantity
    if not bid_levels or not ask_levels:
      return None
    bid_prices = sorted(bid_levels, reverse=True)[:5]
    ask_prices = sorted(ask_levels)[:5]
    bid = bid_prices[0]
    ask = ask_prices[0]
    bid_size = sum(bid_levels[price] for price in bid_prices)
    ask_size = sum(ask_levels[price] for price in ask_prices)
    if bid_size + ask_size == 0 or ask <= bid:
      return None
    imbalance = (bid_size - ask_size) / (bid_size + ask_size)
    microprice = (ask * bid_size + bid * ask_size) / (bid_size + ask_size)
    return bid, bid_size, ask, ask_size, imbalance, microprice

  def _order_flow(self, trades: list[Trade], bid: int, bid_size: int, ask: int, ask_size: int) -> float:
    flow = sum(
      trade.quantity * (1 if trade.book_side == "ask" else -1)
      for trade in trades
      if trade.taker_owner == "market"
    )
    if self.previous_bid is not None:
      previous_price, previous_size = self.previous_bid
      flow += bid_size if bid > previous_price else -previous_size if bid < previous_price else bid_size - previous_size
    if self.previous_ask is not None:
      previous_price, previous_size = self.previous_ask
      flow -= ask_size if ask < previous_price else -previous_size if ask > previous_price else ask_size - previous_size
    return flow

  def _update_filter(self, observation: float) -> float | None:
    if not self.filter_ready:
      self.filter_mean = observation
      self.filter_drift = 0.0
      self.filter_variance = 1.0
      self.filter_ready = True
      return None
    predicted_mean = self.filter_mean + self.filter_drift
    predicted_variance = self.filter_variance + 0.05
    innovation = observation - predicted_mean
    innovation_variance = predicted_variance + 0.25
    gain = predicted_variance / innovation_variance
    self.filter_mean = predicted_mean + gain * innovation
    self.filter_drift += 0.05 * gain * innovation
    self.filter_variance = max(0.01, (1.0 - gain) * predicted_variance)
    return innovation / math.sqrt(innovation_variance)

  def _manage_order(
    self,
    timestamp_us: int,
    signal: int,
    bid: int,
    ask: int,
    innovation_z: float,
    obi_z: float,
  ) -> None:
    order_item = next(iter(self.orders.items()), None)
    if order_item is not None:
      order_id, (side, submitted_at, remaining, canceling) = order_item
      expired = timestamp_us - submitted_at >= ORDER_TIMEOUT_US
      should_exit = abs(innovation_z) < EXIT_Z and abs(obi_z) < EXIT_Z
      desired_side = self._desired_side(signal)
      if not canceling and (expired or should_exit or desired_side != side):
        self.cancel_order(order_id)
        self.orders[order_id] = (side, submitted_at, remaining, True)
      return
    side = self._desired_side(signal)
    if side is None:
      return
    if side == Side.BUY and self.inventory + ORDER_SIZE > MAX_INVENTORY:
      return
    if side == Side.SELL and self.inventory - ORDER_SIZE < -MAX_INVENTORY:
      return
    price = bid if side == Side.BUY else ask
    order_id = self.send_order(
      OrderRequest(side=side, price=max(1, price), quantity=ORDER_SIZE, order_type=OrderType.LIMIT)
    )
    self.orders[order_id] = (side, timestamp_us, ORDER_SIZE, False)

  def _desired_side(self, signal: int) -> Side | None:
    if signal > 0:
      return Side.BUY
    if signal < 0:
      return Side.SELL
    if self.inventory > 0:
      return Side.SELL
    if self.inventory < 0:
      return Side.BUY
    return None

  @staticmethod
  def _append(values: list[float], value: float) -> None:
    values.append(value)
    if len(values) > WINDOW:
      del values[0]

  @staticmethod
  def _z_score(values: list[float]) -> float:
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return (values[-1] - mean) / math.sqrt(max(variance, 1e-12))

  @staticmethod
  def _quantiles(values: list[float], tail_probability: float) -> tuple[float, float]:
    ordered = sorted(values)
    low_index = int((1.0 - tail_probability) * (len(ordered) - 1))
    high_index = int(tail_probability * (len(ordered) - 1))
    return ordered[low_index], ordered[high_index]
