"""Descriptive causal research on the real round-0 tape; never submits orders."""

from __future__ import annotations

import argparse
import bisect
import collections
import dataclasses
import statistics
from pathlib import Path

from simulator.main import (
    MAX_POSITION,
    MAX_POTENTIAL_POSITION,
    ORDER_ACCEPT_DELAY_MS,
    POSITION_BREACH_PENALTY_PER_SECOND,
)
from simulator.models import OrderBookSnapshot, Trade
from simulator.simulator import ExchangeSimulator, SimulationConfig
from simulator.strategy import BaseStrategy
from tools.common import ROOT, identifier, now, sha256, source_digest, write_once

HORIZONS_SECONDS = (0.1, 0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0)
WINDOWS = ((0, 1200, "discovery"), (1200, 2400, "chronological-check"), (2400, 3600, "later-check"))


@dataclasses.dataclass(frozen=True, slots=True)
class Point:
    timestamp_us: int
    bid: int | None
    ask: int | None
    bid_size: int
    ask_size: int
    external_flow: int
    trade_matches: int

    @property
    def mid(self) -> float | None:
        if self.bid is None or self.ask is None:
            return None
        return (self.bid + self.ask) / 2

    @property
    def imbalance(self) -> float | None:
        total = self.bid_size + self.ask_size
        if self.bid is None or self.ask is None or not total:
            return None
        return (self.bid_size - self.ask_size) / total


class Observer(BaseStrategy):
    def __init__(self) -> None:
        super().__init__()
        self.points: list[Point] = []
        self.order_counts: collections.Counter[tuple[int, int]] = collections.Counter()

    def on_order_book_change(self, snapshot: OrderBookSnapshot, trades: list[Trade]) -> None:
        bids = [item for item in snapshot.bids if item.owner == "market"]
        asks = [item for item in snapshot.asks if item.owner == "market"]
        bid = bids[0].price if bids else None
        ask = asks[0].price if asks else None
        self.order_counts[(len(bids), len(asks))] += 1
        external = [
            trade
            for trade in trades
            if trade.taker_owner == "market" and trade.maker_owner == "market"
        ]
        self.points.append(
            Point(
                snapshot.timestamp_us,
                bid,
                ask,
                sum(item.quantity for item in bids if item.price == bid),
                sum(item.quantity for item in asks if item.price == ask),
                sum(trade.quantity * (1 if trade.book_side == "ask" else -1) for trade in external),
                len(external),
            )
        )


def summary(values: list[float]) -> dict[str, object]:
    if not values:
        return {"count": 0, "mean": None, "min": None, "max": None}
    ordered = sorted(values)
    return {
        "count": len(values),
        "mean": statistics.mean(values),
        "min": ordered[0],
        "p10": ordered[int((len(ordered) - 1) * 0.1)],
        "median": statistics.median(values),
        "p90": ordered[int((len(ordered) - 1) * 0.9)],
        "max": ordered[-1],
        "positive_fraction": sum(value > 0 for value in values) / len(values),
        "negative_fraction": sum(value < 0 for value in values) / len(values),
    }


def correlation(left: list[float], right: list[float]) -> float | None:
    if len(left) < 3 or len(set(left)) < 2 or len(set(right)) < 2:
        return None
    return statistics.correlation(left, right)


def pre_activation_index(times: list[int], requested_at_us: int) -> int | None:
    """The engine activates before the first market row >= request+latency."""
    event = bisect.bisect_left(times, requested_at_us + ORDER_ACCEPT_DELAY_MS * 1000)
    return event - 1 if 0 < event < len(times) else None


def flow_diagnostics(points: list[Point], start: int, end: int) -> list[dict[str, object]]:
    times = [point.timestamp_us for point in points]
    signals = [
        index
        for index, point in enumerate(points)
        if start <= point.timestamp_us < end and point.external_flow
    ]
    output = []
    for horizon in HORIZONS_SECONDS:
        markouts: list[float] = []
        midpoint_moves: list[float] = []
        sign_flipped_markouts: list[float] = []
        entry_misses = missing_quotes = 0
        eligible = 0
        for index in signals:
            point = points[index]
            requested_exit = bisect.bisect_left(times, point.timestamp_us + int(horizon * 1e6))
            entry_index = pre_activation_index(times, point.timestamp_us)
            if requested_exit >= len(points) or entry_index is None:
                continue
            exit_index = pre_activation_index(times, times[requested_exit])
            if exit_index is None or times[requested_exit] >= end or times[exit_index] >= end:
                continue
            eligible += 1
            entry, exit_point = points[entry_index], points[exit_index]
            p_mid, e_mid = point.mid, exit_point.mid
            if (
                point.bid is None
                or point.ask is None
                or entry.bid is None
                or entry.ask is None
                or exit_point.bid is None
                or exit_point.ask is None
                or p_mid is None
                or e_mid is None
            ):
                missing_quotes += 1
                continue
            sign = 1 if point.external_flow > 0 else -1
            midpoint_moves.append(sign * (e_mid - p_mid))
            buy_fill = entry.ask <= point.ask and entry.ask_size > 0
            sell_fill = entry.bid >= point.bid and entry.bid_size > 0
            if (sign > 0 and not buy_fill) or (sign < 0 and not sell_fill):
                entry_misses += 1
            else:
                markouts.append(
                    float(exit_point.bid - entry.ask if sign > 0 else entry.bid - exit_point.ask)
                )
            if (sign < 0 and buy_fill) or (sign > 0 and sell_fill):
                sign_flipped_markouts.append(
                    float(exit_point.bid - entry.ask if sign < 0 else entry.bid - exit_point.ask)
                )
        output.append(
            {
                "horizon_seconds": horizon,
                "eligible_signal_events": eligible,
                "entry_misses": entry_misses,
                "missing_quotes": missing_quotes,
                "same_direction_midpoint_change_ticks": summary(midpoint_moves),
                "one_lot_entry_at_touch_exit_markout_ticks": summary(markouts),
                "opposite_direction_entry_exit_markout_ticks": summary(sign_flipped_markouts),
            }
        )
    return output


def grid_diagnostics(points: list[Point], start: int, end: int) -> dict[str, object]:
    times = [point.timestamp_us for point in points]
    complete = [point for point in points if point.mid is not None]
    complete_times = [point.timestamp_us for point in complete]
    signal_times = [point.timestamp_us for point in points if point.external_flow]
    signal_signs = [1 if point.external_flow > 0 else -1 for point in points if point.external_flow]
    age_bins = ((0, 1), (1, 3), (3, 5), (5, 8), (8, 30))
    output: dict[str, object] = {}
    for horizon in (1, 3, 6):
        imbalance_values: list[float] = []
        future_changes: list[float] = []
        phases: dict[str, list[float]] = {f"{low}-{high}s": [] for low, high in age_bins}
        used: set[int] = set()
        for timestamp in range(start, end - horizon * 1_000_000, 1_000_000):
            index = bisect.bisect_left(complete_times, timestamp)
            if index >= len(complete) or index in used:
                continue
            point = complete[index]
            label_time = point.timestamp_us + horizon * 1_000_000
            if label_time >= end:
                continue
            used.add(index)
            future = bisect.bisect_right(times, label_time) - 1
            if future < 0:
                continue
            later = points[future]
            p_mid, e_mid, imbalance = point.mid, later.mid, point.imbalance
            if p_mid is None or e_mid is None:
                continue
            change = e_mid - p_mid
            if imbalance is not None:
                imbalance_values.append(imbalance)
                future_changes.append(change)
            last_signal = bisect.bisect_right(signal_times, point.timestamp_us) - 1
            if last_signal < 0:
                continue
            age = (point.timestamp_us - signal_times[last_signal]) / 1e6
            for low, high in age_bins:
                if low <= age < high:
                    phases[f"{low}-{high}s"].append(signal_signs[last_signal] * change)
                    break
        output[str(horizon)] = {
            "future_horizon_seconds": horizon,
            "imbalance_next_mid_correlation": correlation(imbalance_values, future_changes),
            "grid_observations": len(future_changes),
            "sampler": "first complete callback at or after each fixed one-second grid target",
            "last_external_flow_direction_by_causal_age": {
                name: summary(values) for name, values in phases.items()
            },
        }
    return output


def analyze(data: Path, folder: Path, end_seconds: int = 3600) -> None:
    if folder.exists():
        raise FileExistsError("Research ID already exists; keep old evidence and choose a new ID.")
    if end_seconds < 1:
        raise ValueError("Declare a positive end time before running diagnostics.")
    windows_spec = list(WINDOWS)
    if end_seconds > 3600:
        windows_spec.extend(
            (start, min(start + 1200, end_seconds), f"additional-check-{start // 1200 + 1}")
            for start in range(3600, end_seconds, 1200)
        )
    windows_spec = [
        (start, min(end, end_seconds), label)
        for start, end, label in windows_spec
        if start < end_seconds
    ]
    before = sha256(data)
    plan: dict[str, object] = {
        "created_utc": now(),
        "data": str(data.relative_to(ROOT)),
        "data_sha256": before,
        "simulator_sha256": source_digest(),
        "script_sha256": sha256(Path(__file__)),
        "trade_strategy_changes": False,
        "grid_sampler": "first complete callback at or after each fixed calendar target",
        "windows_seconds": windows_spec,
        "horizons_seconds": HORIZONS_SECONDS,
        "hypotheses": [
            "External aggressive flow predicts continuation beyond 5ms, after the bid/ask cost.",
            "Continuation weakens/reverts with causal time since the last external trade.",
            "Static queue imbalance predicts later prices beyond the external-flow explanation.",
        ],
        "reject_if": [
            "Directional effect changes sign or disappears in later chronological blocks.",
            "Edge survives only in midpoint predictions, not opposite-quote markout after latency.",
            "Claim depends on a global price anchor, future event schedule or unavailable depth.",
        ],
        "limitations": [
            "Whole tape was used in earlier baseline runs; these are chronological diagnostics, "
            "not a newly untouched holdout or independent private validation.",
            "No orders are placed. One-lot markout is an isolated quote-path diagnostic, not PnL.",
            "Exit markout uses available opposite quote, not a fully tested exit IOC/portfolio.",
            "Overlapping signals/horizons are dependent and their profits cannot be summed.",
            "Independent sampling/generator identity cannot be verified from this file alone.",
            "One-lot quote diagnostics ignore our counterfactual book changes; actual strategy "
            "replay is required before adoption or sizing.",
        ],
    }
    write_once(folder / "plan.json", plan)
    with (folder / "analysis.py").open("xb") as handle:
        handle.write(Path(__file__).read_bytes())
    observer = Observer()
    config = SimulationConfig(
        order_accept_delay_ms=ORDER_ACCEPT_DELAY_MS,
        public_depth=20,
        max_position=MAX_POSITION,
        max_potential_position=MAX_POTENTIAL_POSITION,
        position_breach_penalty_per_second=POSITION_BREACH_PENALTY_PER_SECOND,
    )
    null = ExchangeSimulator(observer, config).run(data)
    if sha256(data) != before or source_digest() != plan["simulator_sha256"]:
        raise ValueError("Data or official engine changed during analysis.")
    points = observer.points
    if not points or any(
        a.timestamp_us > b.timestamp_us for a, b in zip(points, points[1:], strict=False)
    ):
        raise ValueError("Empty or non-chronological callback sequence.")
    valid = [point for point in points if point.mid is not None]
    gaps = [
        (b.timestamp_us - a.timestamp_us) / 1000 for a, b in zip(points, points[1:], strict=False)
    ]
    quote_gaps = [
        (b.timestamp_us - a.timestamp_us) / 1000 for a, b in zip(valid, valid[1:], strict=False)
    ]
    observed_us = points[-1].timestamp_us - points[0].timestamp_us
    missing_us = sum(
        later.timestamp_us - point.timestamp_us
        for point, later in zip(points, points[1:], strict=False)
        if point.mid is None
    )
    signed_trades = [point for point in points if point.external_flow]
    trade_gaps = [
        (b.timestamp_us - a.timestamp_us) / 1e6
        for a, b in zip(signed_trades, signed_trades[1:], strict=False)
    ]
    spreads = [
        float(point.ask - point.bid)
        for point in valid
        if point.ask is not None and point.bid is not None
    ]
    report: dict[str, object] = {
        "scope": "synthetic round0 descriptive/causal hypothesis research, NOT strategy PnL",
        "null_strategy_result": null.model_dump(mode="json"),
        "data_sha256": before,
        "start_seconds": points[0].timestamp_us / 1e6,
        "end_seconds": points[-1].timestamp_us / 1e6,
        "callback_rows": len(points),
        "valid_two_sided_rows": len(valid),
        "missing_side_rows": len(points) - len(valid),
        "missing_side_time_seconds": missing_us / 1e6,
        "two_sided_wall_clock_fraction": 1 - missing_us / observed_us,
        "event_gap_ms": summary(gaps),
        "complete_quote_gap_ms": summary(quote_gaps),
        "spread_ticks": summary(spreads),
        "visible_market_order_counts": {
            f"bids={bids},asks={asks}": count
            for (bids, asks), count in observer.order_counts.items()
        },
        "signed_trade_callback_count": len(signed_trades),
        "trade_matches": sum(point.trade_matches for point in points),
        "aggressor_interarrival_seconds": summary(trade_gaps),
        "buy_aggressor_callbacks": sum(point.external_flow > 0 for point in points),
        "sell_aggressor_callbacks": sum(point.external_flow < 0 for point in points),
        "windows": [],
    }
    windows: list[dict[str, object]] = []
    for start, end, label in windows_spec:
        subset = [point for point in valid if start * 1e6 <= point.timestamp_us < end * 1e6]
        mids = [value for point in subset if (value := point.mid) is not None]
        flows = flow_diagnostics(points, start * 1_000_000, end * 1_000_000)
        windows.append(
            {
                "label": label,
                "start_seconds": start,
                "end_seconds": end,
                "mid_ticks": summary(mids),
                "flow": flows,
                "grid": grid_diagnostics(points, start * 1_000_000, end * 1_000_000),
            }
        )
    report["windows"] = windows
    write_once(folder / "result.json", report)
    print(f"Research recorded at {folder}")
    print(f"Rows={len(points)}; complete quotes={len(valid)}; flow signals={len(signed_trades)}")
    print(f"Complete-quote spread: {summary(spreads)}")
    print("Detailed chronological flow, imbalance and phase diagnostics are in result.json.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", required=True)
    parser.add_argument("--data", default="data/round0/sample.csv")
    parser.add_argument("--end-seconds", type=int, default=3600)
    args = parser.parse_args()
    from tools.common import inside

    analyze(
        inside(args.data),
        inside(f"research/round0/{identifier(args.id)}"),
        args.end_seconds,
    )


if __name__ == "__main__":
    main()
