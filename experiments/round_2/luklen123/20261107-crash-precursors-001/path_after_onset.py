"""Average signed mid path around large-move onsets: how much is left once the move is visible?"""
import sys
import pandas as pd
d = pd.read_pickle(sys.argv[1])
mid = d["mid"].ffill().values
fwd60 = pd.Series(mid).shift(-60) - pd.Series(mid)
thr = 2 * fwd60.std()
for sign, lab in ((-1, "DOWN"), (1, "UP")):
    cand = fwd60.index[(sign * fwd60) >= thr].tolist()
    ev = []
    for i in cand:
        if not ev or i - ev[-1] > 120:
            ev.append(i)
    print(f"{lab} n={len(ev)} threshold={thr:.0f}")
    for i in ev:
        p = lambda k: sign * (mid[min(len(mid) - 1, i + k)] - mid[i])
        path = {k: round(p(k), 1) for k in (-60, -30, -10, 0, 5, 10, 20, 30, 60, 120, 300)}
        print("  onset", i, path, " left after 10s->300s:", round(p(300) - p(10), 1))
