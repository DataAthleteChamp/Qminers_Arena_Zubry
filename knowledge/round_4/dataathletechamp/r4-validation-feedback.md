# Round 4 validation (server tape B) feedback log

Final = the latest successful upload. Cancelling a running or waiting
submission is now possible in the portal, and new submissions show their
filename. Exports are archived locally under
`experiments/round_4/dataathletechamp/20261108-r4-validation-feedback-001/`.

| Upload | File (sha256 prefix) | R4 public A | Validation B | Notes |
|---|---|---:|---:|---|
| U1 | `r4_u1_follower_u7_baseline.py` (d2a0fc9c, = R3 final U7) | 821,692 | **1,326,712** | penalty 0; ordinary seconds +1,198.7k (99.9/s); 34 jump seconds +128.0k (23 positive); 19/20 positive 600 s blocks |

The validation tape is momentum-friendly like R4 public. B over A is 1.61×
for the same file (R3: 1.30×).

## Neighbourhood of U8 on R4 (`20261108-r4-neighbourhood-001`)

U8 makes 821,664 on R4, 415,883 on R3 and 171,568 on R2. One change at a
time (R4 / R3 / R2):

| change | R4 | R3 | R2 |
|---|---:|---:|---:|
| flip margin 0.6 | 792k | 392k | 133k |
| flip margin 0.8 | 821k | 392k | 161k |
| flip margin 1.3 | 782k | 382k | 154k |
| flip margin 1.6 | 729k | 374k | 140k |
| A_SWEEP 2 | 821k | 402k | 158k |
| A_SWEEP 4 | 822k | 419k | 173k |
| flow 400 | 823k | 389k | 159k |
| flow 900 | 822k | 412k | 157k |
| TRIG1 FV 0.35 | 826k | 405k | 178k |
| TRIG1 FV 0.75 | 816k | 383k | 171k |

- HOLD_S 10, 15 and 20 are identical to each other (R4 822,094): the hold
  deadline almost never binds.
- Flip margin 1.0 stays best on R4.
- No single parameter gives a material gain. Improvements must be
  structural.

## Structural tests on R4 (official engine; R4 / R3 / R2)

| test | best R4 | R3 | R2 | verdict |
|---|---:|---:|---:|---|
| pure price trend families: mid momentum 5 s / EMA crossovers (`20261108-r4-trend-families-001`) | 396,638 / −1k to −86k | – | – | far below U7 |
| second flow window 0.5–5 s (`20261108-r4-flow2-001`) | 823,375 | – | 167,085 | noise |
| adverse stop 3 ticks, IOC exit (`20261108-r4-stops-001`) | 829,890 | 412,707 | 161,836 | +8k R4, R2 −5k |
| adverse stop 5 / 8 / 12, giveback 8 / 15 | 822–826k / 815k | 402–417k | 152–166k | noise or worse |
| alpha gate refit with R4 (h 2 s, h 5 s, variance-normalised; `r4-alpha-refit.md`) | 816,529 | R3+R2 −14% to −26% | – | rejected; an independent R3+R2 gate is better |
| evidence sizing with reset, τ 5–10 s (`20261108-r4-evidence-001`) | 816,828 | 413,322 | 172,296 | worse on R4 |

On R4 the event study shows a large continuation after followed trades that
go 5 ticks against at 2 s. In the engine a stop on such trades is
noise-sized, because the follower re-enters on the next signal. Use event
studies to rank ideas, not to size gains.

## Random search over U8's signal settings (`20261108-r4-random-search-001`)

The search drew 40 random combinations of HOLD_S, HOLD_F_S, FLIP_MARGIN,
A_SWEEP, RUN_MIN, FILL_MIN, BIG_FILL, FLOW_TRIG, TRIG1_FLOW, TRIG1_FV and
TRIG1_GATED (seed 20261108), plus U8 and U8 with a 10 s hold. Each ran on R4,
R3 and R2.

- **Best on R4:** rs14 at 823,052, +0.2% over U8, but −7.6% on R3.
- **U8 with a 10 s hold:** 822,094 / 415,983 / 171,468, equal to U8.
- **Best for the worst tape:** apart from U8 itself, every combination loses
  at least 3.9% somewhere (rs20: R4 −3.9%).

U8 (equivalently U7) is a robust local optimum of this parameter space.
Further gains must come from new information or timing, not settings.
