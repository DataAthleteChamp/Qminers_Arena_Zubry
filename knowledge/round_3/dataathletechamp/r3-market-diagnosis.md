# Round 3 public tape: market diagnosis versus R0-R2

Question: what changed on the Round 3 public tape (A), why do all retained
R1/R2 strategies lose on it, and which observable mechanisms remain?

## Data and method

- A: `data/round3/round3_public.csv`, SHA256
  `1021586b92a3d9dfdb70096e6b0af34d460813b139f1f51f56b73871cb5a2d15`,
  86,670,643 bytes, 2,412,805 rows, 0.001095-5999.994333 s, zero duplicate
  timestamps, zero integrity violations. Inserts 1,234,596 (G-B 589,656,
  G-A 588,666, F-B 28,161, F-A 28,113); cancels 1,178,209.
- Organizer rule (relayed by owner): validation B and private C keep the old
  length (~12,000 s); public A is about half, so E[B PnL] is about 2x E[A PnL]
  only if the tapes are stationary. In R2 our makers realised B/A = 0.3-0.6.
- Engine: unchanged official simulator; 23/23 upstream fingerprints match;
  `QminersOrg/qminers-algo-arena` still at `3f5bea7` on 2026-11-08 01:10.
- Same-method profile: archived R2 `market-profile-v3/profile.py`, only the
  output path changed, run as experiment `20261108-r3-market-profile-001`.
  R0/R1/R2 reports are the archived R2 outputs.
- Event-level null replays (official engine, no orders) of R0 sample_v2, R1,
  R2 A and R3 A: `20261108-r3-deep-diagnostics-001` (`replay.py`,
  `analyze.py`, `signals.py`). Fit window for any threshold: t < 2400 s;
  evaluation t >= 2400 s. All descriptions consume A information.

## Cross-round facts (same code for every tape)

| Metric | R0 v2 | R1 | R2 A | R3 A |
|---|---:|---:|---:|---:|
| Duration s | 5,750 | 12,000 | 6,000 | 6,000 |
| Events/s | 348 | 368 | 366 | 402 |
| External volume lots/s | 553 | 1,121 | 1,167 | 1,194 |
| Time-weighted spread ticks | 1.59 | 1.07 | 1.23 | 1.25 |
| 1 s return SD ticks | 0.50 | 0.92 | 3.65 | 4.49 |
| Mid min / max | 9966 / 10023 | 9992 / 10095 | 9459 / 10008 | 9768 / 10130 |
| Taker order-sign ACF1 | 0.000 | 0.015 | 0.030 | 0.052 |
| 1 s return ACF1 | 0.065 | 0.010 | 0.014 | 0.108 |
| VR5 / VR60 / VR300 / VR1200 | 1.07/1.19/1.10/1.14 | 1.00/1.04/0.90/0.52 | 0.94/1.10/1.69/2.50 | 1.18/0.85/0.78/1.03 |
| Touch maker markout @0 / 1 / 10 / 60 s | +0.84/+0.84/+0.84/+0.84 | +0.54/+0.03/+0.04/+0.005 | +0.60/-0.33/-0.52/-0.48 | +0.63/-0.62/-0.38/-0.17 |
| Past-fit ridge MSE gain 0.2 / 1 s | n/a | 18.9% / 11.3% | 2.9% / 0.9% | 3.5% / 1.9% |
| 100-lot frictionless sign oracle /s at 1 / 10 / 60 s | 36/13/6 | 64/23/10 | 148/62/32 | 199/80/35 |

R3 is a third regime: **momentum up to ~10 s and mean reversion at 30-300 s**
(R3 1 s ACF1 by thirds 0.139/0.082/0.111). R2 trended/crashed at long
horizons; R1 was calm with strong short-horizon book predictability.
R3 mid at 600 s marks: 9995.5, 9909.5, 10035, 10097.5, 9862, 9781.5, 9874.5,
10080.5, 9898.5, 9886.5, end 9872.5 — a 360-tick range with 100-250-tick swings.

## Frozen strategies on R3 A (all penalty 0)

| Strategy (unchanged bytes) | R3 A PnL | Earlier evidence |
|---|---:|---|
| R2 actual Final (`1d2c63ea`) | -33,296 | R2 A 127,559; export 80,993 |
| R2 gap/FIFO = luklen `kuba.py` (`ac3d1814`) | -35,203 | R2 A 103,998; B 43,782 |
| R2 1x96 trial (`fbaaf56d`) | -35,568 | R2 A 121,235 |
| luklen s_67 40-lot (`27664f05`) | -40,848 | R2 A 104,260 |
| R2 clean reference (`10886b7d`) | -42,132 | R2 A 104,703; B 47,150 |
| luklen s_75 HPO (`199582a1`) | -72,860 | R2 A 124,971; B untested |
| R1 Final (`c1f19466`) | -422,816 | R1 505,225 / private 504,903 |
| official trend_follower | -195 | example |

The R2 Final oscillated between +14,788 (3600 s) and -33,296: its 10-60 s
trend-target was whipsawed by 30-300 s reversion. These are A-only replays.

## Mechanisms observed on R3 A (descriptive, not executed PnL)

1. **Toxic passive fills.** Lot-weighted touch markout +0.626 at fill, then
   -0.458 @0.5 s, -0.619 @1 s, -0.591 @5 s; as a group touch makers lose
   559 ticks·lot/s at 1 s. Symmetric resting quotes are the losing default.
2. **Informed takers with post-latency drift.** Measured from the standing mid
   5 ms after each taker order: 1-10 lots +0.36 @1 s; 10-50 +0.42; 50-200 +0.66;
   200-1000 +1.28; >=1000 +2.71 (R1 <=+0.65 for >=1000; R2 small orders ~0).
   Multi-level sweeps continue most: 200-1000 lots sweeping >=2 levels
   +3.48 mean/+3.0 median @1 s (n=866); 1000-3000 lots +5.26/+5.0 (n=164).
   Sweep continuation had the same sign on R2 (+2.41/+3.25), so it is the most
   transfer-plausible fast signal.
3. **Fade the flow at 10-60 s.** Touch fills against the sign of the 10 s
   taker-flow EMA earn +1.254 @10 s and +2.348 @60 s per lot (2.76M lots);
   fills with the flow lose -2.067/-2.772. R2 had the opposite sign at 60 s
   (+0.44 with / -1.41 against for 2 s EMA), so this is R3-specific.
4. **Short-horizon flow predictability.** 0.5 s signed-volume EMA vs 0.5 s
   future move corr +0.214 fit / +0.181 evaluation; eval top/bottom 5% states
   moved +1.43/-1.47 ticks within 0.5 s. At 30 s the 10 s flow EMA reverses
   (-0.168 fit / -0.129 eval).
5. **Penalty geometry.** `simulator/simulator.py:1290-1295` accrues
   elapsed-seconds x 10,000 whenever |I| > 100, independent of excess size.
   A 1000-lot burst needs >10 ticks per second held to pay; no observed
   trigger has that mean move, so bursts are not a default lever.
6. **Fill size decides toxicity.** Maker markout @1 s per filled taker order
   (lot-weighted): 1-25 lots +0.259, 26-100 +0.089, 101-300 -0.329,
   301-500 -0.875, 501-1000 -1.343, >1000 -2.636 (R2: +0.397 ... -1.346).
   Orders >=500 lots are ~36% of volume and -1.916 (first/last 3000 s
   -1.816/-2.013). A resting order behind a ~550-lot L1 queue is filled mainly
   by these large orders, so queue position, not just price, sets the markout.
   This independently reproduces an owner-pasted external report (100 ms
   sampling) to within ~0.05 ticks; the external text is preserved in
   `experiments/round_3/dataathletechamp/20261108-r3-external-report-crosscheck-001/`.

## Executable follow-the-taker screen (not official PnL)

Enter by crossing at the touch 5 ms after the taker event, exit by crossing
after H; mean ticks per lot, fit t<2400 s / eval t>=2400 s; no overlap control,
no exit latency, size capped by entry L1 only:

| Trigger (R3 A) | Events | H=1 s | H=2 s | R2 A H=2 s | R1 H=2 s |
|---|---:|---:|---:|---:|---:|
| taker >=1000 lots | 757 | +0.73 / +1.19 | +1.24 / +1.86 | +0.25 / -0.20 | -0.64 / -0.75 |
| 200-1000 lots sweeping >=2 levels | 866 | +1.36 / +0.94 | +1.84 / +1.18 | +0.35 / -0.57 | -1.00 / -1.22 |
| taker >=500 lots | 2,850 | +0.34 / +0.40 | +0.66 / +0.65 | -0.24 / -0.27 | -0.72 / -0.75 |

This is the strongest R3-specific fast mechanism found so far: roughly
100 lots x 1.2-1.9 ticks x ~1,600 distinct triggers before overlap
control (order of 0.2-0.3M on A). It fails on R1/R2, so it is only valid if
B/C share the R3 regime. Script: `follow_taker_screen.py` in the diagnostics
experiment (output `follow-taker-screen-v2.txt`).

## Limits

One public tape, many screens, A-only. Markout tables assume fills on market
liquidity, not our queue position. B/C may differ; R2 showed public rankings
can reverse on B. No private-score probability is claimed.

## Reproduce

```bash
env -u VIRTUAL_ENV PYTHONPATH=$PWD uv run --locked python experiments/round_3/dataathletechamp/20261108-r3-market-profile-001/profile.py --data data/round3/round3_public.csv --id round3 --label round3-public-A
env -u VIRTUAL_ENV PYTHONPATH=$PWD uv run --locked python experiments/round_3/dataathletechamp/20261108-r3-deep-diagnostics-001/replay.py --data data/round3/round3_public.csv --label round3
cd experiments/round_3/dataathletechamp/20261108-r3-deep-diagnostics-001 && uv run --locked python analyze.py && uv run --locked python signals.py round3 round2 round1
env -u VIRTUAL_ENV PYTHONPATH=$PWD uv run --locked python experiments/round_3/dataathletechamp/20261108-r3-seed-baselines-001/run.py --id <id> --strategy <path> --tape data/round3/round3_public.csv --stage r3-A-seed-diagnostic
```
