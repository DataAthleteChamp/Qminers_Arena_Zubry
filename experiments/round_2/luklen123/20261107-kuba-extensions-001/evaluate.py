"""Compare kuba variants with kuba.py tape by tape and apply the acceptance rule.

Accept when: wins >= 12/15 tapes, variant worst tape >= 0.98 * kuba worst tape, mean delta > 0.
Usage: evaluate.py <baseline_matrix.csv> <variants_matrix.csv> [<more.csv> ...]
"""

import sys

import pandas as pd

pd.set_option("display.width", 220)
base = pd.read_csv(sys.argv[1])
base = base[base.name == "kuba"].set_index("tape").pnl
var = pd.concat([pd.read_csv(p) for p in sys.argv[2:]])
var = var[var.error.isna()] if "error" in var else var
rows = []
for name, g in var.groupby("name"):
    s = g.set_index("tape").pnl.reindex(base.index)
    if s.isna().any():
        continue
    d = s - base
    rows.append({
        "name": name,
        "wins": int((d > 0).sum()),
        "mean_delta": d.mean(),
        "worst_delta": d.min(),
        "min_pnl": s.min(),
        "R1_d": d.get("round1"),
        "R2_d": d.get("round2_public"),
        "R2m_d": d.get("r2_mirror"),
        "penalty": g.penalty.sum(),
        "accept": (d > 0).sum() >= 12 and s.min() >= 0.98 * base.min() and d.mean() > 0,
    })
out = pd.DataFrame(rows).sort_values(["accept", "mean_delta"], ascending=False)
print(f"kuba baseline: min={base.min():.0f} R1={base['round1']:.0f} R2={base['round2_public']:.0f} "
      f"R2m={base['r2_mirror']:.0f}")
print(out.round(0).to_string(index=False))
