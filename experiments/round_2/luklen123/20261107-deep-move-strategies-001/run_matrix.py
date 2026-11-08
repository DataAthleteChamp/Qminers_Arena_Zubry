"""Run every strategy on every tape in the official simulator (parallel) and summarise.

Usage: run_matrix.py <label> --tapes a.csv b.csv ... --strategies x.py y.py ...
Writes matrix_<label>.csv and prints per-strategy aggregates.
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def run(tape: Path, strat: Path, label: str) -> dict:
    log_dir = HERE / "runs" / label / tape.stem / strat.stem
    p = subprocess.run(
        ["uv", "run", "--locked", "python", "-m", "simulator.main", "--backtest", str(tape),
         "--strategy", str(strat), "--log-dir", str(log_dir), "--no-logs"],
        cwd=ROOT, capture_output=True, text=True)
    base = {"tape": tape.stem, "name": strat.stem}
    if p.returncode != 0:
        return {**base, "error": (p.stderr.strip().splitlines() or ["?"])[-1][:200]}
    r = json.loads((log_dir / "result.json").read_text())
    peak, mdd = -1e18, 0.0
    for row in csv.DictReader((log_dir / "pnl.csv").open()):
        v = float(row["pnl"])
        peak = max(peak, v)
        mdd = max(mdd, peak - v)
    return {**base, "pnl": r["pnl"], "fills": r["fills"], "penalty": r["breach_penalty"],
            "pnl_se": r["pnl_se"] or 0.0, "max_dd": mdd, "inv_q997": r["abs_inventory_q997"]}


def main() -> None:
    label = sys.argv[1]
    a = sys.argv.index("--tapes")
    b = sys.argv.index("--strategies")
    tapes = [Path(x).resolve() for x in sys.argv[a + 1 : b]]
    strats = [Path(x).resolve() for x in sys.argv[b + 1 :]]
    jobs = [(t, s) for t in tapes for s in strats]
    jobs.sort(key=lambda j: -j[0].stat().st_size)  # long tapes first
    with ThreadPoolExecutor(max_workers=9) as ex:
        res = list(ex.map(lambda j: run(j[0], j[1], label), jobs))
    keys = ["tape", "name", "pnl", "fills", "penalty", "pnl_se", "max_dd", "inv_q997", "error"]
    with (HERE / f"matrix_{label}.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(res)
    errs = [r for r in res if "error" in r]
    for r in errs:
        print("ERROR", r["tape"], r["name"], r["error"])
    print(f"{len(res) - len(errs)} ok, {len(errs)} errors -> matrix_{label}.csv")


if __name__ == "__main__":
    main()
