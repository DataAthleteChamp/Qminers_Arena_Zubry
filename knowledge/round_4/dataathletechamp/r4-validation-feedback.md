# Round 4 validation (server tape B) feedback log

Final = the latest successful upload. Cancelling a running or waiting
submission is now possible in the portal, and new submissions show their
filename. Exports are archived locally under
`experiments/round_4/dataathletechamp/20261108-r4-validation-feedback-001/`.

**Upload budget (Round 4): 10, three used.** Ask for an upload only when a
candidate:

- beats U1 on R4 public by more than the ±25k noise;
- is better on average across paired R4-like synthetic tapes;
- does not collapse on R3 or R2.

Keep 3 uploads in reserve for the final and a fallback re-upload.

| Upload | File (sha256 prefix) | R4 public A | Validation B | Notes |
|---|---|---:|---:|---|
| U1 | `r4_u1_follower_u7_baseline.py` (d2a0fc9c, = R3 final U7) | 821,692 | **1,326,712** | penalty 0; ordinary seconds +1,198.7k (99.9/s); 34 jump seconds +128.0k (23 positive); 19/20 positive 600 s blocks |
| U2 | `r4_u2_trig2_ungated.py` (b239d85a) | 886,626 | **1,343,784** | penalty 0; fills 3,881, traded 762,300; paired vs U1: **+17,072**; see below |
| U3 slot | `r4_u6_jump_k4.py` (ca3e1b7c) | 920,538 | **1,343,238** | penalty 4,422; fills 3,919, traded 765,416; paired vs U2: **−546**; see below |

### U2 vs U1 on validation (paired; `u2-trig2-ungated/` vs `u1-follower-u7-baseline/`)

U2 was uploaded as a validation probe of TRIG2 on an independent tape from the R4 generator. The
pre-declared bar was U1 + 50k, because a real +7.9% public edge would show about +130k on a tape
twice as long. That bar was **not met**.

- **Paired difference:** +17,072 (+1.3%). The 95% block-bootstrap CI is [−66k, +79k].
- **By block:** U2 is better in 15 of 20 blocks of 600 s. The first half gives +27.8k, the second
  half −10.7k.
- **Where the difference comes from:**
  - Outside the 20 largest paired one-second changes, U2 gains +34.7k: small, steady gains in
    ordinary time.
  - Those 20 seconds net −17.7k, dominated by one jump second at 9,089 s (−32.6k).
- **Reading:**
  - The TRIG2 edge carries over in sign but at about a sixth of its public size (+1.4k vs
    +10.8k per 1,000 s).
  - Most of the public +65k was threshold fit on R4 public.
  - Expected private gain over U1 is small and positive, with jump-second risk.

### All-in probe: `r4_u8_allin.py` (sha256 058c74c9…f568), uploaded after the U6 result

- **What it is:** U6 + a gated CUSUM trigger on the per-insert placement drift (κ 0.5, h 5, τ 200 ms;
  `20261108-r4-cusum-001`), with the jump-onset burst raised to ±500 lots for 100 ms
  (`20261108-r4-allin-001`).
- **Results:** official engine, Δ vs U6.

  | file | R4 | R3 | R2 |
  |---|---:|---:|---:|
  | U8 (CUSUM + burst 500 / 100 ms) | 948,126 (+27,588) | 421,985 (+5,881) | 158,885 (+192) |
  | U7 (CUSUM only; CLI 932,031, sha 72844dc5) | +11,493 | +3,694 | +1,017 |
  | U8 with a 30 ms window | +27,354 | −9,574 | −4,966 |

  - R4 penalty 7,466. Official CLI verified; preflight passed.
- **Rule** (set by the owner's "go all in"): keep U8 if its validation is ≥ 1,333,238 (U6 − 10k).
  Otherwise re-upload U6 (`r4_u6_jump_k4.py`, ca3e1b7c) before 12:00.

### Next probe: `r4_u6_jump_k4.py` (sha256 ca3e1b7c…dac79), replacing the U5 candidate

- **What it is:** U5's jump-onset flip plus the 300-lot, 50 ms burst. The detector now needs ≥ 4 hidden
  inserts within 20 ms at spread ≤ 2 (U5: 3 inserts at spread ≤ 1).
- **Results:** official engine; Δ vs U2.

  | file | R4 | R3 | R2 | R4 penalty |
  |---|---:|---:|---:|---:|
  | U6 | 920,538 (+33,912) | 416,104 (+700) | 158,693 (−822) | 4,795 |
  | U5 | 912,274 (+25,648) | 407,508 (−7,896) | 152,088 (−7,427) | 4,488 |

  - Official CLI verified; preflight passed.
  - The 20–40 ms windows at K 4 and spread ≤ 2–3 all give +33.7k to +34.4k on R4
    (`20261108-r4-u5-tune-001`).
- **Pre-declared rule:** keep U6 as the final if its validation is ≥ 1,333,784 (U2 − 10k). Otherwise
  re-upload U2 (`r4_u2_trig2_ungated.py`, b239d85a) before 12:00.
  - The paired-difference CI on validation is about ±70k, so the probe can only catch a clear loss.
- **Validation result** (`u6-jump-k4/`): 1,343,238, i.e. U2 − 546. The rule is met, so U6 stays the final.
  - Only 16 seconds differ from U2: about 8 onsets.
  - Wins: +7.8k, +3.7k, +1.9k. Losses: −6.6k, −5.3k, −2.9k, −2.2k.
  - Unlike R4 public (5 of 5 onsets right), validation onsets were a wash. Pooled over about 15
    onsets the expected gain is small (about +2k per onset).

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
