# Data release: the hidden fair price and regimes

After the final results the organisers released every round's validation and private tapes, the
hidden fair price and the regime timings (`data/market_data/`, see its README). This note records what
we verified and what the hidden data shows.
- **Data:** `market_data.zip` (sha256 in `data/market_data/manifest.json`).
- **Scripts and raw outputs:** `experiments/round_4/dataathletechamp/20261109-release-*`.
- **Engine:** the unchanged official engine.

## 1. The released tapes are the official ones

Replaying our finals reproduces every official score to the dollar (`20261109-release-reproduction-001`):

| Final | Tape | Local replay = dashboard |
|---|---|--:|
| R1: Maciej's 8-slot maker (`submissions/round_1/dataathletechamp/final_20261107/strategy.py`) | private | 504,903 |
| R2: Maciej's EMA grid maker (`submissions/round_2/dataathletechamp/final_actual_20261108/strategy.py`) | validation / private | 80,993 / 2,281 |
| R3: Paweł's `r3_final.py` (copy: `strategies/round_4/dataathletechamp/r4_final_pawel_r3_final.py`) | validation / private | 597,854 / 589,202 |
| R3: our U7 (`strategies/round_3/dataathletechamp/r3_follower_u7_flow_deepfv.py`) | validation | 538,844 |
| R4: Paweł's `r3_final.py` (same copy) | validation / private | 1,420,312 / 1,250,605 |

The engine, our archived files and the released data agree exactly. The replays also settle which
file was our Round 3 final: it was Paweł's `r3_final.py`.

## 2. Round 1: one regime, a compound-Poisson random walk

Both Round 1 fair-price files behave the same way (`20261109-release-fair-regime-001/r1_and_meta.py`):
- **Timing:** the price moves 7.8–7.9 times per second, at Poisson times (exponential gaps, CV 1.0).
- **Size:** each move is independent, zero-mean and about 0.31 ticks (sd). Moves are nearly normal,
  slightly heavy-tailed (excess kurtosis ~1), and the largest is 2.1 ticks.
- **No link between the two:** move size does not depend on the wait before it (corr(move², gap) = 0.02).
- **Net effect:** a driftless random walk of about 0.87 ticks per √s. There was no drift to predict;
  the edge was in execution.

## 3. Rounds 2–4: regimes

| Regime | Length | Fair price |
|---|---|---|
| base | the rest: 41–82% of the time | calm: about 8 moves per second (R2) or 15–19 (R3–R4), sd ~0.3 ticks |
| `s3_turbulent` | spells of ~40–55 s, 15–30% of the time | 1.5–3× the base rate of moves, heavy-tailed: sd 0.7–2.1, single moves up to 100+ ticks |
| `s2_thinning` | exactly 3.0 s | almost frozen: 1.4–4 moves per second, median net move ≤ 1.1 ticks |
| `s2_burst_A` / `_B` | exactly 3.2 s | opens with a jump in the first 50 ms (median 22–36 ticks): A down, B up |
| `meta_A` / `_B` (R4 only) | ~19 s | one-way drift of about 11–16 ticks, A down and B up in 86–95% of episodes |
| `reserve_A` / `_B` (R4 only) | ~25 s | no reliable direction |

These facts hold on all nine regime files (`burst_check2.py`; windows are half-open, `[Start, End)`):
- **Every burst comes straight after a thinning window:** 410 of 410 bursts.
- **The opening jump always has the labelled sign** (A down, B up, 100%). The burst as a whole keeps
  that sign 90–100% of the time.
- **Bursts are regular:** 52–56 per 12,000 s tape, about one every 3.5–4 minutes.

## Why it matters

- **The precursor existed.** Each burst's opening jump (median 22–36 ticks per tape) was preceded by
  a 3-second lull in the fair price. In Round 4 we searched for exactly such a precursor
  (`r4-hidden-ioc-precursor.md`, `r4-jump-onset.md`).
- **Next experiment:** check whether the visible book shows that lull live, for example as fewer
  inserts or thinner depth. If it does, the follower could get ready before the jump instead of
  reacting about 0.3 s after it.
- **Round 4's extra regimes:** the slow `meta` drifts are a plausible source for the trend-like episodes
  we saw in Round 4. That is an untested match.
