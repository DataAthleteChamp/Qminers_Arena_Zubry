# Round 4 opening: data, first profile and incumbents

## Data

`data/round4/round4_public.csv`: sha256 61c0b6d1…8a56, 2,398,520 rows,
6,000 s, price 9,146–10,039. Every check passed: time ordered, unique insert
IDs, positive inserts, cancels target known IDs. The lossless gzip archive
(19.9 MB) and the manifest are committed. Registration script:
`experiments/round_4/dataathletechamp/20261108-r4-data-registration-001/register.py`.

The generator family is unchanged: G resting inserts (584,787 asks /
585,291 bids), F IOCs (29,320 / 29,125) and cancels. Official null replay:
952,959 BBO changes and 209,655 trades
(`20261108-r4-diagnostics-001/round4/replay.npz`).

## First profile against R3 and R2 (`quick_profile.py`)

| | R4 | R3 | R2 |
|---|---:|---:|---:|
| 1 s mid SD (ticks) | **6.17** | 4.49 | 3.80 |
| excess kurtosis | 129 | 213 | 232 |
| mid start → end | 9999.5 → 9554 | 9995.5 → 9872.5 | 9998.5 → 9690.5 |
| spread 1 tick / 2 ticks | 0.810 / 0.145 | 0.816 / 0.140 | 0.839 / 0.116 |
| trades/s, lots/s | 34.9, 1,285 | 34.0, 1,194 | 32.9, 1,167 |
| VR 2 / 5 / 10 s | 1.29 / 1.74 / **1.98** | 1.11 / 1.19 / 1.13 | 1.03 / 0.98 / 1.03 |
| VR 30 / 60 / 120 / 300 s | 1.64 / 1.41 / 1.35 / 1.09 | 0.91 / 0.86 / 0.86 / 0.78 | 1.13 / 1.16 / 1.33 / 1.78 |
| taker flow 1 s → next 1 s (corr) | **+0.210** | +0.145 | +0.050 |
| taker flow 10 s → next 10 s (corr) | −0.080 | −0.136 | +0.047 |

R4 is a strong short- and medium-horizon **momentum** tape: moves continue
over 2–60 s, peaking around 10 s. R3 reverted beyond 10 s. The R3 lesson
"don't fight 1–5 s momentum, expect reversion at 10–60 s" does not transfer;
re-test hold lengths and trend-aware exits on R4.

## Incumbents unchanged on R4 public (official engine, penalty 0)

| Strategy | R4 PnL | fit / eval PnL/s |
|---|---:|---:|
| U7 `r3_follower_u7_flow_deepfv.py` | **821,692** | 165.7 / 117.7 |
| U8 `r3_follower_u8.py` | 821,664 | 165.2 / 118.1 |
| U6 `r3_alpha_follower_p1_sw3_rlin0.py` | 749,685 | 154.1 / 105.5 |
| U4 `r3_alpha_follower_p1_sw3.py` | 642,720 | 124.4 / 95.6 |
| D1 `r3_informed_follower.py` | 623,085 | 121.2 / 92.3 |
| naive flow follower | 561,936 | 105.7 / 85.6 |
| colleague JumpBurst | 351,064 | 76.9 / 46.2 |
| aged maker (best config) | 122,485 | 28.7 / 14.9 |

The ranking from R3 holds on R4, and the trigger stack (U4 → U6 → U7) adds
+179k on R4. The R4 baseline upload is
`strategies/round_4/dataathletechamp/r4_u1_follower_u7_baseline.py`, a byte
copy of U7. Runner with the R4 tape:
`experiments/round_4/dataathletechamp/20261108-r4-runner-001/runner.py`.
