"""Run s1 variants (constant overrides) in the official simulator, in parallel.

Writes variants/<name>.py, runs/<tape>/<name>/ and results_<tape>.csv in this folder.
Halves are read from the full run's 1 s pnl.csv (state preserved, no tape slicing).
Usage: run_variants.py <tape.csv> <tape_label> [variant ...]
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASE = ROOT / "strategies" / "s1.py"
V2 = ROOT / "strategies" / "zubry_v2.py"

VARIANTS: dict[str, dict[str, str] | None] = {
    "zubry_v2": None,
    "s1": {},
    "s1_no_vol": {"VOL_MAX": "0.0"},
    "s1_no_pull": {"BIG_TAKER": "0"},
    "s1_no_spread": {"REQUIRE_SPREAD": "0"},
    "s1_only_spread": {"VOL_MAX": "0.0", "BIG_TAKER": "0"},
    "s1_flatten": {"FLATTEN_IN_STRESS": "True"},
    "s1_no_reduce": {"KEEP_REDUCING_QUOTE": "False"},
    "s1_cool10": {"COOLDOWN_S": "10.0"},
    "s1_cool05": {"COOLDOWN_S": "0.5"},
    "s1_big100": {"BIG_TAKER": "100"},
    "s1_big500": {"BIG_TAKER": "500"},
    "s1_vol2": {"VOL_MAX": "2.0"},
    "s1_vol5": {"VOL_MAX": "5.0"},
    # batch 2: combinations around the no-pull result
    "s1_vol_only": {"REQUIRE_SPREAD": "0", "BIG_TAKER": "0"},
    "s1_np_vol2": {"BIG_TAKER": "0", "VOL_MAX": "2.0"},
    "s1_np_vol5": {"BIG_TAKER": "0", "VOL_MAX": "5.0"},
    "s1_np_noreduce": {"BIG_TAKER": "0", "KEEP_REDUCING_QUOTE": "False"},
    "s1_big1000": {"BIG_TAKER": "1000"},
    "s1_big500_cool05": {"BIG_TAKER": "500", "COOLDOWN_S": "0.5"},
    "s1_np_win30": {"BIG_TAKER": "0", "VOL_WINDOW_S": "30"},
    "s1_np_win120": {"BIG_TAKER": "0", "VOL_WINDOW_S": "120"},
    # batch 3: queue pre-positioning (s1 defaults now have BIG_TAKER=0)
    "s1_off1_keep0": {"QUOTE_OFFSET": "1"},
    "s1_off1_keep1": {"QUOTE_OFFSET": "1", "KEEP_BEHIND": "1"},
    "s1_off1_keep2": {"QUOTE_OFFSET": "1", "KEEP_BEHIND": "2"},
    "s1_off0_keep1": {"KEEP_BEHIND": "1"},
    "s1_off2_keep1": {"QUOTE_OFFSET": "2", "KEEP_BEHIND": "1"},
}


def make(name: str) -> Path:
    over = VARIANTS[name]
    if over is None:
        return V2
    src = BASE.read_text()
    for k, v in over.items():
        src, n = re.subn(rf"^{k} = [^#\n]+", f"{k} = {v}  ", src, flags=re.M)
        if n != 1:
            raise SystemExit(f"constant {k} not found exactly once")
    out = HERE / "variants" / f"{name}.py"
    out.parent.mkdir(exist_ok=True)
    out.write_text(src)
    return out


def run(name: str, tape: Path, label: str) -> dict:
    strat = make(name)
    log_dir = HERE / "runs" / label / name
    cmd = ["uv", "run", "--locked", "python", "-m", "simulator.main", "--backtest", str(tape),
           "--strategy", str(strat), "--log-dir", str(log_dir), "--no-logs"]
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    (HERE / "runs" / label).mkdir(parents=True, exist_ok=True)
    (HERE / "runs" / label / f"{name}.log").write_text(p.stdout + p.stderr)
    if p.returncode != 0:
        return {"name": name, "error": p.stderr[-400:]}
    r = json.loads((log_dir / "result.json").read_text())
    rows = list(csv.DictReader((log_dir / "pnl.csv").open()))
    end_s = float(rows[-1]["elapsed_s"])
    pnl_mid = [float(x["pnl"]) for x in rows if float(x["elapsed_s"]) <= end_s / 2][-1]
    peak, mdd = -1e18, 0.0
    for x in rows:
        v = float(x["pnl"])
        peak = max(peak, v)
        mdd = max(mdd, peak - v)
    return {"name": name, "pnl": r["pnl"], "h1": pnl_mid, "h2": r["pnl"] - pnl_mid, "fills": r["fills"],
            "volume": r["traded_volume"], "penalty": r["breach_penalty"],
            "pnl_se": round(r["pnl_se"] or 0, 1), "max_dd": mdd, "inv_q997": r["abs_inventory_q997"],
            "sha256": hashlib.sha256(strat.read_bytes()).hexdigest()[:12]}


def main() -> None:
    tape, label = Path(sys.argv[1]), sys.argv[2]
    names = sys.argv[3:] or list(VARIANTS)
    with ThreadPoolExecutor(max_workers=9) as ex:
        res = list(ex.map(lambda n: run(n, tape, label), names))
    keys = ["name", "pnl", "h1", "h2", "fills", "volume", "penalty", "pnl_se", "max_dd", "inv_q997",
            "sha256", "error"]
    with (HERE / f"results_{label}.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(res)
    for r in res:
        if "error" in r:
            print(f"{r['name']:16s} ERROR {r['error']}")
            continue
        print(f"{r['name']:16s} pnl={r['pnl']:9.0f} h1={r['h1']:9.0f} h2={r['h2']:9.0f} "
              f"fills={r['fills']:6d} pen={r['penalty']:.0f} se={r['pnl_se']:7.1f} "
              f"mdd={r['max_dd']:7.0f} invq997={r['inv_q997']} {r['sha256']}")


if __name__ == "__main__":
    main()
