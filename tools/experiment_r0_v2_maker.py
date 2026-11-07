"""Frozen prefix selection, warm-start chronological checks, and one new .py artifact."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from tools.common import (
    ROOT,
    identifier,
    inside,
    now,
    read_json,
    sha256,
    source_digest,
    write_once,
)
from tools.compare import numeric
from tools.run_experiment import run

DATA = "data/round0/sample_v2.csv"
PROTOTYPE = "strategies/r0_v2_maker.py"
FIT_END = 1200
OWNER = "sol-dbea"
FIT_WEIGHTS = {"fit-mid": 0.0, "fit-half": 0.5, "fit-full": 1.0}


def text(record: dict[str, object], name: str) -> str:
    value = record.get(name)
    if not isinstance(value, str):
        raise ValueError(f"Missing text field: {name}")
    return value


def study_path(study: str) -> Path:
    identifier(study)
    if len(study) > 40:
        raise ValueError("Study ID must be at most 40 characters.")
    return inside(f"research/round0/{study}")


def generated_source(source: str, weight: float, activation: int) -> str:
    for old, new in (
        ("IMBALANCE_WEIGHT = 0.0\n", f"IMBALANCE_WEIGHT = {weight!r}\n"),
        ("ACTIVATE_AT_US = 0\n", f"ACTIVATE_AT_US = {activation}\n"),
    ):
        if source.count(old) != 1:
            raise ValueError(f"Prototype marker is not unique: {old.strip()}")
        source = source.replace(old, new, 1)
    return source


def prepare(study: str) -> None:
    folder = study_path(study)
    if folder.exists():
        raise FileExistsError("Study already exists; choose a new immutable ID.")
    data, prototype = inside(DATA), inside(PROTOTYPE)
    data_hash = sha256(data)
    staging = inside(f"logs/{study}")
    staging.mkdir(parents=True, exist_ok=False)
    prefix = staging / "fit-prefix.csv"
    rows = 0
    last_time = 0.0
    with data.open(newline="") as source, prefix.open("x", newline="") as destination:
        destination.write(next(source))
        for line in source:
            timestamp = float(line.partition(",")[0])
            if timestamp >= FIT_END:
                break
            if timestamp < last_time:
                raise ValueError("Non-chronological tape")
            destination.write(line)
            rows += 1
            last_time = timestamp
    if not rows or sha256(data) != data_hash:
        raise ValueError("Empty prefix or changed raw data")
    write_once(
        folder / "plan.json",
        {
            "created_utc": now(),
            "data": DATA,
            "data_sha256": data_hash,
            "simulator_sha256": source_digest(),
            "prototype_sha256": sha256(prototype),
            "script_sha256": sha256(Path(__file__)),
            "fit_prefix": str(prefix.relative_to(ROOT)),
            "fit_prefix_sha256": sha256(prefix),
            "fit_prefix_rows": rows,
            "fit_window_seconds": [0, FIT_END],
            "fit_last_event_seconds": last_time,
            "validation_window_seconds": [FIT_END, "EOF"],
            "weights": FIT_WEIGHTS,
            "baseline": "same market maker, imbalance weight zero",
            "hypothesis": "Depth weighting improves executed net PnL over midpoint quoting.",
            "selection": "Highest prefix official PnL; no suffix PnL used for selection.",
            "validation": "Replay from first row; place no orders before 1200s; start flat.",
            "reject_if": [
                "Any inventory penalty, failed preflight, or changed inputs.",
                "No positive validation PnL.",
                "Depth weighting lacks a positive paired 60-second block-bootstrap lower bound.",
            ],
            "limitations": [
                "Whole-file descriptive diagnostics were already inspected: this is a "
                "chronological check, not a newly untouched holdout.",
                "Same public/private generator is a working assumption, not organizer-confirmed.",
                "A block bootstrap describes this observed tape, not probability of winning.",
                "Raw tick prices do not identify a named real-world asset.",
            ],
            "baseline_evidence": {
                "v1_original_and_fixed_pnl": 1878,
                "v2_original_pnl": -531,
                "v2_fixed_pnl": -14125,
                "v2_original_fills": 618,
                "v2_fixed_fills": 16594,
                "interpretation": "Fixing the IOC callback lets the losing policy keep trading.",
            },
            "sources": [
                "Official README: latency, FIFO, inventory limits and liquidation markout.",
                "Cartea/Donnelly/Jaimungal 2018: Sections 1-2; adverse-selection-aware quoting.",
                "Gould/Bonart 2015: Sections 5.1-5.2; horizon and partition limitations.",
            ],
        },
    )
    for source_path, name in ((prototype, "prototype.py"), (Path(__file__), "experiment.py")):
        with (folder / name).open("xb") as destination:
            destination.write(source_path.read_bytes())
    print(f"Prepared {rows} prefix events; raw data unchanged; study={folder}")


def trial_result(study: str, trial: str) -> dict[str, object]:
    folder = inside(f"research/experiments/{study}-{trial}")
    outcome = read_json(folder / "outcome.json")
    if outcome.get("status") != "success":
        raise ValueError(f"Trial did not succeed: {trial}")
    result_path = folder / "result.json"
    if outcome.get("result_sha256") != sha256(result_path):
        raise ValueError("Frozen result changed")
    return read_json(result_path)


def run_trial(study: str, trial: str) -> None:
    folder = study_path(study)
    plan = read_json(folder / "plan.json")
    if sha256(inside(DATA)) != text(plan, "data_sha256"):
        raise ValueError("Raw data changed since preparation")
    if source_digest() != text(plan, "simulator_sha256"):
        raise ValueError("Official engine changed")
    if trial in FIT_WEIGHTS:
        weight, activation, data = FIT_WEIGHTS[trial], 0, text(plan, "fit_prefix")
    elif trial in ("check-baseline", "check-selected"):
        selection = read_json(folder / "selection.json")
        weight = 0.0 if trial == "check-baseline" else numeric(selection, "weight")
        activation, data = FIT_END * 1_000_000, DATA
    elif trial == "release":
        release = read_json(folder / "release.json")
        strategy = text(release, "file")
        weight, activation, data = numeric(release, "weight"), 0, DATA
    else:
        raise ValueError(f"Unknown trial: {trial}")
    if trial != "release":
        source = generated_source((folder / "prototype.py").read_text(), weight, activation)
        strategy = f"logs/{study}/{trial}.py"
        with inside(strategy).open("x") as destination:
            destination.write(source)
    code, recorded = run(
        f"{study}-{trial}",
        OWNER,
        strategy,
        data,
        "playground",
        f"Frozen weight={weight}; activation={activation}us; prefix-selected maker.",
        "Failure, penalty, changed hashes or nonpositive chronological net PnL.",
    )
    if code:
        raise RuntimeError(f"Recorded failed trial at {recorded}; exit={code}")
    result = trial_result(study, trial)
    print(
        f"{trial}: pnl={numeric(result, 'pnl'):.2f}, "
        f"fills={numeric(result, 'fills'):.0f}, "
        f"penalty={numeric(result, 'breach_penalty'):.2f}"
    )


def select(study: str) -> None:
    results = {name: trial_result(study, name) for name in FIT_WEIGHTS}
    if any(numeric(value, "breach_penalty") != 0 for value in results.values()):
        raise ValueError("Training produced an inventory penalty")
    winner = max(results, key=lambda name: numeric(results[name], "pnl"))
    write_once(
        study_path(study) / "selection.json",
        {"weight": FIT_WEIGHTS[winner], "trial": winner, "fit_results": results},
    )
    print(f"Prefix-selected {winner}; weight={FIT_WEIGHTS[winner]}")


def curve(study: str, trial: str) -> NDArray[np.float64]:
    path = inside(f"logs/{study}-{trial}/pnl.csv")
    with path.open(newline="") as source:
        reader = csv.DictReader(source)
        rows = [(float(row["elapsed_s"]), float(row["pnl"])) for row in reader]
    return np.asarray(rows, dtype=np.float64)


def paired_interval(delta: NDArray[np.float64], block: int) -> list[float]:
    increments = np.diff(delta)
    if not len(increments):
        raise ValueError("No validation increments")
    rng = np.random.default_rng(20261107)
    totals = np.empty(2000)
    offsets = np.arange(block)
    for index in range(len(totals)):
        starts = rng.integers(0, len(increments), size=(len(increments) + block - 1) // block)
        positions = ((starts[:, None] + offsets) % len(increments)).ravel()[: len(increments)]
        totals[index] = increments[positions].sum()
    return [float(value) for value in np.quantile(totals, [0.025, 0.975])]


def evaluate(study: str) -> None:
    folder = study_path(study)
    selected_weight = numeric(read_json(folder / "selection.json"), "weight")
    selected_trial = "check-selected" if selected_weight else "check-baseline"
    baseline = trial_result(study, "check-baseline")
    selected = trial_result(study, selected_trial)
    left, right = curve(study, "check-baseline"), curve(study, selected_trial)
    if left.shape != right.shape or not np.array_equal(left[:, 0], right[:, 0]):
        raise ValueError("Paired PnL clocks differ")
    if numeric(baseline, "breach_penalty") or numeric(selected, "breach_penalty"):
        raise ValueError("Validation penalty")
    mask = left[:, 0] >= FIT_END - 1
    delta = right[mask, 1] - left[mask, 1]
    intervals = {str(block): paired_interval(delta, block) for block in (30, 60, 120)}
    accept_overlay = (
        selected_weight != 0
        and numeric(selected, "pnl") > numeric(baseline, "pnl")
        and intervals["60"][0] > 0
    )
    released_weight = selected_weight if accept_overlay else 0.0
    released_result = selected if accept_overlay else baseline
    if numeric(released_result, "pnl") <= 0:
        raise ValueError("No profitable validated candidate; do not freeze a losing policy.")
    write_once(
        folder / "validation.json",
        {
            "baseline": baseline,
            "selected": selected,
            "paired_pnl_delta": numeric(selected, "pnl") - numeric(baseline, "pnl"),
            "paired_block_bootstrap_95pct": intervals,
            "bootstrap_seed": 20261107,
            "bootstrap_replicates": 2000,
            "bootstrap_sampling": "1s PnL increments, including the final partial interval.",
            "accept_imbalance_overlay": accept_overlay,
            "release_weight": released_weight,
            "scope": "Chronological observed-tape validation, not private PnL or P(win).",
        },
    )
    print(f"Validation delta={delta[-1]:.2f}; 60s interval={intervals['60']}")
    print(f"Release weight={released_weight}; validated PnL={numeric(released_result, 'pnl')}")


def freeze(study: str) -> None:
    folder = study_path(study)
    weight = numeric(read_json(folder / "validation.json"), "release_weight")
    target = inside("submissions/r0/r0_v2_dbea.py")
    target.parent.mkdir(parents=True, exist_ok=True)
    source = generated_source((folder / "prototype.py").read_text(), weight, 0)
    with target.open("x") as destination:
        destination.write(source)
    write_once(
        folder / "release.json",
        {
            "file": str(target.relative_to(ROOT)),
            "sha256": sha256(target),
            "bytes": target.stat().st_size,
            "weight": weight,
            "activation_us": 0,
            "uploaded": False,
            "note": "Exact full-tape release run is required; fit period is in sample.",
        },
    )
    print(f"New standalone candidate: {target}; sha256={sha256(target)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study", required=True)
    parser.add_argument(
        "action",
        choices=[
            "prepare",
            "fit-mid",
            "fit-half",
            "fit-full",
            "select",
            "check-baseline",
            "check-selected",
            "evaluate",
            "freeze",
            "release",
        ],
    )
    args = parser.parse_args()
    try:
        actions = {"prepare": prepare, "select": select, "evaluate": evaluate, "freeze": freeze}
        if args.action in actions:
            actions[args.action](args.study)
        else:
            run_trial(args.study, args.action)
    except (OSError, ValueError, RuntimeError) as error:
        print(f"V2 experiment failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
