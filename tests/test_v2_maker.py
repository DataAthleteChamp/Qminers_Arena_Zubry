from pathlib import Path

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
from strategies.zubry_v2 import ZubryV2Strategy
from tools.preflight import inspect_source

ROOT = Path(__file__).resolve().parents[1]


def setup_strategy() -> tuple[ZubryV2Strategy, list[OrderRequest], list[str]]:
    strategy = ZubryV2Strategy()
    sent: list[OrderRequest] = []
    canceled: list[str] = []

    def submit(request: OrderRequest) -> str:
        sent.append(request)
        return f"u{len(sent)}"

    strategy._attach_context(
        StrategyContext(submit, canceled.append, lambda _a, _b: None, lambda: 0)
    )
    return strategy, sent, canceled


def book(bid: int = 99, ask: int = 101) -> OrderBookSnapshot:
    return OrderBookSnapshot(
        timestamp_us=0,
        bids=[BookOrderView("b", Side.BUY, bid, 10, "market")],
        asks=[BookOrderView("a", Side.SELL, ask, 10, "market")],
    )


def test_file_passes_published_rule_preflight() -> None:
    assert inspect_source(ROOT / "strategies/zubry_v2.py") == []


def test_no_duplicate_orders_while_in_flight() -> None:
    strategy, sent, _ = setup_strategy()
    strategy.on_order_book_change(book(), [])
    strategy.on_order_book_change(book(), [])
    assert len(sent) == 2


def test_partial_fill_and_cancel_race_keep_inventory_and_reservation() -> None:
    strategy, sent, canceled = setup_strategy()
    strategy.on_order_book_change(book(), [])
    strategy.on_private_order_update(
        PrivateOrderEvent(
            timestamp_us=5000,
            order_id="u1",
            status=OrderStatus.ACCEPTED,
            remaining_quantity=2,
        )
    )
    strategy.on_order_book_change(book(100, 102), [])
    assert canceled == ["u1"]
    assert len(sent) == 2
    strategy.on_private_order_update(
        PrivateOrderEvent(
            timestamp_us=7000,
            order_id="u1",
            status=OrderStatus.PARTIALLY_FILLED,
            filled_quantity=1,
            remaining_quantity=1,
            fill_price=99,
        )
    )
    strategy.on_order_book_change(book(100, 102), [])
    assert len(sent) == 2
    strategy.on_private_order_update(
        PrivateOrderEvent(
            timestamp_us=10000,
            order_id="u1",
            status=OrderStatus.CANCELED,
            remaining_quantity=1,
        )
    )
    strategy.on_order_book_change(book(100, 102), [])
    assert len(sent) == 3
    assert strategy.inventory == 1


def test_own_quotes_do_not_pollute_market_fair_value() -> None:
    strategy, sent, _ = setup_strategy()
    snapshot = book()
    snapshot.bids.insert(0, BookOrderView("own", Side.BUY, 100, 1000, "user"))
    strategy.on_order_book_change(snapshot, [])
    assert [(order.price, order.quantity) for order in sent] == [(99, 2), (101, 2)]


def test_untracked_fill_is_an_error_not_silent_inventory_loss() -> None:
    strategy, _, _ = setup_strategy()
    with pytest.raises(RuntimeError, match="Untracked"):
        strategy.on_private_order_update(
            PrivateOrderEvent(
                timestamp_us=5000,
                order_id="unknown",
                status=OrderStatus.FILLED,
                filled_quantity=1,
                remaining_quantity=0,
                fill_price=99,
            )
        )


def test_pending_buy_does_not_exceed_soft_inventory_limit() -> None:
    strategy, sent, _ = setup_strategy()
    strategy.inventory = 19
    strategy.on_order_book_change(book(), [])
    assert sent[0].side == Side.BUY
    assert sent[0].quantity == 1
    strategy.on_private_order_update(
        PrivateOrderEvent(
            timestamp_us=5000,
            order_id="u1",
            status=OrderStatus.FILLED,
            filled_quantity=1,
            remaining_quantity=0,
            fill_price=99,
        )
    )
    strategy.on_order_book_change(book(), [])
    assert strategy.inventory == 20
    assert len(sent) == 2
