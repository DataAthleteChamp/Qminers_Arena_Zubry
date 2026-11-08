"""Share of seconds flagged by smoothed-L1 drain variants. Usage: drain_variants.py <sec.pkl>"""
import sys
import pandas as pd
d = pd.read_pickle(sys.argv[1])
l1 = (d.bq1 + d.aq1).astype(float)
slow = l1.ewm(halflife=120).mean()
mid = d.mid.ffill()
fwd = (mid.shift(-60) - mid).abs()
for hl in (5, 10):
    fast = l1.ewm(halflife=hl).mean()
    for ratio in (0.35, 0.5):
        s = fast < ratio * slow
        print(f"fast_hl={hl:2d} ratio={ratio} flagged={s.mean():.3f} |fwd60| flagged={fwd[s].mean():.1f} vs not={fwd[~s].mean():.1f}")
