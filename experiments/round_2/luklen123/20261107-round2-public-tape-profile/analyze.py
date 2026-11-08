"""Profile a reconstructed tape for strategy design. Usage: analyze.py <tape.csv> <out_dir>"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 30)


def sec(title: str) -> None:
    print(f"\n=== {title} ===")


def main(tape: Path, out: Path) -> None:
    raw = pd.read_csv(tape, dtype={"Side": "string", "Lifespan": "string"})
    bbo = pd.read_pickle(out / "bbo.pkl")
    tr = pd.read_pickle(out / "trades.pkl")
    od = pd.read_pickle(out / "orders.pkl")

    sec("Raw tape")
    print(f"rows={len(raw)} t=[{raw.Time.min():.6f},{raw.Time.max():.6f}] duration_s={raw.Time.max() - raw.Time.min():.1f}")
    print(raw.Operation.value_counts().to_string())
    ins = raw[raw.Operation == "Insert"]
    print("side:", ins.Side.value_counts().to_dict(), "lifespan:", ins.Lifespan.value_counts().to_dict())
    print("monotonic time:", bool(raw.Time.is_monotonic_increasing), "dup ids among inserts:",
          int(ins.OrderId.duplicated().sum()))
    print("price range:", ins.Price.min(), ins.Price.max(), "volume quantiles:",
          ins.Volume.quantile([0, .25, .5, .75, .9, .99, 1]).to_dict())
    print("top volumes:", ins.Volume.value_counts().head(12).to_dict())
    dt = np.diff(raw.Time.values)
    print(f"inter-event dt: mean={dt.mean() * 1e3:.3f}ms median={np.median(dt) * 1e3:.3f}ms "
          f"p99={np.quantile(dt, .99) * 1e3:.2f}ms max={dt.max():.3f}s same-timestamp share={np.mean(dt == 0):.3f}")
    canc = raw[raw.Operation == "Cancel"]
    ins_ids = set(ins.OrderId.values)
    print("cancels of never-inserted ids:", int((~canc.OrderId.isin(ins_ids)).sum()))
    filled_ids = set(od.loc[od.end == "filled", "id"].values)
    ioc_ids = set(od.loc[od.end == "ioc", "id"].values)
    canc_ids = canc.OrderId.values
    unk = canc[~canc.OrderId.isin(set(od.loc[od.end == "cancel", "id"].values))]
    print(f"cancels not applied={len(unk)}: of which target fully-filled={unk.OrderId.isin(filled_ids).sum()} "
          f"target IOC={unk.OrderId.isin(ioc_ids).sum()} dup-cancel={pd.Series(canc_ids).duplicated().sum()}")

    sec("Event rate per 10 minutes")
    raw["blk"] = (raw.Time // 600).astype(int)
    print(raw.groupby(["blk", "Operation"]).size().unstack().to_string())

    sec("BBO / spread")
    b = bbo[(bbo.bb > 0) & (bbo.ba > 0)].copy()
    b["spr"] = b.ba - b.bb
    t = b.t.values
    w = np.diff(np.append(t, t[-1]))  # time weights
    sp = b.spr.values
    for v in sorted(set(np.unique(sp)[:12])):
        pass
    tw = pd.Series(w).groupby(sp).sum() / w.sum()
    print("crossed/locked rows:", int((sp <= 0).sum()))
    print("time-weighted spread distribution (ticks):", tw.head(12).round(4).to_dict())
    print("event-weighted spread quantiles:", pd.Series(sp).quantile([.1, .5, .9, .99]).to_dict())
    b["mid"] = (b.bb + b.ba) / 2
    print("L1 qty quantiles bid:", b.bq.quantile([.1, .5, .9]).to_dict(), "ask:", b.aq.quantile([.1, .5, .9]).to_dict())
    print("mid start/end/min/max:", b.mid.iloc[0], b.mid.iloc[-1], b.mid.min(), b.mid.max())

    # 1-second grid of mid
    grid = np.arange(np.ceil(t[0]), np.floor(t[-1]) + 1)
    idx = np.searchsorted(t, grid, side="right") - 1
    g = pd.DataFrame({"t": grid, "mid": b.mid.values[idx], "spr": sp[idx], "bq": b.bq.values[idx],
                      "aq": b.aq.values[idx], "bb": b.bb.values[idx], "ba": b.ba.values[idx]})
    g.to_pickle(out / "grid1s.pkl")
    sec("Mid per 10 minutes (1s grid)")
    g["blk"] = (g.t // 600).astype(int)
    r1 = g.mid.diff()
    g["r1"] = r1
    print(g.groupby("blk").agg(mid_first=("mid", "first"), mid_last=("mid", "last"), mid_min=("mid", "min"),
                               mid_max=("mid", "max"), vol1s=("r1", "std"), spr_med=("spr", "median"),
                               spr_mean=("spr", "mean"), bq_med=("bq", "median"), aq_med=("aq", "median")).round(3)
          .to_string())

    sec("Return structure (mid, 1s grid)")
    m = g.mid.values
    for h in [1, 2, 5, 10, 30, 60, 120, 300, 600]:
        d = m[h:] - m[:-h]
        print(f"h={h:4d}s std={d.std():8.3f} mean={d.mean():8.4f} var_ratio(vs 1s*h)={d.var() / (r1.var() * h):.3f}")
    print("autocorr of 1s returns lag1..5:", [round(r1.autocorr(k), 4) for k in range(1, 6)])
    r10 = pd.Series(m[::10]).diff()
    print("autocorr of 10s returns lag1..3:", [round(r10.autocorr(k), 4) for k in range(1, 4)])
    r60 = pd.Series(m[::60]).diff()
    print("autocorr of 60s returns lag1..3:", [round(r60.autocorr(k), 4) for k in range(1, 4)])
    # mean reversion to rolling mean
    for L in [30, 120, 600]:
        dev = g.mid - g.mid.rolling(L).mean()
        fut = g.mid.shift(-30) - g.mid
        c = dev.corr(fut)
        print(f"corr(mid - MA{L}, next 30s return) = {c:.4f}")

    sec("Event-level mid changes")
    mid_ev = b.mid.values
    dm = np.diff(mid_ev)
    nz = dm[dm != 0]
    print(f"mid changes: {len(nz)} of {len(dm)} events; |dm| dist:",
          pd.Series(np.abs(nz)).value_counts().head(8).to_dict())
    s = np.sign(nz)
    print("sign autocorr of successive mid changes (lag1):", round(float(np.corrcoef(s[:-1], s[1:])[0, 1]), 4),
          "(negative = bounce)")

    sec("Trades")
    print(f"trades={len(tr)} volume={tr.qty.sum()} aggr buy share(vol)={tr.loc[tr.aggr > 0, 'qty'].sum() / tr.qty.sum():.3f}")
    # aggregate trades per taker
    tk = tr.groupby("taker").agg(t=("t", "first"), qty=("qty", "sum"), aggr=("aggr", "first"),
                                 lvls=("price", "nunique"), px_first=("price", "first"), px_last=("price", "last"))
    print(f"taker orders={len(tk)} size quantiles:", tk.qty.quantile([.5, .9, .99, 1]).to_dict(),
          "multi-level sweeps:", int((tk.lvls > 1).sum()))
    print("maker age at fill (s) quantiles:", tr.maker_age.quantile([.1, .5, .9, .99]).round(3).to_dict())
    tk["blk"] = (tk.t // 600).astype(int)
    print("taker count/vol per 10min:")
    print(tk.groupby("blk").agg(n=("qty", "size"), vol=("qty", "sum"),
                                buy_share=("aggr", lambda x: (x > 0).mean())).round(3).to_string())
    # taker inter-arrival / clustering
    tdt = np.diff(tk.t.values)
    print(f"taker inter-arrival: mean={tdt.mean():.3f}s median={np.median(tdt):.4f}s; share<5ms={np.mean(tdt < .005):.3f}")
    sg = tk.aggr.values
    print("trade sign autocorr lag1,2,5,10:",
          [round(float(np.corrcoef(sg[:-k], sg[k:])[0, 1]), 4) for k in (1, 2, 5, 10)])

    sec("Maker markout: mid after trade vs trade price, signed for passive side")
    # passive side gains (price - mid_future) * aggr  (aggressor buys -> maker sold at price)
    tt = tk.t.values
    pos0 = np.searchsorted(t, tt, side="left") - 1  # state before taker event
    pos0 = np.clip(pos0, 0, len(t) - 1)
    mid_before = mid_ev[pos0]
    vwap = (tr.assign(pq=tr.price * tr.qty).groupby("taker").pq.sum() / tk.qty).reindex(tk.index).values
    for h in [0.0, 0.005, 0.05, 0.5, 1, 5, 10, 30, 60, 300]:
        pos = np.searchsorted(t, tt + h, side="right") - 1
        mf = mid_ev[pos]
        mk = (vwap - mf) * tk.aggr.values  # per unit, maker perspective
        print(f"h={h:7.3f}s maker markout/unit mean={np.average(mk, weights=tk.qty):7.3f} "
              f"| half-spread captured vs mid_before={np.average((vwap - mid_before) * tk.aggr.values, weights=tk.qty):.3f}"
              f" | mid move in aggr dir={np.average((mf - mid_before) * tk.aggr.values, weights=tk.qty):.3f}")

    sec("Markout by taker size bucket (maker perspective, h=10s, per unit)")
    pos = np.searchsorted(t, tt + 10, side="right") - 1
    tk["mk10"] = (vwap - mid_ev[pos]) * tk.aggr.values
    pos = np.searchsorted(t, tt + 1, side="right") - 1
    tk["mk1"] = (vwap - mid_ev[pos]) * tk.aggr.values
    tk["szb"] = pd.qcut(tk.qty, 5, duplicates="drop")
    print(tk.groupby("szb", observed=True).agg(n=("qty", "size"), mk1=("mk1", "mean"), mk10=("mk10", "mean")).round(3)
          .to_string())

    sec("L1 queue imbalance -> future mid (1s grid)")
    g["imb"] = (g.bq - g.aq) / (g.bq + g.aq)
    for h in [1, 5, 10, 30, 60]:
        fut = g.mid.shift(-h) - g.mid
        c = g.imb.corr(fut)
        q = pd.qcut(g.imb, 5, duplicates="drop")
        print(f"h={h:3d}s corr={c:.4f} mean fut by imb quintile:",
              fut.groupby(q, observed=True).mean().round(3).to_list())

    sec("Trade-flow imbalance (signed taker volume over past 10s) -> future mid")
    tk_sv = pd.Series(tk.qty.values * tk.aggr.values, index=tk.t.values)
    cum = np.cumsum(tk_sv.values)
    ci = np.searchsorted(tk.t.values, g.t.values, side="right") - 1
    cs = np.where(ci >= 0, cum[np.clip(ci, 0, None)], 0)
    for L in [5, 10, 60]:
        flow = pd.Series(cs) - pd.Series(cs).shift(L)
        for h in [5, 30, 60]:
            fut = g.mid.shift(-h) - g.mid
            print(f"flow{L}s -> fut{h}s corr={flow.corr(fut):.4f}")

    sec("Order lifecycle")
    gtc = od[od.life == "G"]
    print(od.end.value_counts().to_dict())
    print("crossed on entry share:", round(od.crossed.mean(), 4))
    lifet = (gtc.t_end - gtc.t_in).dropna()
    print("GTC lifetime (s) quantiles:", lifet.quantile([.1, .25, .5, .75, .9, .99]).round(4).to_dict())
    c = gtc[gtc.end == "cancel"]
    print("cancel lifetime <5ms share:", round(((c.t_end - c.t_in) < .005).mean(), 4),
          "<50ms:", round(((c.t_end - c.t_in) < .05).mean(), 4))
    print("GTC fill ratio (volume):", round(gtc.filled.sum() / gtc.vol.sum(), 4))

    sec("Placement distance of resting inserts from best same-side (ticks, at insert time)")
    ins_ev = bbo[bbo.op == 1]  # resting inserts (non-crossing)
    # align with raw inserts that rested: join on time order
    rest_ins = od[(od.life == "G") & (~od.crossed)].sort_values("t_in")
    pos = np.searchsorted(t, rest_ins.t_in.values, side="left") - 1
    pos = np.clip(pos, 0, len(t) - 1)
    bbp, bap = b.bb.values[pos], b.ba.values[pos]
    dist = np.where(rest_ins.side.values == "B", bbp - rest_ins.price.values, rest_ins.price.values - bap)
    print(pd.Series(dist).value_counts().sort_index().loc[-5:25].to_dict())
    print("inside-spread (improving) share:", round(float((dist < 0).mean()), 4))

    sec("Price level structure: time at each mid residue mod 10/100 and big resting walls")
    print("mid mod 10 dist (1s grid):", (g.mid % 10).value_counts(normalize=True).sort_index().round(3).to_dict())
    big = od[(od.vol >= od.vol.quantile(.999))]
    print("orders >= p99.9 volume:", len(big), "vol threshold", od.vol.quantile(.999),
          "ends:", big.end.value_counts().to_dict())
    print(big[["side", "price", "vol", "t_in", "t_end", "end", "filled"]].head(15).to_string())

    sec("Simple passive-MM opportunity (1-lot at best, ignoring queue): touch frequency")
    # how often price trades through each side: count taker events per second and per spread state
    tk["spr_before"] = sp[pos0]
    print(tk.groupby("spr_before").agg(n=("qty", "size"), mk1=("mk1", "mean"), mk10=("mk10", "mean")).head(8)
          .round(3).to_string())


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
