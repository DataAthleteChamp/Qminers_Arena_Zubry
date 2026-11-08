"""Regime persistence: is trailing realized vol / spread a usable ex-ante filter? Usage: regime.py <out_dir>"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
out = Path(sys.argv[1])
g = pd.read_pickle(out / "grid1s.pkl")
r = g.mid.diff()
for L in (10, 30, 60):
    past = r.rolling(L).std()
    fut = r[::-1].rolling(60).std()[::-1].shift(-1)
    print(f"corr(trailing vol{L}s, next-60s vol) = {past.corr(fut):.3f}")
v60 = r.rolling(60).std()
q = v60.quantile([.5, .75, .9])
print("trailing vol60 quantiles:", q.round(2).to_dict())
hi = v60 > 3.0
runs = (hi != hi.shift()).cumsum()[hi]
print(f"share of seconds with vol60>3: {hi.mean():.3f}; episodes: {runs.nunique()}; median episode s: {runs.value_counts().median():.0f}")
spr = g.spr
f10 = (g.mid.shift(-10) - g.mid).abs()
print("mean |10s move| by current spread:", f10.groupby(spr.clip(upper=4)).mean().round(2).to_dict())
print("mean |10s move| by vol60 bucket:", f10.groupby(pd.cut(v60, [0, 1.5, 3, 6, 100])).mean().round(2).to_dict())
