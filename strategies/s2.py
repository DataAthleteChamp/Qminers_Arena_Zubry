"""Short-horizon order-flow momentum strategy."""

from __future__ import annotations

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


FLOW_WINDOW = 8
PRICE_WINDOW = 8
MIN_FLOW = 3
ORDER_SIZE = 2
MAX_INVENTORY = 20
COOLDOWN_US = 250_000


class FlowMomentumStrategy(BaseStrategy):
  """Trade short-lived agreement between aggressive flow and price movement."""

  def __init__(self) -> None:
    super().__init__()
    self.inventory = 0
    self.flow_history: deque[int] = deque(maxlen=FLOW_WINDOW)
    self.mid_history: deque[float] = deque(maxlen=PRICE_WINDOW)
    self.order_in_flight = False
    self.order_side: Side | None = None
    self.last_order_time_us = -COOLDOWN_US

  def on_order_book_change(
    self, snapshot: OrderBookSnapshot, trades: list[Trade]
  ) -> None:
    """Use recent aggressive flow and BBO movement to choose one IOC side."""
    if not snapshot.bids or not snapshot.asks:
      return

    best_bid = snapshot.bids[0].price
    best_ask = snapshot.asks[0].price
    current_mid = (best_bid + best_ask) / 2.0
    self.mid_history.append(current_mid)

    trade_flow = sum(
      trade.quantity if trade.book_side == "ask" else -trade.quantity
      for trade in trades
    )
    self.flow_history.append(trade_flow)

    if self.order_in_flight or len(self.mid_history) < PRICE_WINDOW:
      return
    if snapshot.timestamp_us - self.last_order_time_us < COOLDOWN_US:
      return

    net_flow = sum(self.flow_history)
    price_move = current_mid - self.mid_history[0]
    signal = 0
    if net_flow >= MIN_FLOW and price_move >= 0:
      signal = 1
    elif net_flow <= -MIN_FLOW and price_move <= 0:
      signal = -1
    if signal == 0:
      return

    if signal > 0:
      if self.inventory + ORDER_SIZE > MAX_INVENTORY:
        return
      side = Side.BUY
      price = best_ask
    else:
      if self.inventory - ORDER_SIZE < -MAX_INVENTORY:
        return
      side = Side.SELL
      price = best_bid

    self.send_order(
      OrderRequest(
        side=side,
        price=max(1, price),
        quantity=ORDER_SIZE,
        order_type=OrderType.IOC,
      )
    )
    self.order_in_flight = True
    self.order_side = side
    self.last_order_time_us = snapshot.timestamp_us

  def on_private_order_update(self, event: PrivateOrderEvent) -> None:
    """Track incremental fills and release the IOC slot at terminal status."""
    if event.filled_quantity and self.order_side is not None:
      direction = 1 if self.order_side == Side.BUY else -1
      self.inventory += direction * event.filled_quantity
    if event.status in (
      OrderStatus.CANCELED,
      OrderStatus.FILLED,
      OrderStatus.REJECTED,
    ):
      self.order_in_flight = False
      self.order_side = None
