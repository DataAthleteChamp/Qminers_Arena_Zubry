"""Robust hyperparameter search for the kuba/s_67 engine by successive halving over many tapes.

Stage 1: N random configs + s_67 baseline on 4 synthetic tapes; score = mean(delta) - 0.5*std(delta)
         against the baseline on the same tapes; keep the top K1.
Stage 2: top K1 on 8 more synthetic tapes + R2 public + R2 mirror; keep configs with R2 and
         R2-mirror delta >= 0, rank by wins then mean delta; keep top K2.
Stage 3: top K2 + baseline on R1.
Everything runs in the official simulator. Usage: uv run --locked python optimize.py [N] [seed]
"""

from __future__ import annotations

import csv
import json
import random
import statistics
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE.parent / "20261107-kuba-extensions-001"))
import generate_kuba as gk  # noqa: E402

TAPES = HERE.parent / "20261107-deep-move-strategies-001" / "tapes"
DATA = Path("/Users/lukaszlenart/Qminers_Arena_Zubry/data")
STAGE1 = [TAPES / f"{t}.csv" for t in ("syn_1", "syn_2m", "syn_4", "syn_6m")]
STAGE2 = [TAPES / f"{t}.csv" for t in ("syn_1m", "syn_2", "syn_3", "syn_3m", "syn_4m", "syn_5",
                                        "syn_5m", "syn_6")]
STAGE2 += [DATA / "round2" / "round2_public.csv", TAPES / "r2_mirror.csv"]
STAGE3 = [DATA / "round1" / "round1.csv"]
K1, K2 = 10, 3

BASELINE = {"QUOTE_SIZE": "40"}  # s_67


def sample(rng: random.Random) -> dict[str, str]:
    ema = rng.choice((0.5, 0.75, 1.0, 1.5, 2.0))
    e = tuple(max(1, round(x * ema)) for x in (3, 30, 120))
    mpl = rng.choice((2, 3))
    return {
        "QUOTE_SIZE": str(rng.choice((32, 36, 40, 44, 48))),
        "INVENTORY_SKEW": f"{10 ** rng.uniform(-2.3, -1.7):.4f}",
        "EMA_SECONDS": f"({e[0]}, {e[1]}, {e[2]})",
        "GAP_QTY": str(rng.choice((60, 100, 150))),
        "FRAGILE_SIZE": str(rng.choice((8, 12, 20))),
        "TOPUP_MIN": str(rng.choice((4, 8, 16))),
        "MAX_PER_LEVEL": str(mpl),
        "SLOT_MULT": str(mpl),
        "SHOCK_SPREAD": str(rng.choice((3, 4))),
        "RECOVERY_US": str(rng.choice((100_000, 200_000, 500_000))),
        "MIN_L1": str(rng.choice((50, 100, 150))),
        "CAUTION_DIV": str(rng.choice((1, 2))),
    }


def run(cfg: str, tape: Path) -> float:
    strat = HERE / "cfgs" / f"{cfg}.py"
    log = HERE / "runs" / tape.stem / cfg
    res = log / "result.json"
    if not res.exists():
        p = subprocess.run(["uv", "run", "--locked", "python", "-m", "simulator.main", "--backtest",
                            str(tape), "--strategy", str(strat), "--log-dir", str(log), "--no-logs"],
                           cwd=ROOT, capture_output=True, text=True)
        if p.returncode != 0:
            raise RuntimeError(f"{cfg} on {tape.stem}: {p.stderr[-300:]}")
    r = json.loads(res.read_text())
    if r["breach_penalty"]:
        return float("-inf")
    return float(r["pnl"])


def evaluate(cfgs: list[str], tapes: list[Path]) -> dict[tuple[str, str], float]:
    jobs = [(c, t) for t in sorted(tapes, key=lambda p: -p.stat().st_size) for c in cfgs]
    with ThreadPoolExecutor(max_workers=9) as ex:
        vals = list(ex.map(lambda j: run(*j), jobs))
    return {(c, t.stem): v for (c, t), v in zip(jobs, vals, strict=True)}


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    rng = random.Random(int(sys.argv[2]) if len(sys.argv) > 2 else 7)
    (HERE / "cfgs").mkdir(exist_ok=True)
    configs = {"base_s67": BASELINE}
    for i in range(n):
        configs[f"cfg_{i:03d}"] = {**sample(rng)}
    for name, over in configs.items():
        (HERE / "cfgs" / f"{name}.py").write_text(gk.render(f"HPO config {name}.", over))
    (HERE / "configs.json").write_text(json.dumps(configs, indent=1))

    def deltas(res, cfg, tapes):
        return [res[(cfg, t.stem)] - res[("base_s67", t.stem)] for t in tapes]

    r1 = evaluate(list(configs), STAGE1)
    s1 = {c: statistics.mean(deltas(r1, c, STAGE1)) - 0.5 * statistics.pstdev(deltas(r1, c, STAGE1))
          for c in configs if c != "base_s67"}
    top1 = sorted(s1, key=s1.get, reverse=True)[:K1]
    print("stage1 top:", [(c, round(s1[c])) for c in top1], flush=True)

    r2 = evaluate(["base_s67", *top1], STAGE2)
    allt = STAGE1 + STAGE2
    res = {**r1, **r2}
    rows = []
    for c in top1:
        d = deltas(res, c, allt)
        rows.append({"cfg": c, "wins": sum(x > 0 for x in d), "mean_delta": statistics.mean(d),
                     "min_pnl": min(res[(c, t.stem)] for t in allt),
                     "R2_d": res[(c, "round2_public")] - res[("base_s67", "round2_public")],
                     "R2m_d": res[(c, "r2_mirror")] - res[("base_s67", "r2_mirror")]})
    rows.sort(key=lambda r: (r["R2_d"] >= 0 and r["R2m_d"] >= 0, r["wins"], r["mean_delta"]),
              reverse=True)
    for r in rows:
        print("stage2", {k: (round(v) if isinstance(v, float) else v) for k, v in r.items()}, flush=True)
    top2 = [r["cfg"] for r in rows if r["R2_d"] >= 0 and r["R2m_d"] >= 0][:K2] or [rows[0]["cfg"]]

    r3 = evaluate(["base_s67", *top2], STAGE3)
    res.update(r3)
    base_min = min(res[("base_s67", t.stem)] for t in allt + STAGE3)
    print(f"baseline s_67 min over 15 tapes: {base_min:.0f}", flush=True)
    for c in top2:
        d = deltas(res, c, allt + STAGE3)
        mn = min(res[(c, t.stem)] for t in allt + STAGE3)
        print(f"FINAL {c} wins={sum(x > 0 for x in d)}/15 mean_delta={statistics.mean(d):.0f} "
              f"min={mn:.0f} R1_d={d[-1]:.0f} accept={sum(x > 0 for x in d) >= 12 and mn >= 0.98 * base_min}"
              f" params={configs[c]}", flush=True)
    with (HERE / "results.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["cfg", "tape", "pnl"])
        for (c, t), v in sorted(res.items()):
            w.writerow([c, t, v])


if __name__ == "__main__":
    main()
