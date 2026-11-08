# R3 informed-follower submission candidate (D1, hold 5 s, join-touch exit)

Experiment `20261108-r3-w2-follower-001` (raw outputs stay in `experiments/`, uncommitted).
Official engine only (in-process runner = CLI to the unit). Public tapes only; private B/C unknown.

## Files

| file | sha256 | flags |
|---|---|---|
| `strategies/round_3/dataathletechamp/r3_informed_follower.py` | `1d3f2506851c0b2653197981f46fb95d3e10d5090bca6366cfdd7a09c332303a` | all robustness flags off (reference D1) |
| `strategies/round_3/dataathletechamp/r3_informed_follower_gate0867.py` | `d4cd5fd03c0c8e702fff33b819b3edfaaf35880e97b49a17f5a1bcb435fb8de3` | `REGIME_GATE_MIN_A_PER_S=0.867`, `CANCEL_STALE_EXIT=True`; otherwise identical |

The grid runs used pre-lint bytes:

- base file: `407b033e…`;
- gated file: `411573d9…`.

The pre-lint and final bytes differ only by a docstring re-wrap and one line break in one expression.
The final bytes re-verified by CLI to the unit:

| tape | base | gated |
|---|---|---|
| R3 | 270,035 | 243,640 |
| R2 | 26,175 | 31,935 |

## Definition

- **Signal A.** For each market taker order, trades are grouped by consecutive `taker_order_id` within
  one callback. Our own taker trades are excluded. Direction comes from the book side that was hit. A
  fires if any of these holds:
  - run position ≥ 4 among consecutive same-direction taker orders and filled ≥ 100;
  - first-to-last fill price span ≥ 2 ticks;
  - filled ≥ 500.
- **D1 state machine.**
  - A from flat sets the target to ±`MAX_LOTS` (100). The entry is an IOC at the current
    market-owned touch.
  - A same-direction A extends the 5 s hold. An opposite A flips with an IOC at touch ± 3 ticks.
  - At the deadline the strategy joins the exit-side touch for 1 s, then sends an IOC at touch ± 3.
  - Position plus in-flight and resting orders is clamped to ±`MAX_LOTS` ≤ 100.
- **Port check.** This is a line-for-line port of `follow_exec.py` (`11d19a09…`, config `touch_h5_w1`)
  of `20261108-r3-follow-exit-optimization-001`.
- **Parameters.** All parameters are module-level constants read at call time.
- **`REGIME_GATE_MIN_A_PER_S`** (default 0 = off).
  - Rate = A orders in the last `REGIME_GATE_WINDOW_S` = 120 s divided by 120. This estimate is
    conservative, so the gate stays closed for roughly the first 100 s.
  - While the rate is below the threshold:
    - no entry from flat;
    - no hold extension;
    - an opposite A closes the position instead of flipping.
- **`STRONG_FLIP_ONLY`** (False). When True, the strategy flips only on a span ≥ 2 or fill ≥ 500 and
  ignores weaker opposite A.
- **`CANCEL_STALE_EXIT`** (False). When True, a resting touch-exit order is cancelled once the
  target is re-established. The reference D1 leaves it resting.
- **`MAX_LOTS`** (100). The value is clamped to the range 0–100.

## Provenance and reproduction

**Data** (sha256 prefixes):

| tape | file | sha256 prefix |
|---|---|---|
| R3 A | `data/round3/round3_public.csv` | `1021586b92a3d9df` |
| R2 | `round2_public.csv` | `88ff641e962540c6` |
| R1 | `round1.csv` | `362e8208be1eeec3` |
| R0 | `sample_v2.csv` | `dd4e00e281abe50c` |

**Engine (unchanged).**

| file | sha256 prefix |
|---|---|
| `simulator.py` | `c37b2262186f977d` |
| `models.py` | `d66d6155376fae92` |
| `strategy.py` | `464830f41c071531` |
| `main.py` | `8bf3f82e9d5f72c4` |

Configuration: 5 ms latency, depth 20, position limit ±100, penalty 10,000 per second.

**Evaluation windows.** Fit is t < 2400 s and eval is the rest. No parameter was fitted here:
- the A thresholds and the hold come from earlier experiments;
- the 0.867 gate is the R3-fit-window tercile from `20261108-r3-spectral-hawkes-regime-001`.

**Commands.** Run from the main checkout. The runner is `20261108-r3-wave-runner-001/runner.py`
(`0797277195836…`); the grids are in the experiment folder.

```
env -u VIRTUAL_ENV uv run --locked python -m tools.preflight <file>
env -u VIRTUAL_ENV uv run --locked python experiments/round_3/dataathletechamp/20261108-r3-wave-runner-001/runner.py \
  --strategy <abs file> --grid <abs grid.json> --tapes r3,r2,r1 --out <abs out> --workers 3
env -u VIRTUAL_ENV uv run --locked exchange-simulator --strategy <abs file> \
  --backtest data/round3/round3_public.csv --log-dir <abs out>/cli --no-logs
```

## Results

PnL is in currency units. "fit / eval" is PnL per second, with fit = t < 2400 s; for R1 that is the
first 2400 s of its 12,000 s.

| variant | R3 PnL | R3 fit / eval | R2 PnL | R2 fit / eval | R1 PnL | R1 fit / eval | R0 v2 PnL |
|---|---|---|---|---|---|---|---|
| base (file defaults) | **270,035** | 39.3 / 48.8 | 26,175 | 5.3 / 3.7 | −197,905 | −15.0 / −17.5 | −227,385 |
| gate 0.80 | 249,330 | 35.9 / 45.4 | 27,205 | 4.8 / 4.4 | −93,862 | −8.0 / −7.7 | 0 |
| gate 0.867 | 243,326 | 34.5 / 44.6 | 31,835 | 5.5 / 5.2 | −31,587 | −4.4 / −1.5 | 0 |
| gate 0.95 | 225,398 | 30.4 / 42.4 | 30,980 | 7.3 / 3.7 | −14,305 | −2.3 / −0.4 | 0 |
| strong flip only | 231,935 | 30.7 / 44.0 | 10,700 | 7.2 / −1.8 | −167,916 | −13.0 / −14.7 | — |
| strong flip + gate 0.867 | 202,440 | 26.7 / 38.4 | 9,093 | 7.2 / −2.3 | −24,390 | −3.6 / −1.0 | — |
| cancel stale exit | 270,229 | 39.4 / 48.8 | 26,384 | 5.3 / 3.8 | −197,585 | −15.0 / −17.4 | — |
| MAX_LOTS 50 | 149,744 | 21.7 / 27.1 | 25,922 | 3.2 / 5.1 | −87,677 | −6.5 / −7.8 | — |
| **gate 0.867 + cancel stale (`_gate0867` file)** | 243,640 | 34.6 / 44.6 | 31,935 | 5.5 / 5.2 | −31,555 | −4.4 / −1.5 | — |

Run-level facts:

- **Penalty and exposure.** Penalty was 0 in every run. Maximum exposure including pending orders was
  ≤ `MAX_LOTS`.
- **Gate 0.867 closed-time share.** The gate was closed for this share of each tape: R3 34%, R2 51%,
  R1 85%, R0 100%. On R0 it never opens.

Verdicts:

- **Reproduction is exact.** R3 270,035.0 and R2 26,175.0 equal the reference harness.
- **Gate fails the pre-registered rule** (regime experiment H1: R3 eval segment > 5% worse). It is
  better on R2 at every threshold. On R3 the eval change is:

  | threshold | R3 eval change |
  |---|---|
  | 0.80 | −7.1% |
  | 0.867 | −8.6% |
  | 0.95 | −13.2% |

  It is an insurance trade:

  | threshold | R3 change | R2 change | R1 change | R0 change |
  |---|---|---|---|---|
  | 0.867 | −26.7k (90.1% of base) | +5.7k | +166.3k | +227.4k |
- **Strong flip only is rejected.** R3 −38.1k, R2 −15.5k; only R1 improves (+30.0k).
- **Cancel stale exit is a deterministic fix with negligible effect.** R3 +194, R2 +209, R1 +320.

## Checks

- **Official CLI.** Every CLI result equals the runner, with penalty 0 throughout.

  | file | tape | CLI result |
  |---|---|---|
  | base | R3 | pnl 270,035.00; fills 2,367; volume 444,620; 12.8 s wall |
  | base | R1 | −197,905.00 |
  | gated | R3 | 243,640.00 |
  | gated | R1 | −31,555.00 |

  Command: `exchange-simulator --strategy <file> --backtest <tape> --no-logs`.
- **`tools.preflight`.** Both files pass. Both files are also clean under `ruff check` and
  `ruff format --check` with the project config.
- **Synthetic edge states.** The test covered empty, one-sided and crossed books, a user-only top of
  book, tiny prices, unknown or duplicate private events, `MAX_LOTS` 0 and 500, and all flags. There
  was no exception, and exposure stayed ≤ 100 over 6 × 20,000 callbacks.
- **Runtime.** With 3 concurrent processes:
  - R3: 13–15 s;
  - R2: 10–14 s;
  - R1 (12,000 s): 21–25 s, including 21.5–22.4 s via the CLI.

  That is about 25 s per 12,000 s tape, far below 300 s.

## Recommendation and limitations

- **If B/C are stationary with A.** Keep the file defaults (ungated): they give the highest public R3
  PnL.
- **If B/C may contain R1/R2-like low-informed flow.** Upload `_gate0867`: about −10% on A in
  exchange for cutting the R1/R0 losses.
  - This is a judgment against a rule the gate failed, not a passed test.
  - Owner decision.
- **Data limits.**
  - The evidence is one A tape, one chronological split and a non-reactive tape.
  - The 0.867 threshold was fitted on the R3 fit window.
  - The R1 and R0 tapes come from earlier-round generators.
- **Not yet validated.** The file has not been through the website sandbox, and private PnL is not
  implied.
