"""Second-pass questions: momentum robustness, big-taker impact after latency, walls, queue fill odds."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

pd.set_option("display.width", 200)


def sec(s: str) -> None:
    print(f"\n=== {s} ===")


def main(out: Path) -> None:
    bbo = pd.read_pickle(out / "bbo.pkl")
    tr = pd.read_pickle(out / "trades.pkl")
    od = pd.read_pickle(out / "orders.pkl")
    g = pd.read_pickle(out / "grid1s.pkl")
    b = bbo[(bbo.bb > 0) & (bbo.ba > 0)].reset_index(drop=True)
    t = b.t.values
    mid = ((b.bb + b.ba) / 2).values

    def mid_at(x: np.ndarray) -> np.ndarray:
        return mid[np.clip(np.searchsorted(t, x, side="right") - 1, 0, len(t) - 1)]

    sec("Momentum robustness: non-overlapping 30s samples, signal = mid - MA(L) , per 10-min block")
    g["blk"] = (g.t // 600).astype(int)
    for L in [60, 300, 600]:
        g[f"dev{L}"] = g.mid - g.mid.rolling(L).mean()
    for H in [10, 30, 60]:
        g[f"f{H}"] = g.mid.shift(-H) - g.mid
    s = g.iloc[::30].dropna()
    rows = []
    for blk, d in s.groupby("blk"):
        rows.append({"blk": blk, **{f"c_dev{L}_f30": round(d[f"dev{L}"].corr(d.f30), 3) for L in [60, 300, 600]},
                     "c_past60_f60": round((d.mid - d.mid.shift(2)).corr(d.f60), 3)})
    print(pd.DataFrame(rows).to_string(index=False))
    print("pooled non-overlapping:", {f"dev{L}->f30": round(s[f"dev{L}"].corr(s.f30), 3) for L in [60, 300, 600]})
    # sign-strategy toy: hold sign(dev300) for 30s, ticks per unit, minus 1 tick round-trip cost
    for L in [60, 300, 600]:
        pnl = np.sign(s[f"dev{L}"]) * s.f30
        print(f"toy sign(dev{L}) hold30s: mean/unit={pnl.mean():.3f} ticks, by block:",
              pnl.groupby(s.blk).mean().round(2).to_list())

    sec("Largest 60s moves (crash anatomy)")
    g["r60"] = g.mid.diff(60)
    top = g.reindex(g.r60.abs().sort_values(ascending=False).index).head(200)
    picked = []
    for _, r in top.iterrows():
        if all(abs(r.t - p) > 120 for p in picked):
            picked.append(r.t)
        if len(picked) == 8:
            break
    for p in sorted(picked):
        w = g[(g.t > p - 60) & (g.t <= p)]
        tk = tr[(tr.t > p - 60) & (tr.t <= p)]
        print(f"t={p:7.0f} move={g.loc[g.t == p, 'r60'].iloc[0]:+7.1f} spr_mean={w.spr.mean():.2f} "
              f"bq_med={w.bq.median():.0f} aq_med={w.aq.median():.0f} trades_vol={tk.qty.sum()} "
              f"signed_vol={(tk.qty * tk.aggr).sum()}")

    sec("Big-taker impact AFTER 5ms latency (what we can still trade on)")
    tk = tr.groupby("taker").agg(t=("t", "first"), qty=("qty", "sum"), aggr=("aggr", "first"),
                                 lvls=("price", "nunique"))
    tt = tk.t.values
    m5 = mid_at(tt + 0.005)
    for lo, hi in [(1, 50), (50, 200), (200, 500), (500, 1000), (1000, 10**6)]:
        sel = (tk.qty >= lo) & (tk.qty < hi)
        res = {}
        for h in [0.1, 1, 10, 60]:
            res[h] = round(float(((mid_at(tt[sel] + h) - m5[sel]) * tk.aggr[sel]).mean()), 3)
        print(f"taker size [{lo},{hi}) n={int(sel.sum()):6d} continuation from t+5ms (ticks): {res}")
    sel = tk.lvls > 1
    print("multi-level sweeps n=", int(sel.sum()), {h: round(float(((mid_at(tt[sel] + h) - m5[sel]) * tk.aggr[sel]).mean()), 3)
                                                   for h in [0.1, 1, 10, 60]})

    sec("Big-taker follow toy: cross spread at t+5ms on taker>=X, exit at mid t+h (cost = half spread)")
    spr5 = (b.ba - b.bb).values[np.clip(np.searchsorted(t, tt + 0.005, side="right") - 1, 0, len(t) - 1)]
    for X in [300, 500, 1000, 2000]:
        sel = tk.qty.values >= X
        for h in [1, 10, 60]:
            gross = (mid_at(tt[sel] + h) - m5[sel]) * tk.aggr.values[sel]
            net = gross - spr5[sel] / 2 - 0.5  # enter half spread + exit approx half spread
            print(f"X={X:5d} h={h:3d}s n={int(sel.sum()):5d} gross={gross.mean():.3f} net~={net.mean():.3f}")

    sec("Rolling realized vol regime vs maker markout")
    g["vol60"] = g.mid.diff().rolling(60).std()
    tk["vol60"] = g.vol60.values[np.clip(np.searchsorted(g.t.values, tt) - 1, 0, len(g) - 1)]
    vwap = (tr.assign(pq=tr.price * tr.qty).groupby("taker").pq.sum() / tk.qty).values
    tk["mk10"] = (vwap - mid_at(tt + 10)) * tk.aggr.values
    tk["mk1"] = (vwap - mid_at(tt + 1)) * tk.aggr.values
    tk["volq"] = pd.qcut(tk.vol60, 4)
    print(tk.groupby("volq", observed=True).apply(
        lambda d: pd.Series({"n": len(d), "mk1_w": np.average(d.mk1, weights=d.qty),
                             "mk10_w": np.average(d.mk10, weights=d.qty), "mk10_small": d.mk10[d.qty < 50].mean()}),
        include_groups=False).round(3).to_string())

    sec("Wall signal: resting insert >= 2000 lots at best (same side) -> mid change")
    big = od[(od.life == "G") & (od.vol >= 2000) & (~od.crossed)].copy()
    pos = np.clip(np.searchsorted(t, big.t_in.values, side="left") - 1, 0, len(t) - 1)
    at_best = np.where(big.side == "B", big.price.values == b.bb.values[pos], big.price.values == b.ba.values[pos])
    big = big[at_best]
    sgn = np.where(big.side == "B", 1, -1)
    m0 = mid_at(big.t_in.values + 0.005)
    print("n walls at best:", len(big), "lifetime median s:", round(float((big.t_end - big.t_in).median()), 3),
          "fill share:", round(float(big.filled.sum() / big.vol.sum()), 4))
    for h in [0.1, 0.5, 1, 5, 30]:
        print(f"h={h}s mid move in wall-side direction (bid wall -> up): {np.mean((mid_at(big.t_in.values + h) - m0) * sgn):.3f}")

    sec("Depth imbalance including size: total L1 vol vs future, and qty at L1 when mid moves")
    # When bid queue small (< 100) relative to ask, does bid get taken out?
    g["imb"] = (g.bq - g.aq) / (g.bq + g.aq)
    g["thin_bid"] = g.bq < 0.2 * g.aq
    g["thin_ask"] = g.aq < 0.2 * g.bq
    for h in [1, 5, 10]:
        f = g.mid.shift(-h) - g.mid
        print(f"h={h}s fut mid | thin bid={f[g.thin_bid].mean():.3f} (n={int(g.thin_bid.sum())}) "
              f"thin ask={f[g.thin_ask].mean():.3f} (n={int(g.thin_ask.sum())}) all={f.mean():.3f}")

    sec("Queue: when best bid price persists, how long; and how many lots trade at it")
    # level episodes on bid
    bb = b.bb.values
    chg = np.flatnonzero(np.diff(bb) != 0) + 1
    starts = np.r_[0, chg]
    ends = np.r_[chg, len(bb)]
    dur = t[np.minimum(ends, len(t) - 1)] - t[starts]
    print("best-bid episode duration quantiles (s):", pd.Series(dur).quantile([.25, .5, .75, .9]).round(3).to_dict(),
          "episodes:", len(dur))
    sells = tr[tr.aggr < 0]
    # volume traded at the prevailing best bid per episode
    ep = np.searchsorted(t[starts], sells.t.values, side="right") - 1
    vol_ep = np.bincount(ep, weights=sells.qty.values, minlength=len(starts))
    print("sell-taker volume hitting per bid episode quantiles:", pd.Series(vol_ep).quantile([.25, .5, .75, .9]).to_dict())

    sec("Volume of trades per second and per minute (for fill-capacity of a 1..10 lot maker)")
    print("taker volume / s mean:", round(tr.qty.sum() / 6000, 1), "taker orders / s:", round(len(tk) / 6000, 2))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
