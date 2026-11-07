"""Record a real official-simulator run, including failures; never upload."""

from __future__ import annotations

import argparse
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

from tools.common import ROOT, identifier, inside, now, read_json, sha256, source_digest, write_once
from tools.preflight import inspect_source


def run(
    experiment_id: str,
    owner: str,
    strategy: str,
    backtest: str,
    round_id: str,
    hypothesis: str,
    rejection: str,
    full_logs: bool = False,
    timeout: float = 900,
) -> tuple[int, Path]:
    identifier(experiment_id)
    identifier(owner)
    identifier(round_id)
    if not hypothesis.strip() or not rejection.strip() or not 0 < timeout <= 900:
        raise ValueError("A hypothesis/rejection criterion and timeout in (0, 900] are required.")
    strategy_path, data_path = inside(strategy), inside(backtest)
    if data_path.suffix != ".csv":
        raise ValueError("Official runner expects plain CSV, not compressed data.")
    folder = inside(f"research/experiments/{experiment_id}")
    log_dir = inside(f"logs/{experiment_id}")
    if folder.exists() or log_dir.exists():
        raise FileExistsError(
            "Experiment/log ID already exists. Do not overwrite research history."
        )
    before = {
        "strategy_sha256": sha256(strategy_path),
        "data_sha256": sha256(data_path),
        "simulator_sha256": source_digest(),
    }
    command = [
        "uv",
        "run",
        "--locked",
        "exchange-simulator",
        "--strategy",
        str(strategy_path),
        "--backtest",
        str(data_path),
        "--log-dir",
        str(log_dir),
        "--public-depth",
        "20",
    ]
    if not full_logs:
        command.append("--no-logs")
    revision = subprocess.run(
        ["git", "--no-pager", "-C", str(ROOT), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    dirty = bool(
        subprocess.run(
            ["git", "--no-pager", "-C", str(ROOT), "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    )
    record: dict[str, object] = {
        "schema_version": 1,
        "id": experiment_id,
        "owner": owner,
        "round": round_id,
        "started_utc": now(),
        "hypothesis": hypothesis,
        "reject_if": rejection,
        "strategy": str(strategy_path.relative_to(ROOT)),
        "backtest": str(data_path.relative_to(ROOT)),
        "log_dir": str(log_dir.relative_to(ROOT)),
        "source_kind": "synthetic-playground" if round_id == "playground" else "declared-public",
        "git_before_run": revision,
        "git_dirty_before_run": dirty,
        "python": platform.python_version(),
        "command": [
            "uv",
            "run",
            "--locked",
            "exchange-simulator",
            "--strategy",
            str(strategy_path.relative_to(ROOT)),
            "--backtest",
            str(data_path.relative_to(ROOT)),
            "--log-dir",
            str(log_dir.relative_to(ROOT)),
            "--public-depth",
            "20",
            *([] if full_logs else ["--no-logs"]),
        ],
        **before,
        "status": "planned",
        "limitations": [
            "Public tape PnL is not private-round PnL or final z-score.",
            "The caller declares round/data provenance; filenames do not identify the instrument.",
            "Local preflight is not the server's complete static validator.",
            "Timeout/thread settings are not an OS sandbox or memory certification.",
        ],
    }
    write_once(folder / "plan.json", record)
    with (folder / "strategy.py").open("xb") as handle:
        handle.write(strategy_path.read_bytes())
    issues = inspect_source(strategy_path)
    if issues:
        write_once(folder / "outcome.json", {"status": "failed-preflight", "errors": issues})
        return 1, folder
    environment = dict(
        os.environ,
        OMP_NUM_THREADS="1",
        OPENBLAS_NUM_THREADS="1",
        MKL_NUM_THREADS="1",
        NUMEXPR_MAX_THREADS="1",
    )
    start = time.perf_counter()
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=environment,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        write_once(
            folder / "outcome.json",
            {"status": "failed-timeout", "timeout_seconds": timeout, "error": str(error)},
        )
        return 2, folder
    elapsed = time.perf_counter() - start
    unchanged = before == {
        "strategy_sha256": sha256(strategy_path),
        "data_sha256": sha256(data_path),
        "simulator_sha256": source_digest(),
    }
    if result.returncode or not unchanged:
        write_once(
            folder / "outcome.json",
            {
                "status": "failed",
                "returncode": result.returncode,
                "inputs_unchanged": unchanged,
                "stdout": result.stdout[-16000:],
                "stderr": result.stderr[-16000:],
                "elapsed_seconds": elapsed,
            },
        )
        return 2, folder
    actual = read_json(log_dir / "result.json")
    write_once(folder / "result.json", actual)
    write_once(
        folder / "outcome.json",
        {
            "status": "success",
            "finished_utc": now(),
            "elapsed_seconds": elapsed,
            "result_sha256": sha256(folder / "result.json"),
            "stdout": result.stdout,
            "stderr": result.stderr[-16000:],
            "decision": "human review; not automatically final",
        },
    )
    return 0, folder


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("id", "owner", "strategy", "backtest", "round", "hypothesis", "reject-if"):
        parser.add_argument(f"--{name}", required=True)
    parser.add_argument("--full-logs", action="store_true")
    parser.add_argument("--timeout", type=float, default=900)
    args = parser.parse_args()
    try:
        code, folder = run(
            args.id,
            args.owner,
            args.strategy,
            args.backtest,
            args.round,
            args.hypothesis,
            args.reject_if,
            args.full_logs,
            args.timeout,
        )
    except (OSError, ValueError) as error:
        print(f"Experiment error: {error}", file=sys.stderr)
        return 2
    print(f"Recorded experiment: {folder}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
