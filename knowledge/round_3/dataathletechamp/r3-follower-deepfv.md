# R3 follower + deep insert-FV flow trigger (TRIG1) — official-engine grid

Experiment `20261108-r3-w7-deepfv-001` (branch `r3-da-deepfv`, base commit 1e6fb95).
Strategy: `strategies/round_3/dataathletechamp/r3_follower_deepfv.py` = U4
(`r3_alpha_follower_p1_sw3.py`, sha256 e4dfd2ce…574f) + flag `TRIG1` and `TRIG1_*` knobs.
Data: R3 public `round3_public.csv` sha256 1021586b92a3…, R2 public `round2_public.csv` 88ff641e9625…,
R1 `round1.csv` (info only). Official simulator unchanged (`simulator.py` c37b2262186f…).
Runner: `experiments/round_3/dataathletechamp/20261108-r3-wave-runner-001/runner.py` (official engine,
max_position 100, potential 1000, 5 ms accept delay, depth 20); fit window t < 2,400 s, eval t >= 2,400 s.

## Question and mechanism

The oracle-gap study (`r3-oracle-gap.md`, experiment `20261108-r3-w6-oracle-gap-001`) found that 57% of the
gap to perfect foresight comes from late entry (about 0.3 s). It also found that new resting inserts carry information
only when you look at full visible depth. The ±2.5-tick window that U4's `FV_DEPTH = 2` features use has an IC of about 0.
TRIG1 (long; short mirrored) fires when two conditions hold over the last `TRIG1_WIN_MS` = 200 ms:
- net market-taker fill volume (taker buy +) >= `TRIG1_FLOW`;
- the mean of (new resting market insert price − mid before the event) is >= `TRIG1_FV` ticks. This uses both sides,
  unweighted, over all visible depth.

New inserts are market order ids above a running max id; the deep scan keeps its own max id, so U4 features are
untouched. A side is scanned only if its first view changed or its length grew (one row per snapshot), which costs
+8 s per R3 run. The trigger is edge-triggered and is handled exactly like an A event of that sign: entry, 5 s hold
extension or flip. `TRIG1_GATED` decides whether flips must pass the P1 alpha gate. `TRIG1 = False` reproduces U4
exactly: R3 330,208 / R2 109,317 / R1 −112,045.

## Predeclared grid and rule

The grid was base plus (flow, FV) = (300, 1.0), (300, 0.5) and (200, 1.0), run gated, with ungated tried for the
best cell. Ungated was in fact run for all three cells. A cell is accepted only if all of these hold:
- R3 > 330,208;
- R3 eval/s >= 56.3;
- R2 >= 87,000;
- a neighbouring cell keeps >= 0.5 of the R3 gain.

| variant | R3 PnL | fit/s | eval/s | R2 PnL | R2 eval/s | R3 lots | TRIG1 fires R3 (entry/flip/ext/gate-blocked) |
|---|---:|---:|---:|---:|---:|---:|---|
| base (U4) | 330,208 | 51.6 | 57.3 | 109,317 | 22.6 | 301,670 | — |
| 300 / 1.0 gated | 355,860 | 57.1 | 60.8 | 88,944 | 16.9 | 324,544 | 4,090 (13/217/3,353/507) |
| **300 / 0.5 gated (default)** | **363,045** | 55.4 | **63.9** | **97,459** | 15.3 | 349,900 | 7,392 (25/448/5,566/1,353) |
| 200 / 1.0 gated | 350,572 | 56.1 | 60.0 | 88,805 | 15.2 | 335,672 | 5,283 (20/292/4,180/791) |
| 300 / 1.0 ungated | 369,216 | 57.8 | 64.0 | 119,127 | 23.5 | 385,544 | 4,109 (10/538/3,561/0) |
| 300 / 0.5 ungated | 294,624 | 46.0 | 51.2 | 162,533 | 31.4 | 503,858 | 7,383 (15/1,258/6,110/0) |
| 200 / 1.0 ungated | 360,640 | 55.1 | 63.5 | 103,975 | 21.3 | 416,672 | 5,300 (14/732/4,554/0) |

All cells had breach penalty 0. R3 600 s blocks were positive in 10/10 for every cell except 300 / 0.5 ungated
(9/10). R1, run once for information: base −112,045 (2/20 blocks positive), default −117,035 (1/20), 300 / 1.0 ungated −110,585 (2/20).
The follower fails in R1's regime with or without TRIG1.

## Verdict

**ACCEPT, default 300 / 0.5 gated.** The predeclared procedure picks the best gated cell on R3, which is 300 / 0.5.
Its ungated version fails, with R3 at 294,624.
- R3: 363,045 (+32,837, +9.9%); eval/s 63.9 (+6.6).
- R2: 97,459, which passes the 87,000 floor.
- Neighbours: 300 / 1.0 gated keeps 0.78 of the gain and 200 / 1.0 gated keeps 0.62.
- Official CLI on R3 with the committed default: pnl **363,045.00**, breach_penalty 0, the same as the runner.
- `tools.preflight` passed.

Caveats, stated honestly:
- Gated TRIG1 lowers R2 in **all three** cells (−11.9k … −20.5k; R2 eval/s 15–17 vs 22.6).
- Most fires are hold extensions, not earlier flips. The gate blocks 1,353 TRIG1 flips on R3.
- 300 / 1.0 ungated was better on both public tapes (369,216 / 119,127). It was not the predeclared pick, and its FV
  neighbour (0.5 ungated) loses 35.6k on R3, so it stays a flag setting
  (`TRIG1_FV = 1.0`, `TRIG1_GATED = False`).
- The thresholds come from an event study on the full R3 public tape, so R3 (both halves) is in-sample. R2 is the
  only replication, and on R2 the default is worse than U4.

Public PnL is not private PnL. Server validation is still needed before any upload decision.

## Reproduce (from MAIN)

```bash
W=experiments/round_3/dataathletechamp/worktrees/deepfv; E=$W/experiments/round_3/dataathletechamp/20261108-r3-w7-deepfv-001
env -u VIRTUAL_ENV uv run --locked python experiments/round_3/dataathletechamp/20261108-r3-wave-runner-001/runner.py \
  --strategy $W/strategies/round_3/dataathletechamp/r3_follower_deepfv.py --grid $E/grid.json --tapes r3,r2 --out $E/out --workers 2
env -u VIRTUAL_ENV uv run --locked python -m simulator.main --backtest data/round3/round3_public.csv \
  --strategy $W/strategies/round_3/dataathletechamp/r3_follower_deepfv.py --log-dir $E/cli_r3 --no-logs
env -u VIRTUAL_ENV uv run --locked python -m tools.preflight $W/strategies/round_3/dataathletechamp/r3_follower_deepfv.py
```

The grid ran on the same code with `TRIG1 = False` as the file default (snapshot `r3_follower_deepfv_gridrun.py`,
sha256 0cdb01d25793…). The committed file only changes the defaults (`TRIG1 = True`, `TRIG1_FV = 0.5`) and the first
docstring line. Committed file sha256 7b03aff42159…8fba (30,746 bytes). `ruff check` reports only E501 long lines; the
base has the same kind (21 in the base, 25 here).
