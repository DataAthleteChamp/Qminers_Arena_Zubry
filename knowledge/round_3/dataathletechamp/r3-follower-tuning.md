# R3 follower tuning: two-stage, plateau-seeking sweep inside the combined regime file

Owner `dataathletechamp`, branch `r3-da-follower-tune`, 2026-11-08 (02:44–03:03 CET). Experiment
`20261108-r3-w4-follower-tune-001` (gitignored; plan, grids, analysis scripts, runner outputs and CLI logs
stay there). Status: **research candidate, not uploaded**. All numbers come from the official engine on public
tapes. **Validation B / private C performance of the tuned file is UNKNOWN until the B upload.**

## Result in one paragraph
Under the owner's final objective (Round 3 only), exactly one change passed: **`A_SWEEP` 2 → 3**, with the
regime gate and the maker switched off. The resulting file `strategies/round_3/dataathletechamp/r3_combined_tuned.py`
is the plain D1 informed follower in which a taker order whose fills span exactly 2 ticks no longer counts
as signal A. On the R3 public tape it makes **301,177 vs 270,035** for the plain follower (+31,142). Both
windows improve: fit +39.3 → +47.2 /s and eval (t ≥ 2,400 s) +48.8 → +52.2 /s. It is better in **10/10** paired
600 s blocks. R2 rises from 26,175 to 106,317; R1 stays −197,905, unchanged from the plain follower. No gate
setting improved R3. The selection used the same public tape, so the size of the gain is optimistic.
For reference, the v1 metric J (R3 eval/s + R2/s) of the final file is 69.93, against 57.71 for C2 and 53.16
for the plain follower.

## Provenance
| item | value |
|---|---|
| base file | `r3_combined_regime.py` sha256 `111fc83e955b2507745bbbac85bb49cef44568bc3e53b29b61d629bccc7394bc` |
| **final file** | `r3_combined_tuned.py` sha256 **`c8ef8b26b4287022a83d61f0e2d1e750ac292988a7e47e5f3a8ad4c45176f85a`** (18,488 B) |
| R3 A | `data/round3/round3_public.csv` `1021586b92a3d9df…` (6,000 s) |
| R2 / R1 | `round2_public.csv` `88ff641e962540c6…` / `round1.csv` `362e8208be1eeec3…` |
| engine (unchanged) | `simulator.py` c37b2262…, `models.py` d66d6155…, `strategy.py` 464830f4…, `main.py` 8bf3f82e…, `__init__.py` 9fc736ff… |
| runner | `20261108-r3-wave-runner-001/runner.py` 07972771… (in-process official `ExchangeSimulator`, 5 ms, depth 20, ±100, max potential 1000, penalty 10,000/s); constants set as module globals |
| windows | R3/R2 fit = PnL curve at the last sample ≤ 2,400 s; eval = total − fit, divided by 3,600 s; 600 s blocks |
| main checkout | `03e573d` |

## Procedure (predeclared in the experiment's `plan.md` before each batch; file mtimes are the record)
Grid (base in brackets): A_RUN_MIN {3,[4],5}, A_FILL_MIN {50,[100],200}, A_SWEEP {[2],3}, A_BIG {300,[500],1000},
FOLLOW_HOLD_S {3,[5],8}, RATE_HIGH {0.80,[0.867],0.95}, RATE_TAU_S {[120],240}.
- Stage 1 varies one parameter at a time; there is no full product.
- Stage 2 combines the 2–3 best passing changes: all pairs plus the triple.
- **Plateau rule**: every adjacent in-grid value must keep at least 70% of the candidate's objective. For an
  edge value, the only neighbour is the base.

**v1 (the original task), plan written 02:45:56, first run 02:46:00.**
- Reference: file defaults C2 (gate + maker).
- J = PnL_R3(t ≥ 2,400 s)/3,600 + PnL_R2/6,000.
- R3 fit had to stay ≥ 90% of base, and R1 > 0 for the finalists.

**v2 (owner change at ≈02:55, plan written 02:55:44, first run 02:55:51).**
- Only Round 3 matters: B and C come from the R3 setup.
- On B, the gated follower made 258,688 against 272,176 ungated; the maker probe lost 659,826.
- Reference BASE_P = plain follower = `MAKER_ENABLED=False`, `REGIME_ENABLED=False` (ladder C0).
- Objective O = R3 total PnL.
- Honesty check: R3 eval/s may fall by at most 2.0 /s.
- The gate is turned on only if it raises R3 eval/s **and** O, and its neighbours hold.
- R2 and R1 are reported but are not constraints.

## v2 stage 1: plain follower base (r3 decides; r2 for information)
| variant | R3 PnL | ΔO | R3 fit/s | R3 eval/s (Δ) | R3 +blocks | plateau | R2 PnL | verdict |
|---|---|---|---|---|---|---|---|---|
| BASE_P (gate off, maker off) | 270,035 | 0 | +39.3 | +48.8 | 9/10 | – | 26,175 | reference |
| A_RUN_MIN 3 | 269,959 | −76 | +38.7 | +49.2 (+0.42) | 8/10 | 1.00 | 11,179 | no |
| A_RUN_MIN 5 | 240,685 | −29,350 | +34.4 | +43.9 (−4.88) | 9/10 | 1.12 | 6,662 | no |
| A_FILL_MIN 50 | 253,262 | −16,773 | +36.6 | +45.9 (−2.87) | 8/10 | 1.07 | −17,867 | no |
| A_FILL_MIN 200 | 257,173 | −12,862 | +35.7 | +47.6 (−1.15) | 9/10 | 1.05 | 44,159 | no |
| **A_SWEEP 3** | **301,177** | **+31,142** | **+47.2** | **+52.2 (+3.41)** | 9/10 | 0.90 ok | 106,317 | **PASS** |
| A_BIG 300 | 231,939 | −38,096 | +33.2 | +42.3 (−6.53) | 8/10 | 1.16 | −18,321 | no |
| A_BIG 1000 | 217,418 | −52,617 | +31.0 | +39.7 (−9.09) | 8/10 | 1.24 | 20,344 | no |
| FOLLOW_HOLD_S 3 | 252,127 | −17,908 | +32.0 | +48.7 (−0.13) | 9/10 | 1.07 | −17,459 | no |
| FOLLOW_HOLD_S 8 | 257,666 | −12,369 | +39.1 | +45.5 (−3.32) | 9/10 | 1.05 | 36,982 | no |
| gate 0.80 / τ120 | 269,126 | −909 | +39.1 | +48.7 (−0.10) | 9/10 | 1.00 | 29,495 | gate no |
| gate 0.867 / τ120 | 268,763 | −1,272 | +38.5 | +49.0 (+0.18) | 9/10 | 0.87 | 37,333 | gate no (O falls) |
| gate 0.867 / τ240 | 267,162 | −2,873 | +38.1 | +48.8 (0.00) | 9/10 | 1.01 | 33,133 | gate no |
| gate 0.95 / τ120 | 232,858 | −37,177 | +34.9 | +41.4 (−7.35) | 8/10 | 1.15 | 50,942 | gate no |

All gate rows use maker off and penalty 0.

**Decision.** One change passes, so there are no stage-2 combinations. FINAL v2 = BASE_P + `A_SWEEP=3`, and the gate stays off.

**Paired 600 s blocks (R3), A_SWEEP 3 minus BASE_P:** +600, +7,138, +2,365, +8,768, +2,031, +1,187,
+4,581, +1,594, +1,483, +1,395.
- The candidate is better in **10/10** blocks. The largest block carries 28% of the gain.
- Fit: 94,354 → 113,225. Eval: 175,681 → 187,952.
- Worst drawdown: −13.5k → −12.2k.

On R2 (information only), the candidate is better in 7/10 blocks, but one block carries +53.2k of the +80.1k gain.

**Post-hoc neighbourhood around FINAL v2.** This was declared before running, is informational, and did not change the selection.

| variant (A_SWEEP 3 +) | R3 PnL | ratio to FINAL | eval/s |
|---|---|---|---|
| A_SWEEP 4 instead of 3 | 300,120 | 1.00 | +51.3 |
| A_RUN_MIN 3 / 5 | 307,067 / 270,659 | 1.02 / 0.90 | +54.2 / +46.5 |
| A_FILL_MIN 50 / 200 | 286,518 / 287,587 | 0.95 / 0.96 | +50.6 / +50.6 |
| A_BIG 300 / 1000 | 269,562 / 249,687 | 0.90 / 0.83 | +47.7 / +43.4 |
| FOLLOW_HOLD_S 3 / 8 | 283,205 / 288,222 | 0.94 / 0.96 | +52.6 / +48.6 |

- No neighbour collapses: all stay ≥ 0.83, and A_SWEEP 4 is flat.
- A_RUN_MIN 3 together with A_SWEEP 3 is +5.9k better. It is **not adopted**: A_RUN_MIN 3 failed alone in stage 1,
  it cut R2 from 26k to 11k, and it was not predeclared.

## Final file checks (`r3_combined_tuned.py`, c8ef8b26…)
**Diff against the base:** 3 constants plus a docstring line.
- `A_SWEEP = 3`
- `MAKER_ENABLED = False`
- `REGIME_ENABLED = False`

The maker and gate code stays behind its flags.

**Official CLI on R3 A:**
- pnl **301,177**, identical to the runner;
- fills 2,190; traded 410,220; breach_penalty 0; final inventory +100;
- |inv| q50 / q95 = 100 / 100;
- pnl_se 31,634 (one arm, not a paired SE);
- wall time 23.3 s (user 22.6 s).

**Runner:**
- R3 301,177;
- R2 106,317 (8/10 blocks positive);
- R1 **−197,905** (0/20 blocks positive). This is identical to the plain follower: A_SWEEP has no effect on R1.
  R1 is a previous-round generator and no longer a constraint.

**Checks:**
- `tools.preflight`: "Local conservative preflight passed; server sandbox validation is still required."
- `ruff check` and `ruff format --check` pass.

## Mechanism (diagnostic counters, R3)
`A_SWEEP=3` drops taker orders whose fills span exactly 2 ticks from signal A.
- A signals: 6,119 → 5,566 (−9%).
- Flips: 2,151 → 1,974.
- Follower lots: 444,620 → 410,220.
- Fills: 2,367 → 2,190.

The removed triggers were, on average, whipsaw flips that pay the spread (IOC through the touch ± 3). The gain is
spread over the whole tape rather than one episode. On R1, 2-tick sweeps almost never fire (A 9,466 vs 9,454 in the
gated runs), so nothing changes there.

## v1 record: superseded objective, kept for reference
Reference C2: R3 269,288 (fit +41.5 / eval +47.2 /s), R2 63,328, J 57.71. Every run had penalty 0.

| variant | R3 fit/s | R3 eval/s | R3 PnL | R2 PnL | J | v1 verdict |
|---|---|---|---|---|---|---|
| A_RUN_MIN 3 / 5 | +37.4 / +24.5 | +49.2 / +31.2 | 266,982 / 171,128 | 12,094 / 46,494 | 51.23 / 38.93 | no / no |
| A_FILL_MIN 50 / 200 | +35.8 / +25.2 | +45.9 / +28.4 | 251,164 / 162,527 | −16,599 / 58,019 | 43.16 / 38.03 | no / no |
| A_SWEEP 3 | +46.6 | +47.3 | 282,118 | 127,299 | 68.53 | PASS |
| A_BIG 300 / 1000 | +33.5 / +20.2 | +42.3 / +27.1 | 232,562 / 145,847 | −18,147 / 23,157 | 39.25 / 30.91 | no / no |
| FOLLOW_HOLD_S 3 / 8 | +36.6 / +41.3 | +48.1 / +47.9 | 260,945 / 271,799 | 40,834 / 70,338 | 54.87 / 59.67 | no / PASS |
| RATE_HIGH 0.80 / 0.95 | +39.4 / +40.4 | +47.5 / +41.6 | 265,561 / 246,777 | 35,660 / 75,876 | 53.42 / 54.25 | no / no |
| RATE_TAU_S 240 | +41.8 | +48.8 | 275,978 | 56,669 | 58.25 | PASS |
| sweep3 + hold8 | +46.7 | +47.3 | 282,239 | 137,657 | 70.20 | R1 39,465 |
| **sweep3 + tau240** | +45.1 | +47.6 | 279,741 | 142,060 | **71.32** | R1 59,216, v1 final |
| hold8 + tau240 | +41.2 | +45.5 | 262,642 | 68,629 | 56.92 | – |
| sweep3 + hold8 + tau240 | +45.1 | +46.0 | 273,954 | 144,551 | 70.11 | R1 58,614 |
| *(post-hoc)* sweep4 + tau240 / sweep3 + tau360 | +44.5 / +38.9 | +45.1 / +49.1 | 269,045 / 269,961 | 130,079 / 136,647 | 66.74 / 71.85 | plateau, no cliff |

**The v1 final** (gate + maker, `A_SWEEP=3`, `RATE_TAU_S=240`, sha256 `161982ad…`) is kept only as an experiment
snapshot and was **not promoted**.
- Its CLI R3 result is 279,741.
- It raises the maker's quoting time on R3 from 0.19 to 0.26 of the session, and that is the engine that lost
  660k on B.
- Its R2 gain was mostly a single 600 s block (+53.6k of +78.7k).

`A_SWEEP=3` is the best stage-1 change under **both** objectives.

## Limitations
- **Public-tape selection.** One public R3 tape of 6,000 s decided the selection, and O uses both windows. The
  eval check only guards against gains that exist only in the first 2,400 s; it is not out-of-sample evidence.
- **Multiple testing.** About 13 alternatives were tested in v2, so the winner's +31k is biased upward.
- **Noise.** The +31k is about 1× the one-arm pnl_se. The 10/10 paired blocks are the stronger evidence, but they
  are not a paired SE or a P(win).
- **Grid edge.** A_SWEEP has only two grid values. The post-hoc A_SWEEP 4 run (300,120) suggests a plateau.
- **Inherited selection.** The A-definition thresholds come from full-tape fingerprint tables.
- **Mid-session objective change.** The objective changed during the session at the owner's request. Both plans
  and all runs are kept.
- **Previous-round tapes.** The tuned file is the ungated follower, so on R1-like flow it loses heavily (−198k).
  That is acceptable only because B and C are R3-setup tapes.
- **B scaling.** On B, the plain follower earned about half its public rate per second. The B effect of
  `A_SWEEP=3` is unknown and will be confirmed by upload.
- **Sandbox.** The website's static sandbox checker was not run.

## Commands (run from the main checkout; E = the experiment dir in this worktree)
```
env -u VIRTUAL_ENV uv run --locked python experiments/round_3/dataathletechamp/20261108-r3-wave-runner-001/runner.py \
  --strategy <worktree>/strategies/round_3/dataathletechamp/r3_combined_regime.py --grid $E/grid_v2_stage1.json \
  --tapes r3,r2 --out $E/v2_stage1 --workers 4      # v1: grid_stage1/grid_stage2 (+grid_finalists_r1 on r1)
env -u VIRTUAL_ENV uv run --locked python $E/analyze_v2.py $E v2_stage1   # v1: analyze.py $E stage1 stage2 finalists_r1
env -u VIRTUAL_ENV uv run --locked exchange-simulator --strategy <worktree>/strategies/round_3/dataathletechamp/r3_combined_tuned.py \
  --backtest data/round3/round3_public.csv --log-dir $E/cli_v2 --no-logs
env -u VIRTUAL_ENV uv run --locked python -m tools.preflight <worktree>/strategies/round_3/dataathletechamp/r3_combined_tuned.py
```
