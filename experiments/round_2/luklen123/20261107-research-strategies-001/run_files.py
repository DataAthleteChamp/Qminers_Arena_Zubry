"""Run strategy files in the official simulator in parallel; halves come from the 1 s pnl.csv.

Usage: run_files.py <tape.csv> <label> <strategy.py> [...]
Writes runs/<label>/<name>/ and results_<label>.csv next to this script.
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def run(strat: Path, tape: Path, label: str) -> dict:
    name = strat.stem
    log_dir = HERE / "runs" / label / name
    cmd = ["uv", "run", "--locked", "python", "-m", "simulator.main", "--backtest", str(tape),
           "--strategy", str(strat), "--log-dir", str(log_dir), "--no-logs"]
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    (HERE / "runs" / label).mkdir(parents=True, exist_ok=True)
    (HERE / "runs" / label / f"{name}.log").write_text(p.stdout + p.stderr)
    if p.returncode != 0:
        return {"name": name, "error": p.stderr.strip().splitlines()[-1][:300]}
    r = json.loads((log_dir / "result.json").read_text())
    rows = list(csv.DictReader((log_dir / "pnl.csv").open()))
    end_s = float(rows[-1]["elapsed_s"])
    h1 = [float(x["pnl"]) for x in rows if float(x["elapsed_s"]) <= end_s / 2][-1]
    peak, mdd = -1e18, 0.0
    for x in rows:
        v = float(x["pnl"])
        peak = max(peak, v)
        mdd = max(mdd, peak - v)
    return {"name": name, "pnl": r["pnl"], "h1": h1, "h2": r["pnl"] - h1, "fills": r["fills"],
            "volume": r["traded_volume"], "penalty": r["breach_penalty"],
            "pnl_se": round(r["pnl_se"] or 0, 1), "max_dd": mdd, "inv_q997": r["abs_inventory_q997"],
            "sha256": hashlib.sha256(strat.read_bytes()).hexdigest()[:12]}


def main() -> None:
    tape, label = Path(sys.argv[1]), sys.argv[2]
    files = [Path(f).resolve() for f in sys.argv[3:]]
    with ThreadPoolExecutor(max_workers=9) as ex:
        res = list(ex.map(lambda f: run(f, tape, label), files))
    keys = ["name", "pnl", "h1", "h2", "fills", "volume", "penalty", "pnl_se", "max_dd", "inv_q997",
            "sha256", "error"]
    with (HERE / f"results_{label}.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(res)
    for r in res:
        if "error" in r:
            print(f"{r['name']:10s} ERROR {r['error']}")
            continue
        print(f"{r['name']:10s} pnl={r['pnl']:9.0f} h1={r['h1']:9.0f} h2={r['h2']:9.0f} "
              f"fills={r['fills']:6d} pen={r['penalty']:.0f} se={r['pnl_se']:7.1f} "
              f"mdd={r['max_dd']:7.0f} invq997={r['inv_q997']} {r['sha256']}")


if __name__ == "__main__":
    main()
