"""Summarise matrix_<label>.csv per strategy. Usage: summarize.py matrix_m1.csv"""

import sys

import pandas as pd

pd.set_option("display.width", 220)
m = pd.read_csv(sys.argv[1])
if "error" in m and m.error.notna().any():
    print(m[m.error.notna()][["tape", "name", "error"]].to_string())
m = m[m.error.isna()] if "error" in m else m
syn = m[m.tape.str.startswith("syn_")]
orig = syn[~syn.tape.str.endswith("m")]
mirr = syn[syn.tape.str.endswith("m")]
rows = []
for name, g in syn.groupby("name"):
    r2 = m[(m.name == name) & (m.tape == "round2_public")].pnl
    r2m = m[(m.name == name) & (m.tape == "r2_mirror")].pnl
    rows.append({
        "name": name,
        "syn_mean": g.pnl.mean(),
        "syn_median": g.pnl.median(),
        "syn_min": g.pnl.min(),
        "syn_pos": f"{(g.pnl > 0).sum()}/{len(g)}",
        "syn_up_mean": orig[orig.name == name].pnl.mean(),
        "syn_down_mean": mirr[mirr.name == name].pnl.mean(),
        "syn_mdd_mean": g.max_dd.mean(),
        "R2": r2.iloc[0] if len(r2) else float("nan"),
        "R2_mirror": r2m.iloc[0] if len(r2m) else float("nan"),
        "penalty_total": m[m.name == name].penalty.sum(),
    })
out = pd.DataFrame(rows).sort_values("syn_median", ascending=False)
print(out.round(0).to_string(index=False))
