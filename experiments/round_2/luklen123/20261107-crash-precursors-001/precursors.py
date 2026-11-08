"""Do any past-only book/flow features anticipate large moves (direction or size)?

Usage: uv run --locked python precursors.py r2_sec.pkl r1_sec.pkl
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

pd.set_option("display.width", 220)
pd.set_option("display.max_columns", 40)


def features(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    d["mid"] = d["mid"].ffill()
    r1 = d.mid.diff()
    f = pd.DataFrame(index=d.index)
    f["t"] = d.t

    def roll(s, w):
        return s.rolling(w, min_periods=1).sum()

    def imb(a, b):
        return (a - b) / (a + b).replace(0, np.nan)

    f["vol30"] = r1.rolling(30).std()
    f["vol30_rel"] = f.vol30 / r1.rolling(600, min_periods=120).std()
    f["spr10"] = d.spr.rolling(10).mean()
    f["l1_total_rel"] = (d.bq1 + d.aq1).rolling(10).mean() / (d.bq1 + d.aq1).rolling(300, min_periods=60).median()
    f["dep10_total_rel"] = (d.bdep10 + d.adep10) / (d.bdep10 + d.adep10).rolling(300, min_periods=60).median()
    f["l1_imb"] = imb(d.bq1, d.aq1).rolling(10).mean()
    f["dep5_imb"] = imb(d.bdep5, d.adep5).rolling(10).mean()
    f["dep10_imb"] = imb(d.bdep10, d.adep10).rolling(10).mean()
    f["t5_imb"] = imb(d.bdep_t5, d.adep_t5).rolling(10).mean()
    for w in (10, 30):
        f[f"flow{w}"] = imb(roll(d.tk_buy, w), roll(d.tk_sell, w))
        f[f"big{w}"] = roll(d.big_buy - d.big_sell, w)
        f[f"sweep{w}"] = roll(d.sweeps_buy - d.sweeps_sell, w)
        f[f"cancel_near_imb{w}"] = imb(roll(d.can_near_b, w), roll(d.can_near_a, w))
        f[f"insert_near_imb{w}"] = imb(roll(d.ins_near_b, w), roll(d.ins_near_a, w))
        net_b = roll(d.ins_near_b - d.can_near_b, w)
        net_a = roll(d.ins_near_a - d.can_near_a, w)
        f[f"net_liq_imb{w}"] = (net_b - net_a) / (net_b.abs() + net_a.abs()).replace(0, np.nan)
        f[f"ioc_imb{w}"] = imb(roll(d.ioc_b, w), roll(d.ioc_a, w))
    f["activity_rel"] = roll(d.tk_buy + d.tk_sell, 30) / roll(d.tk_buy + d.tk_sell, 600).clip(lower=1) * 20
    for w in (10, 30, 60, 300):
        f[f"ret{w}"] = d.mid - d.mid.shift(w)
    f["dev_ma300"] = d.mid - d.mid.rolling(300).mean()
    for h in (10, 30, 60, 120):
        f[f"fwd{h}"] = d.mid.shift(-h) - d.mid
    return f


FEATS = None


def corr_table(f: pd.DataFrame, label: str, step: int = 30) -> pd.DataFrame:
    s = f.iloc[::step].dropna()
    out = {}
    for c in FEATS:
        out[c] = {
            f"{label}_dir60": s[c].corr(s.fwd60, method="spearman"),
            f"{label}_abs60": s[c].corr(s.fwd60.abs(), method="spearman"),
        }
    return pd.DataFrame(out).T


def events(f: pd.DataFrame, thr: float, sign: int, gap: int = 120) -> list[int]:
    cand = f.index[(sign * f.fwd60) >= thr].tolist()
    picked = []
    for i in cand:
        if not picked or i - picked[-1] > gap:
            picked.append(i)
    return picked


def main() -> None:
    global FEATS
    r2 = features(pd.read_pickle(sys.argv[1]))
    r1 = features(pd.read_pickle(sys.argv[2]))
    FEATS = [c for c in r2.columns if c not in ("t",) and not c.startswith("fwd")]

    print("=== Spearman corr, non-overlapping 30 s samples (n ~ 100 per R2 half, ~400 R1) ===")
    half = len(r2) // 2
    tab = pd.concat([corr_table(r2.iloc[:half], "R2a"), corr_table(r2.iloc[half:], "R2b"),
                     corr_table(r1, "R1")], axis=1).round(3)
    tab["dir_same_sign_3"] = (np.sign(tab.R2a_dir60) == np.sign(tab.R2b_dir60)) & (
        np.sign(tab.R2a_dir60) == np.sign(tab.R1_dir60))
    print(tab.to_string())
    print("approx 95% noise band: R2 half +-0.20, R1 +-0.10")

    print("\n=== Direction, overlapping 1 s samples (more power, corr inflated by overlap) ===")
    rows = {}
    for c in FEATS:
        rows[c] = {
            "R2a": r2.iloc[:half][c].corr(r2.iloc[:half].fwd30, method="spearman"),
            "R2b": r2.iloc[half:][c].corr(r2.iloc[half:].fwd30, method="spearman"),
            "R1": r1[c].corr(r1.fwd30, method="spearman"),
        }
    print(pd.DataFrame(rows).T.round(3).to_string())

    for name, f in (("R2", r2),):
        sd60 = f.fwd60.std()
        for sign, lab in ((-1, "DOWN"), (1, "UP")):
            ev = events(f, 2 * sd60, sign)
            print(f"\n=== {name} event study {lab}: fwd60 move >= 2 sd ({2 * sd60:.0f} ticks), n={len(ev)} ===")
            z = (f[FEATS] - f[FEATS].mean()) / f[FEATS].std()
            pre = pd.DataFrame({k: z.loc[max(0, i - 60):i].mean() for k, i in enumerate(ev)}).T
            at = z.loc[ev]
            print("time of onsets (s):", [int(f.t[i]) for i in ev])
            summary = pd.DataFrame({"mean_z_at_onset": at.mean(), "mean_z_prev60": pre.mean(),
                                    "share_same_sign_at_onset": (np.sign(at) == np.sign(at.mean())).mean()})
            print(summary.round(2).sort_values("mean_z_at_onset", key=abs, ascending=False).head(14).to_string())

    print("\n=== Magnitude: does any feature beat trailing vol at predicting |fwd60|? (30 s samples) ===")
    for name, f in (("R2", r2), ("R1", r1)):
        s = f.iloc[::30].dropna()
        res = {c: s[c].corr(s.fwd60.abs(), method="spearman") for c in FEATS}
        top = sorted(res.items(), key=lambda kv: -abs(kv[1]))[:8]
        print(name, [(k, round(v, 3)) for k, v in top])

    print("\n=== Toy: extreme-decile signal -> mean fwd60 (ticks), per R2 half and R1 ===")
    for c in ("cancel_near_imb10", "net_liq_imb10", "dep10_imb", "t5_imb", "flow30", "big30",
              "ret60", "dev_ma300", "l1_imb", "ioc_imb30"):
        line = []
        for lab, f in (("R2a", r2.iloc[:half]), ("R2b", r2.iloc[half:]), ("R1", r1)):
            s = f.dropna(subset=[c, "fwd60"])
            lo, hi = s[c].quantile([0.1, 0.9])
            line.append(f"{lab}: low={s.fwd60[s[c] <= lo].mean():6.2f} high={s.fwd60[s[c] >= hi].mean():6.2f}")
        print(f"{c:18s} | " + " | ".join(line))


if __name__ == "__main__":
    main()
