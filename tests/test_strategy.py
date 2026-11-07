from __future__ import annotations

from pathlib import Path

import pytest

from simulator.main import load_strategy_from_file
from simulator.models import (
    BookOrderView,
    OrderBookSnapshot,
    OrderRequest,
    OrderStatus,
    PrivateOrderEvent,
    Side,
    Trade,
)
from simulator.strategy import StrategyContext

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("status", [OrderStatus.CANCELED, OrderStatus.REJECTED])
def test_missed_ioc_frees_slot_and_can_retry_same_side(status: OrderStatus) -> None:
    strategy = load_strategy_from_file(ROOT / "strategies/zubry.py")
    sent: list[OrderRequest] = []

    def submit(request: OrderRequest) -> str:
        sent.append(request)
        return f"u{len(sent)}"

    strategy._attach_context(
        StrategyContext(submit, lambda _: None, lambda _a, _b: None, lambda: 0)
    )
    snapshot = OrderBookSnapshot(
        timestamp_us=0,
        bids=[BookOrderView("b", Side.BUY, 9999, 10, "market")],
        asks=[BookOrderView("a", Side.SELL, 10001, 10, "market")],
    )
    flow = [
        Trade(
            timestamp_us=0,
            price=10001,
            quantity=2,
            taker_order_id="t",
            maker_order_id="a",
            taker_owner="market",
            maker_owner="market",
            book_side="ask",
        )
    ]
    strategy.on_order_book_change(snapshot, flow)
    strategy.on_order_book_change(snapshot, flow)
    assert len(sent) == 1
    strategy.on_private_order_update(
        PrivateOrderEvent(timestamp_us=5000, order_id="u1", status=status)
    )
    strategy.on_order_book_change(snapshot, flow)
    assert len(sent) == 2
    assert sent[-1].side == Side.BUY
