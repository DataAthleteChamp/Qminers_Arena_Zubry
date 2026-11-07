"""Freeze exact evaluated strategy bytes for manual upload; never submit."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tools.common import identifier, inside, now, read_json, sha256, source_digest, write_once
from tools.preflight import inspect_source


def freeze(experiment_id: str) -> Path:
    folder = inside(f"research/experiments/{identifier(experiment_id)}")
    plan = read_json(folder / "plan.json")
    outcome = read_json(folder / "outcome.json")
    if outcome.get("status") != "success":
        raise ValueError("Only a successful evaluated experiment can be frozen.")
    if outcome.get("result_sha256") != sha256(folder / "result.json"):
        raise ValueError("Result bytes changed.")
    if plan.get("simulator_sha256") != source_digest():
        raise ValueError("Simulator changed since evaluation.")
    source = folder / "strategy.py"
    expected = plan.get("strategy_sha256")
    if not isinstance(expected, str) or sha256(source) != expected:
        raise ValueError("Evaluated strategy snapshot changed.")
    issues = inspect_source(source)
    if issues:
        raise ValueError("; ".join(issues))
    round_id = plan.get("round")
    if not isinstance(round_id, str):
        raise ValueError("Missing round ID.")
    destination = inside(f"submissions/{identifier(round_id)}/{expected[:12]}")
    destination.mkdir(parents=True, exist_ok=False)
    with (destination / "strategy.py").open("xb") as handle:
        handle.write(source.read_bytes())
    if sha256(destination / "strategy.py") != expected:
        raise ValueError("Frozen bytes differ from the evaluated snapshot.")
    write_once(
        destination / "receipt.json",
        {
            "experiment_id": experiment_id,
            "strategy_sha256": expected,
            "data_sha256": plan.get("data_sha256"),
            "source_kind": plan.get("source_kind"),
            "frozen_utc": now(),
            "official_submission_id": None,
            "server_sandbox_status": "not submitted/tested",
            "final_flag_confirmed": False,
            "warning": "Local only; human review, server validation and Final selection required.",
        },
    )
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("experiment")
    args = parser.parse_args()
    try:
        result = freeze(args.experiment)
    except (OSError, ValueError) as error:
        print(f"Freeze error: {error}", file=sys.stderr)
        return 2
    print(f"Frozen exact evaluated bytes for manual review/upload: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
