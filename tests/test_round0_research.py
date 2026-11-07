from tools.research_round0 import Point, flow_diagnostics, grid_diagnostics, pre_activation_index


def test_latency_uses_book_before_first_eligible_market_event() -> None:
    times = [0, 1000, 10000, 200000, 300000]
    assert pre_activation_index(times, 0) == 1
    assert pre_activation_index(times, 200000) == 3
    assert pre_activation_index(times, 300000) is None


def test_markout_includes_crossing_spread_and_delayed_exit() -> None:
    points = [
        Point(0, 99, 101, 10, 10, 1, 1),
        Point(1000, 99, 101, 10, 10, 0, 0),
        Point(10000, 109, 111, 10, 10, 0, 0),
        Point(200000, 119, 121, 10, 10, 0, 0),
        Point(300000, 119, 121, 10, 10, 0, 0),
    ]
    first = flow_diagnostics(points, 0, 1_000_000)[0]
    assert first["horizon_seconds"] == 0.1
    assert first["same_direction_midpoint_change_ticks"] == {
        "count": 1,
        "mean": 20.0,
        "min": 20.0,
        "p10": 20.0,
        "median": 20.0,
        "p90": 20.0,
        "max": 20.0,
        "positive_fraction": 1.0,
        "negative_fraction": 0.0,
    }
    markout = first["one_lot_entry_at_touch_exit_markout_ticks"]
    assert isinstance(markout, dict)
    assert markout["mean"] == 18.0
    assert markout["count"] == 1


def test_forward_label_cannot_cross_declared_window() -> None:
    points = [
        Point(0, 99, 101, 10, 10, 1, 1),
        Point(1000, 99, 101, 10, 10, 0, 0),
        Point(10000, 109, 111, 10, 10, 0, 0),
        Point(200000, 119, 121, 10, 10, 0, 0),
        Point(300000, 119, 121, 10, 10, 0, 0),
    ]
    first = flow_diagnostics(points, 0, 150000)[0]
    assert first["eligible_signal_events"] == 0


def test_calendar_sampling_waits_for_complete_quote_without_looking_at_price_moves() -> None:
    points = []
    for second in range(5):
        points.extend(
            [
                Point(second * 1_000_000, None, None, 0, 0, 0, 0),
                Point(second * 1_000_000 + 3, 99 + second, 101 + second, 10, 10, 0, 0),
            ]
        )
    diagnostic = grid_diagnostics(points, 0, 5_000_000)
    one_second = diagnostic["1"]
    assert isinstance(one_second, dict)
    assert one_second["grid_observations"] == 4
