# R3 combined regime candidate (follower D1 + FV-gated maker M1 on one ledger)

Owner `dataathletechamp`, branch `r3-da-combined`, 2026-11-08 (02:16–02:45 CET). Experiment
`20261108-r3-w2-combined-001`. Status: **research candidate**. All results come from the official engine on
public or older tapes. Nothing was uploaded, merged or pushed. **Private B/C performance is UNKNOWN.**

## Question
Can one ±100 inventory ledger hold both engines, switched by a causal informed-flow regime state, and beat
each engine alone on the sum over R3 + R2 + R1 without losing R3 eval?
- The informed-flow follower is strong on R3 and negative on R1.
- The FV-gated touch maker is positive on R1 and about zero on R3.

## Strategy definition
File: `strategies/round_3/dataathletechamp/r3_combined_regime.py`, class `CombinedRegime`.

| version | sha256 | used for |
|---|---|---|
| final (committed) | `111fc83e955b2507745bbbac85bb49cef44568bc3e53b29b61d629bccc7394bc` | final checks, see "Official CLI" |
| v1 | `d1f202d03d10770a6e4b9b60053cc99ce607afd6cb0b211d7d3612090f180515` | the ladder, sensitivity and smoke runs |

- The two versions differ only by ruff formatting and a re-wrapped docstring. Their ASTs are identical apart from
  the module docstring.
- The final file reproduces v1 exactly: R3 CLI 269,288, and in the runner R2 63,328 and R1 40,363.
- Variants differ only in module constants, which the runner sets before instantiation.

**E1 follower ("D1").** Copied from the `follow_exec.py` final config: hold 5 s, 100 lots, touch exit 1 s.
- Signal A is computed per market taker order. Trades are grouped by `taker_order_id`; the sign comes from
  `book_side`. A fires when:
  - the order is the 4th or later consecutive same-sign taker order and filled ≥ 100; or
  - max − min fill price ≥ 2 ticks; or
  - filled ≥ 500.
- On A, the target becomes ±100. It is taken by IOC at the current opposite market touch, re-sent until done.
- A same-sign A extends the 5 s deadline. An opposite A flips by IOC through the touch ± 3.
- At the deadline, the follower joins the exit-side touch for 1 s, then exits by IOC at the touch ± 3.

**M1 maker.** Copied from `gated_maker.py` M1_q20_fv05.
- It quotes 20 lots per side at the market touch.
- It re-prices only when the touch moves away: it cancels, then re-sends after the cancel confirms.
- A side s (+1 bid, −1 ask) is cancelled, or not placed, while −s·FV ≥ 0.5 tick. FV is defined as:
  - FV = (max price of new bid limit inserts in the last 50 ms + min price of new ask inserts in the last 50 ms)/2 − market mid;
  - "new" means a market order id larger than every id seen before;
  - FV = 0 when either side has no new insert.
- Total inventory, including all pending orders, is capped at 80 while the maker quotes.

**Regime switch.**
- rate = EMA of the A count, time constant 120 s, as in the spectral/Hawkes screen. Its continuous-time form adds
  1 − e^(−1/120) per A and decays by e^(−Δt/120 s). It starts at 0.
- **High** (rate ≥ `RATE_HIGH` = 0.867 A/s): the follower may enter, extend and flip.
- **Low:** the follower opens nothing new, ignores same-sign extensions, and exits at its deadline.
- The maker quotes only while the follower is flat (idle) and the state is low. `MAKER_WHEN_FLAT_HIGH` also lets
  it quote when the follower is idle in the high state.

**Arbitration.**
- The follower has priority. Activating it cancels all maker quotes.
- The follower then owns the whole inventory until it is flat with no orders. It absorbs maker inventory: for
  example, maker +40 → follower buys 60.
- Every send of both engines is clipped so that |pos + pending buys| ≤ 100 and |pos − pending sells| ≤ 100,
  where pending means resting plus in-flight.
- Maker sends use the cap of 80 over the same totals.

**Flags.** `EXIT_FV_MODE`:
- `off` (default);
- `ioc`: a passive exit is placed only when FV does not oppose the exit side; otherwise the exit is an IOC at once;
- `wait`: keep the 1 s exit timer and join only while FV does not oppose.

`FOLLOW_LOW_EXTEND` (False) lets same-sign A extend an open position in the low state.

## Provenance
| item | value |
|---|---|
| R3 A | `data/round3/round3_public.csv` sha256 `1021586b92a3d9df…` |
| R2 public | `data/round2/round2_public.csv` `88ff641e962540c6…` |
| R1 | `data/round1/round1.csv` `362e8208be1eeec3…` |
| R0 | `data/round0/sample_v2.csv` `dd4e00e281abe50c…` |
| engine (unchanged) | `simulator.py` c37b2262…, `models.py` d66d6155…, `strategy.py` 464830f4…, `main.py` 8bf3f82e…, `__init__.py` 9fc736ff… |
| runner | `20261108-r3-wave-runner-001/runner.py` 07972771… (in-process official `ExchangeSimulator`: 5 ms, depth 20, max_position 100, max_potential 1000, penalty 10,000/s) |
| logic sources | `follow_exec.py` 11d19a09…, `gated_maker.py` v3 56249ed1… |
| windows | R3 and R2: fit = engine PnL curve at the last sample ≤ 2,400 s, eval = rest (3,600 s). R1: fit ≤ 4,800 s, eval 7,200 s. Blocks of 600 s. |
| main checkout | `7bbb8f2`; worktree base `2b50061` |

Commands (from the main checkout; `E` is the experiment dir in the worktree; `S` is the strategy file):
```
env -u VIRTUAL_ENV uv run --locked python experiments/round_3/dataathletechamp/20261108-r3-wave-runner-001/runner.py \
  --strategy $S --grid $E/grid_ladder.json --tapes r3,r2,r1 --out $E/ladder_v1 --workers 3
#   same with --grid $E/grid_sensitivity.json --out $E/sensitivity_v1 ; --grid $E/grid_smoke_r0.json --tapes r0
env -u VIRTUAL_ENV uv run --locked exchange-simulator --strategy $S --backtest data/round3/round3_public.csv --log-dir $E/cli_r3 --no-logs
env -u VIRTUAL_ENV uv run --locked python -m tools.preflight $S
```

Ladder overrides:
- C0: `MAKER_ENABLED=False`, `REGIME_ENABLED=False`
- C1: `FOLLOW_ENABLED=False`
- C2: the file defaults
- C3: `MAKER_WHEN_FLAT_HIGH=True`
- C4: `EXIT_FV_MODE='ioc'`

## Predeclared ladder: official engine, penalty 0 in every run
Acceptance rule: accept a step only if the R3+R2+R1 PnL sum improves and R3 eval falls by no more than 5 PnL/s.

| step | R3 fit/s | R3 eval/s | R3 PnL | R2 fit / eval /s | R2 PnL | R1 fit / eval /s | R1 PnL | R1 +blocks | sum | decision |
|---|---|---|---|---|---|---|---|---|---|---|
| C0 follower only | +39.3 | +48.8 | 270,035 | +5.3 / +3.7 | 26,175 | −15.0 / −17.5 | −197,905 | 0/20 | 98,305 | reference (reproduces D1 exactly) |
| C1 maker only | +2.9 | −2.9 | −3,348 | +5.5 / −1.1 | 9,436 | +5.5 / +6.4 | 72,447 | 20/20 | 78,535 | reference (reproduces M1 exactly) |
| **C2 regime switch** | **+41.5** | **+47.2** | **269,288** | **+11.8 / +9.7** | **63,328** | **+0.9 / +5.0** | **40,363** | 16/20 | **372,979** | **accept**: +274.7k vs C0; R3 eval −1.6/s |
| C3 = C2 + maker when flat in high | +41.4 | +47.1 | 268,952 | +11.7 / +9.8 | 63,220 | +0.9 / +5.0 | 40,463 | 16/20 | 372,635 | reject (−344) |
| C4 = C2 + FV-gated exit (ioc) | +41.2 | +47.3 | 269,036 | +10.7 / +9.5 | 59,832 | +0.8 / +4.9 | 39,061 | 16/20 | 367,929 | reject (−5,050) |

How C2 behaves (time shares):

| tape | regime high | follower on | maker quoting | follower lots | maker lots | A ignored in low | 600 s blocks + | worst DD |
|---|---|---|---|---|---|---|---|---|
| R3 | 77.5% | 80.1% | 18.9% | 364,509 | 35,249 | 1,033 | 9/10 | −13.0k |
| R2 | 55.7% | 59.4% | 39.0% | 290,973 | 73,271 | 2,009 | 7/10 | −19.2k |
| R1 | 7.8% | 10.5% | 87.4% | 86,391 | 296,371 | 8,382 | 16/20 | −7.6k |

Max exposure including pending was 100 in every run (80 in C1).

- C2 keeps R3 and roughly doubles R2: +63k against +26k for the follower alone and +9k for the maker alone.
- C2 turns R1 from −198k into +40k.
- On R1, the follower's episodes in the 8% high time, plus the maker downtime they cause, cost ≈ 32k against the
  maker alone.
- C3 barely changes anything: the follower is flat in the high state very rarely.
- C4's IOC fallback pays the spread exactly when FV says the exit side will fill anyway.

## Post-hoc sensitivity (selected after the ladder; not used to set defaults)
| variant | R3 fit/s | R3 eval/s | R3 PnL | R2 PnL | R1 PnL (fit/eval /s) | sum |
|---|---|---|---|---|---|---|
| RATE_HIGH 0.80 | +39.4 | +47.5 | 265,561 | 35,660 | −37,293 (−5.2/−1.7) | 263,928 |
| RATE_HIGH 0.867 (C2) | +41.5 | +47.2 | 269,288 | 63,328 | 40,363 (+0.9/+5.0) | 372,979 |
| RATE_HIGH 0.95 | +40.4 | +41.6 | 246,777 | 75,876 | 65,582 (+4.0/+6.4) | 388,235 |
| RATE_HIGH 1.005 | +28.8 | +38.6 | 207,961 | 65,464 | 71,647 (+5.3/+6.4) | 345,072 |
| FOLLOW_LOW_EXTEND | +42.1 | +48.2 | 274,794 | 61,904 | 40,167 | 376,865 |
| EXIT_FV_MODE wait | +41.7 | +47.8 | 271,985 | 61,982 | 39,848 | 373,815 |

**The threshold is knife-edge.**
- R1 goes from −37k at 0.80, to +40k at 0.867, to +66k at 0.95, to +72k at 1.005.
- R3 goes from 266k, to 269k, to 247k, to 208k over the same thresholds.
- 0.95 has the best sum, but R3 eval drops by 5.6/s against C2 (7.2/s against C0), which fails the R3 rule.

Low-extend (+3.9k) and wait-mode exits (+0.8k) gain only on R3; R2 and R1 fall, which is within noise. Not adopted.

**RATE_TAU_S sweep.** Final file, RATE_HIGH 0.867. Selected after the ladder; the default is not changed.

| RATE_TAU_S | R3 PnL (fit / eval /s) | R2 PnL | R1 PnL | sum |
|---|---|---|---|---|
| 60 | 252,194 (+39.8 / +43.5) | 30,944 | 15,105 | 298,243 |
| 120 (C2) | 269,288 (+41.5 / +47.2) | 63,328 | 40,363 | 372,979 |
| 180 | 266,959 (+38.7 / +48.4) | 62,204 | 52,228 | 381,391 |
| 240 | 275,978 (+41.8 / +48.8) | 56,669 | 59,216 | 391,863 |
| 360 | 271,480 (+39.9 / +48.8) | 58,153 | 65,351 | 394,984 |

- A slower EMA monotonically reduces false gate openings on R1: 15k → 65k.
- R3 is flat within noise.
- R2 peaks at 120–180 and loses 5–7k at 240–360 because the gate lags real minute-scale regime changes.
- RATE_TAU_S 240 would pass the ladder rule (+18.9k sum; R3 eval +1.6/s). It was chosen in-sample on these same
  three tapes, so it is a candidate for a predeclared check, not the default.

## Maker-only validation probe (C1 as a standalone file)
File: `strategies/round_3/dataathletechamp/r3_combined_maker_probe.py`, class `CombinedMakerProbe`.
sha256: `627769c917fddfcdcd887b86bf79f17f3ca7121ac3aff2ce2daccf8b12c68da0`.

It is identical to the regime file except for three things:
- `FOLLOW_ENABLED = False`, so no follower logic runs and the regime switch has no effect;
- the class name;
- the docstring header.

Results:
- **Runner** (official engine):
  - R3 −3,348 (+2.9 / −2.9 /s, 5/10 blocks);
  - R2 +9,436 (+5.5 / −1.1);
  - R1 +72,447 (+5.5 / +6.4, 20/20 blocks);
  - penalty 0. These match the C1 row exactly.
- **CLI on R3 A:**
  - pnl −3,348; fills 11,409; traded 213,105; penalty 0; final inventory +43;
  - |inv| q50 / q95 = 40 / 80;
  - pnl_se 15,899;
  - 26.4 s wall.
- **Checks:** preflight passes, and ruff check and format pass.
- **Purpose:** a validation-upload probe of whether FV-gated resting quotes earn on the B tape. Its R3 public
  expectation is about 0.

## Official CLI, preflight, runtime
- **CLI on R3 A** (defaults = C2): pnl **269,288**, identical to the runner, for both v1 and the final file.
  - fills 3,872; traded 399,758; breach_penalty 0; final inventory +100;
  - |inv| q50 / q95 = 100 / 100;
  - pnl_se 31,306 (one arm, not a paired SE).
- **CLI robustness runs.**
  - R0 sample_v2: 64,729. The gate never opens; the maker alone gave 10/10 positive blocks in the runner.
  - R1: 40,363.
  - None of the 36 runs on R0 / R1 / R2 / R3 raised an exception: 33 runner runs (3 R0 smoke, 15 ladder,
    15 sensitivity) plus 3 CLI runs.
- **Preflight:** "Local conservative preflight passed; server sandbox validation is still required." This holds
  for both versions.
- **Lint:** `ruff check` and `ruff format --check` pass on the final file.
- **Runtime** (CLI wall time with 3 concurrent processes, 10-core laptop):
  - R3: 33.9 s (user 26.0 s); the final file took 29.8 s (user 25.0 s);
  - R0: 32.9 s;
  - R1 (12,000 s): 55.4 s;
  - runner in-process: 18–44 s per run.

  This is far below the 15-minute server budget, but it is not a server measurement.

## Recommended defaults
Use the file as committed, which is C2:
- `RATE_HIGH=0.867`, `RATE_TAU_S=120`;
- `FOLLOW_HOLD_S=5`, `FOLLOW_LOTS=100`, `EXIT_MODE='touch'`, `EXIT_TOUCH_WAIT_S=1`, `EXIT_FV_MODE='off'`;
- `MAKER_Q=20`, `MAKER_CAP=80`, `FV_CANCEL=0.5`, `FV_WIN_US=50,000`;
- `MAKER_WHEN_FLAT_HIGH=False`, `FOLLOW_LOW_EXTEND=False`.

## Limitations
- **Data.** These are public tapes: one 6,000 s R3 tape with one chronological split. R2 and R1 come from older
  rounds. The tape is non-reactive, and the B/C participant mix is unknown.
- **Noise.** The deltas between C2, C3, C4, low-extend and wait are ≤ 6k, which is within noise. There is no
  paired-delta SE.
- **Threshold.**
  - 0.867 is the R3-fit tercile cut from a screen. Typical R1 and R2 A rates lie close to it.
  - A private tape slightly more active than R1 would reopen the follower in a losing state; RATE_HIGH 0.80 on R1
    gives −37k.
  - The A-definition thresholds came from full-tape fingerprint tables, so there is mild selection.
- **Gate start-up.** The EMA starts at 0, so the follower stays off for the first few minutes while the maker quotes.
- **Gate design.** There is no hysteresis.
- **Validation.** The website's static sandbox checker was not run; the local preflight is conservative only.
- **Research hook.** A `diagnostics()` method holds counters only, for research runners. It has no file or system access.
- **Next test.** The next lever for the knife-edge is a hysteresis or second-feature gate (rate AND rv, see the
  regime notes), or a slower RATE_TAU_S. Neither is adopted here.
- **Not implemented.** E2 stale-snipe (one-sided jump ≥ 2 ticks → IOC the unchanged side, hold 2 s, only when
  the follower is flat) was not implemented in this session.
- **Validation context** (coordinator report, not reproduced locally): the plain D1 follower (R3 public 270,035)
  scored +272,176 on the 12,000 s validation tape B (≈ 23/s against 45/s on public) with penalty 0.
  Public-tape PnL/s therefore overstates B for the follower.
