"""Compare matching public-tape runs; do not invent a private score or a delta SE."""

from __future__ import annotations

import argparse
import json
import math
import sys

from tools.common import identifier, inside, read_json, sha256


def successful(experiment_id: str) -> tuple[dict[str, object], dict[str, object]]:
    folder = inside(f"research/experiments/{identifier(experiment_id)}")
    plan, outcome = read_json(folder / "plan.json"), read_json(folder / "outcome.json")
    if outcome.get("status") != "success":
        raise ValueError(f"{experiment_id} is not a successful run.")
    result_file = folder / "result.json"
    if outcome.get("result_sha256") != sha256(result_file):
        raise ValueError(f"{experiment_id} result changed after recording.")
    return plan, read_json(result_file)


def numeric(record: dict[str, object], name: str) -> float:
    value = record.get(name)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"Missing/non-finite official result field: {name}")
    return float(value)


def compare(baseline: str, candidate: str) -> dict[str, object]:
    left_plan, left = successful(baseline)
    right_plan, right = successful(candidate)
    for key in ("data_sha256", "simulator_sha256", "round"):
        if left_plan.get(key) != right_plan.get(key):
            raise ValueError(f"Cannot compare different evidence: {key}")
    return {
        "baseline": baseline,
        "candidate": candidate,
        "scope": "same public-tape comparison, not independent validation",
        "baseline_public_pnl": numeric(left, "pnl"),
        "candidate_public_pnl": numeric(right, "pnl"),
        "public_pnl_delta": numeric(right, "pnl") - numeric(left, "pnl"),
        "baseline_penalty": numeric(left, "breach_penalty"),
        "candidate_penalty": numeric(right, "breach_penalty"),
        "baseline_fills": left.get("fills"),
        "candidate_fills": right.get("fills"),
        "baseline_inventory": left.get("inventory"),
        "candidate_inventory": right.get("inventory"),
        "single_strategy_pnl_se": {
            "baseline": left.get("pnl_se"),
            "candidate": right.get("pnl_se"),
        },
        "paired_delta_se": None,
        "private_z_score": None,
        "warnings": [
            "One tape is not independent replications or a calibrated chance of winning.",
            "Single-strategy PnL SE is not the SE of this paired difference.",
            "The private-data positive-team mean and standard deviation are not known.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline")
    parser.add_argument("candidate")
    args = parser.parse_args()
    try:
        print(json.dumps(compare(args.baseline, args.candidate), indent=2, allow_nan=False))
    except (OSError, ValueError) as error:
        print(f"Comparison error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
