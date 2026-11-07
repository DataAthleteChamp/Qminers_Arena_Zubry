from __future__ import annotations

import numpy as np
import pytest

from simulator.models import (
    BookOrderView,
    OrderBookSnapshot,
    OrderRequest,
    OrderStatus,
    PrivateOrderEvent,
    Side,
)
from simulator.strategy import StrategyContext
from strategies.r0_v2_maker import POSITION_CAP, R0V2MakerStrategy
from tools.experiment_r0_v2_maker import paired_interval


def attached() -> tuple[R0V2MakerStrategy, list[OrderRequest], list[str]]:
    strategy = R0V2MakerStrategy()
    requests: list[OrderRequest] = []
    cancels: list[str] = []

    def submit(request: OrderRequest) -> str:
        requests.append(request)
        return f"u{len(requests)}"

    strategy._attach_context(
        StrategyContext(submit, cancels.append, lambda _order, _quantity: None, lambda: 0)
    )
    return strategy, requests, cancels


def snapshot(now: int = 0, shift: int = 0) -> OrderBookSnapshot:
    return OrderBookSnapshot(
        timestamp_us=now,
        bids=[
            BookOrderView("b1", Side.BUY, 9999 + shift, 20, "market"),
            BookOrderView("b2", Side.BUY, 9999 + shift, 30, "market"),
        ],
        asks=[BookOrderView("a", Side.SELL, 10001 + shift, 50, "market")],
    )


def test_pending_quotes_are_not_duplicated_and_submissions_do_not_change_inventory() -> None:
    strategy, requests, _ = attached()
    strategy.on_order_book_change(snapshot(), [])
    strategy.on_order_book_change(snapshot(3000), [])
    assert len(requests) == 2
    assert strategy.inventory == 0
    assert requests[0].side == Side.BUY
    assert requests[1].side == Side.SELL


def test_cancel_remains_live_until_acknowledged_and_fill_race_is_accounted() -> None:
    strategy, requests, cancels = attached()
    strategy.on_order_book_change(snapshot(), [])
    strategy.on_private_order_update(
        PrivateOrderEvent(
            timestamp_us=5000,
            order_id="u1",
            status=OrderStatus.ACCEPTED,
            remaining_quantity=requests[0].quantity,
        )
    )
    strategy.on_order_book_change(snapshot(30000, -3), [])
    strategy.on_order_book_change(snapshot(31000, -3), [])
    assert cancels.count("u1") == 1
    assert len(requests) == 2
    quantity = requests[0].quantity
    strategy.on_private_order_update(
        PrivateOrderEvent(
            timestamp_us=32000,
            order_id="u1",
            status=OrderStatus.FILLED,
            filled_quantity=quantity,
            remaining_quantity=0,
            fill_price=requests[0].price,
        )
    )
    strategy.on_private_order_update(
        PrivateOrderEvent(timestamp_us=35000, order_id="u1", status=OrderStatus.REJECTED)
    )
    assert strategy.inventory == quantity
    strategy.on_order_book_change(snapshot(36000, -3), [])
    assert len(requests) == 3
    assert requests[-1].side == Side.BUY


def test_partial_fills_preserve_queue_and_worst_case_capacity() -> None:
    strategy, requests, _ = attached()
    strategy.inventory = POSITION_CAP - 2
    strategy.on_order_book_change(snapshot(), [])
    buy = next(request for request in requests if request.side == Side.BUY)
    assert buy.quantity == 2
    strategy.on_private_order_update(
        PrivateOrderEvent(
            timestamp_us=5000,
            order_id="u1",
            status=OrderStatus.ACCEPTED,
            remaining_quantity=2,
        )
    )
    strategy.on_private_order_update(
        PrivateOrderEvent(
            timestamp_us=6000,
            order_id="u1",
            status=OrderStatus.PARTIALLY_FILLED,
            filled_quantity=1,
            remaining_quantity=1,
            fill_price=buy.price,
        )
    )
    assert strategy.inventory == POSITION_CAP - 1
    assert strategy._slots[Side.BUY].remaining == 1
    strategy.on_order_book_change(snapshot(7000), [])
    assert len(requests) == 2
    assert strategy.inventory + strategy._slots[Side.BUY].remaining == POSITION_CAP


def test_unknown_fill_is_an_explicit_error() -> None:
    strategy, _, _ = attached()
    with pytest.raises(RuntimeError, match="unknown order"):
        strategy.on_private_order_update(
            PrivateOrderEvent(
                timestamp_us=0,
                order_id="missing",
                status=OrderStatus.FILLED,
                filled_quantity=1,
                remaining_quantity=0,
            )
        )


def test_paired_bootstrap_uses_differences_not_individual_strategy_errors() -> None:
    interval = paired_interval(np.arange(301, dtype=np.float64), 60)
    assert interval == [300.0, 300.0]
