"""Share of seconds in which detector / drain would hold the breaker (30 s hold).
Usage: stress_share.py <sec.pkl>"""

import sys

import numpy as np
import pandas as pd

d = pd.read_pickle(sys.argv[1])
mid = d.mid.ffill()
r = mid.diff().fillna(0)
sig2 = (r**2).ewm(halflife=120).mean()
det = (mid - mid.shift(20)).abs() >= np.maximum(5, 2 * np.sqrt(sig2 * 20))
l1 = (d.bq1 + d.aq1).astype(float)
drain = l1 < 0.35 * l1.ewm(halflife=120).mean()
for name, s in (("detector", det), ("drain", drain), ("either", det | drain)):
    held = s.astype(int).rolling(30, min_periods=1).max().astype(bool)
    print(f"{name:9s} trigger seconds={s.mean():.3f} held (30 s)={held.mean():.3f}")
