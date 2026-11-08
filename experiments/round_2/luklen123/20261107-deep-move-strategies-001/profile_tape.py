"""Quick profile of a per-second table. Usage: profile_tape.py <sec.pkl>"""

import sys

import pandas as pd

d = pd.read_pickle(sys.argv[1])
d["mid"] = d.mid.ffill()
r = d.mid.diff()
print("spread dist", d.spr.value_counts(normalize=True).sort_index().head(6).round(3).to_dict())
print("L1 median", d.bq1.median(), d.aq1.median(), "1s vol", round(r.std(), 2),
      "range", d.mid.min(), d.mid.max())
f60 = d.mid.shift(-60) - d.mid
print("seconds with |60s move| >= 63:", int((f60.abs() >= 63).sum()), "std60", round(f60.std(), 1))
print("taker vol/s", round((d.tk_buy + d.tk_sell).mean(), 1))
