# R3 causal alpha model for D1 decisions (flip / entry / hold) — 20261108-r3-w3-alpha-model-001

Owner dataathletechamp, branch `r3-da-alpha-model`, 2026-11-08. Official-engine public-tape research
(`runner.py` in-process `ExchangeSimulator`, 5 ms, depth 20, ±100, 10,000/s). Public A/R2/R1 only;
private B/C performance UNKNOWN. Not uploaded; website sandbox not run.

## Question

D1 (informed follower, h5, join-touch exit) nets 270k on R3 A but loses 65% of gross alpha to
2,151 200-lot flips at ≈ 1.2 ticks/lot. Can a stronger causal, cheap alpha used only for D1's
decisions (P1 flip gate, P2 alpha entry, P3 hold/exit, P4 = P1+P3) keep more of it?

## Provenance

| item | value |
|---|---|
| R3 A | `data/round3/round3_public.csv` `1021586b92a3d9df…` |
| R2 / R1 | `data/round2/round2_public.csv` `88ff641e962540c6…`; `data/round1/round1.csv` `362e8208be1eeec3…` |
| engine | unchanged `simulator.py` c37b2262186f977d, `models.py` d66d6155376fae92, `strategy.py` 464830f41c071531 |
| strategy (default D1) | `strategies/round_3/dataathletechamp/r3_alpha_follower.py` sha256 `a01404e401b9cba4c9b3ab71552681d80b3b449a997f6ba93bd539d8f19a331d` (v2: + FV flags; v1 `fa66f0e1…` in commit f3e0791) |
| strategy (P1 defaults) | `r3_alpha_follower_p1.py` sha256 `51ee7c756562e96e7c120bebbc8dba1a4a55073f92bdc2e6475c4b7a379306bd` (same code; `POLICY="p1"`; v1 `16bcf580…`) |
| scripts (experiment dir, gitignored) | `record.py` 503d3df5…, `fit_alpha.py` 34955715…, `fit_alpha_sym.py` c97c6469…, `fit_flip_model.py` 22bad3a9…, `summarize.py`, `bias_check.py`; runner `20261108-r3-wave-runner-001/runner.py` 07972771… |
| windows | model fit R3 5 s ≤ t < 2394 s (targets end < 2400 s); eval R3 t ≥ 2400 s, all of R2, all of R1 (frozen) |

Grid runs before the final edits used snapshot `ecc25413…` (identical logic; later versions removed
`__slots__`/`__future__`, added the `sym` model, then the FV flags, all default-off). v1 reproduced D1
(270,229 / 26,384 / −197,585) and P1 lin 1.0 (318,172 / 73,799 / −112,045) to the unit; v2 (`a01404e4…`)
reproduces D1 270,229 and P1 lin 1.0 318,172 on R3 (`run_fv_takers`). Preflight passes on both files.

```
E=experiments/round_3/dataathletechamp/20261108-r3-w3-alpha-model-001   # inside the worktree
uv run --locked python $E/record.py r3 $E/features_r3.npz      # also r2, r1 (lots 0 null replay, 33-69 s)
uv run --locked python $E/fit_alpha.py                         # ridge/HGB/distil, fit_report.json, model_block.txt
uv run --locked python $E/fit_alpha.py 1200 _half              # half-window robustness model
uv run --locked python $E/fit_alpha_sym.py [1200 _half]        # mirror-symmetric ridge
uv run --locked python <runner.py> --strategy <abs file> --grid $E/grid_*.json --tapes r3,r2,r1 --out $E/run_* --workers 3
uv run --locked python $E/fv_live_check.py                     # live FV50 precursor check
# FV ladder: grid_fv.json (r3,r2) on snapshot r3_alpha_follower_fv_snapshot.py; grid_fv_takers.json (r3) on fv2 snapshot (= a01404e4)
```

## Features (25, O(1) live, identical code in recorder and strategy)

Event (last market taker order of the callback, 0 on grid rows): A sign, signed run position (≤10),
signed fill/100 (≤20), signed span (≤5). State: signed A EMA 1 s/5 s, strong-A EMA 2 s, sweep (span ≥ 2)
EMA 1 s, exp(−Δt/1 s) since last +A / −A, A-rate EMA (τ 120 s), insert-implied FV 20/50/200 ms (new
market ids within 2 ticks of each touch; (max new bid + min new ask)/2 − mid), inside-spread insert
EMAs by side (τ 50/200 ms), last trade side, signed taker volume EMA 0.2/1/5 s, L1 queue imbalance,
spread, virtual D1 target sign. Rows: every market-taker callback + first callback per 50 ms
(R3 172,849 rows; A count 6,146 = prior agents). Target: mid(t+5 ms+h) − mid(t+5 ms).

## Model scores (R² vs zero / corr; frozen R3-fit models)

| h | model | R3 fit grid | R3 eval grid | R3 eval A rows | R2 grid | R2 A rows | R1 grid |
|---|---|---|---|---|---|---|---|
| 0.5 | ridge | .081/.284 | **.051/.226** | .166/.410 | .014/.145 | .149/.402 | −.019/.410 |
| 0.5 | HGB (d4, 100) | .234/.518 | .049/.229 | .168/.412 | −.009/.113 | .195/.445 | .143/.432 |
| 0.5 | tree d6 distil | .088/.297 | .046/.215 | .149/.391 | .015/.148 | .175/.418 | .057/.366 |
| 1 | ridge | .069/.262 | .036/.191 | .160/.404 | −.013/.081 | .033/.269 | −.191/.301 |
| 1 | HGB | .307/.601 | −.004/.157 | .148/.395 | −.082/.012 | −.002/.251 | −.005/.293 |
| 1 | tree d6 distil | .087/.297 | .021/.167 | .142/.377 | −.018/.073 | .065/.273 | −.047/.231 |
| 2 | ridge (`lin`) | .060/.244 | .020/.152 | .106/.336 | −.034/.029 | −.044/.172 | −.393/.172 |
| 2 | HGB | .394/.690 | −.096/.068 | .023/.271 | −.169/−.049 | −.159/.127 | −.098/.160 |
| 2 | tree d6 distil (`tree`) | .087/.299 | .008/.141 | .082/.288 | −.030/.044 | .016/.182 | −.049/.151 |
| 2 | ridge top-8 distil | .049/.221 | .016/.136 | .082/.299 | −.036/.012 | −.036/.158 | −.417/.127 |
| 2 | mirror-sym ridge (`sym`) | .054/.235 | .022/.151 | .102/.325 | −.029/.031 | −.037/.173 | −.303/.178 |
| 5 | ridge | .052/.226 | .002/.112 | .049/.236 | −.052/−.004 | −.037/.063 | −.649/.074 |
| 5 | HGB | .413/.691 | −.137/.027 | −.131/.106 | −.180/−.021 | −.202/.026 | −.807/.022 |

- Predictability lives at ≤ 1 s and at A events (A-row corr 0.34–0.41); at 2 s the 50 ms-grid corr is
  0.15 (prior frozen linear: 0.16) — the new features do not lift the 2 s grid signal. R2/R1 R² < 0 at
  ≥ 1 s (scale/drift mismatch) though corr stays positive at A rows.
- HGB overfits massively (fit R² .39 → eval −.10 at 2 s); the depth-6 distilled tree generalises better
  than HGB but not better than ridge. A-row-only ridge (λ chosen on an inner split of the fit window)
  = A-row R3 eval .103/.326: no gain over the all-row ridge (negative result).
- Top standardised ridge weights (2 s): fl1 +.81, a5 −.75, fl5 −.60, a1 +.58, sw1 +.44, ta_pos −.39.
- Directional bias: `lin` has mean α̂ −0.13 (fit) … −0.27 (R1) on the grid, learnt from the fit-window
  down-drift (−0.11 ticks/2 s); `sym` (rows augmented with side-mirrors) has mean ≈ 0 and same skill.
- Model cost (pure Python): one α̂ incl. features 6–9 µs; feature-state maintenance ≈ 10 µs/event.
  Full R3 run: D1 13 s, P1 33–41 s (2.41M tape rows; other jobs on the machine) ≪ 15 min.

## Policy table (PnL/s fit / eval; Δ vs D1 paired on the same tape; flips / ignored on R3)

D1: R3 39.4 / 48.8 (270,229), R2 5.3 / 3.8 (26,384), R1 −15.0 / −17.4 (−197,585), 2,151 flips.
R3 Δfit is in-sample for the full-window models.

| variant | R3 fit / eval (Δ) | R2 fit / eval (Δ) | R1 fit / eval (Δ) | R3 flips/ign | rule |
|---|---|---|---|---|---|
| P1 lin 0.6 | 50.0 / 51.7 (+10.6 / +2.9) | 10.8 / 16.9 (+5.5 / +13.1) | −9.4 / −12.3 (+5.7 / +5.1) | 1681/549 | pass |
| **P1 lin 1.0** | 48.2 / **56.2** (+8.9 / **+7.4**) | 9.2 / 14.4 (+3.9 / +10.6) | −6.8 / −11.0 (+8.2 / +6.4) | 1486/798 | pass |
| P1 lin 1.4 | 49.7 / 52.6 (+10.3 / +3.7) | 7.4 / 12.9 (+2.1 / +9.1) | −3.8 / −9.5 (+11.2 / +7.9) | 1275/1063 | pass |
| P1 tree 0.6 / 1.0 / 1.4 | 38.9 / 52.3; 39.3 / 46.8; 36.5 / 46.9 | 5.2 / 10.2; 0.9 / 20.2; 0.4 / 19.1 | −3.6 / −6.4; −2.1 / −3.3; −2.6 / −3.1 | 1115–679 | 0.6 marginal (R2 fit −0.1), others fail R3 eval |
| P1 sym 0.6 / 1.0 / 1.4 | 49.5 / 47.1; 49.0 / 48.1; 49.7 / 46.4 (eval −1.7 / −0.7 / −2.4) | 5.7 / 17.7; 7.0 / 14.8; 9.6 / 16.0 | −9.9 / −13.7; −7.3 / −10.6; −2.9 / −7.5 | 1800–1345 | fail R3 eval |
| P1 lin, model fit t < 1200 s, 0.6 / 1.0 / 1.4 | 42.4 / 48.8; 41.7 / 50.7; 41.3 / 51.9 (eval 0.0 / +1.8 / +3.1) | 7.3 / 1.7; 6.4 / −0.2; 11.3 / −3.9 (eval −2.1 / −4.0 / −7.7) | −9.1 / −13.0; −6.8 / −10.8; −4.1 / −9.5 | 1664–1212 | fail R2 eval |
| P1 sym, fit t < 1200 s, 0.6 / 1.0 / 1.4 | 45.3 / 40.2; 45.5 / 39.9; 41.9 / 33.7 (eval −8.6 / −8.9 / −15.1) | 5.9 / 3.3; 4.2 / 4.1; 4.9 / −0.2 | not run | 1758–1319 | fail |
| P2 lin entry 1.5 / 2.5 | 39.3 / 46.5; = D1 | 7.1 / 3.8; 7.7 / 3.8 | ≈ D1 | 2156; 2151 | fail / no-op (flat only 1.7% of time) |
| P3 lin extend only (1.0, 3 s) | 39.3 / 49.5 (−0.1 / +0.7) | 5.5 / 3.9 (+0.2 / +0.1) | ≈ D1 | 2163 | passes by +0.7 (noise) |
| P3 early exit lin −1.5 / −2.5, tree −2.0 | 41.9 / 41.1; 43.4 / 42.6; 42.2 / 37.5 | 2.3 / −2.6; 4.5 / 2.9; 6.1 / 0.2 | ≈ D1 | | fail (eval −6 … −11) |
| P4 lin 1.0 + exit −2.5; tree 1.0 + exit −2.0 | 51.4 / 48.4; 45.4 / 34.3 | 9.3 / 12.9; −2.6 / 12.3 | −6.2 / −10.8; −1.8 / −3.7 | 1383; 459 | fail R3 eval |

Penalty 0 and no skipped sends in every run. Attribution (ticks·lots vs mid at send): R3 D1 gross 796k,
cost 526k; P1 lin 1.0 gross 697k (−99k), cost 379k (−147k); P1 sym 1.0 gross 695k, cost 404k. R2 D1
gross 536k / cost 509k; P1 lin 1.0 446k / 372k. Every P1 variant trades gross alpha for flip cost; the
net sign depends on which flips are dropped.

## Coordinator FV ladder V1–V4 (inside D1, same IOC execution; flags `FV_FLIP`, `FV_HOLD`, `FV_ENTRY`, `FV_DEPTH`, `FV_TAKERS`)

The tape screen (`jump_precursor_screen.py`) builds FV from **all** G inserts in 50 ms (any depth, incl.
marketable ones). The live FV here sees only resting new market ids within `FV_DEPTH` ticks of the touch
(marketable inserts that fill completely are invisible; their limit price is not in `Trade`). Live FV50
(depth 2) as a precursor (`fv_live_check.py`, 50 ms grid): |FV| ≥ 1 is 7.5–9.1% of R3 time, +1.0–1.1
ticks at 0.5 s; |FV| ≥ 1.5 is 0.3% (−0.15…+0.66), |FV| ≥ 2 is 0.08–0.09% with mean spread 4.8–6.2 and no
edge in R3 eval (+0.11 at 0.5 s). The screen's +3.4-tick FV ≥ 2 signal is **not reproduced live**.

| variant (R3 total; fit / eval PnL/s) | depth 2 | depth 10 | depth 10 + taker fills (`FV_TAKERS`) |
|---|---|---|---|
| V1 pre-emptive flip, FV opposes ≥ 2.0 | 93,711; 15.1 / 15.9 | 14,812; 5.5 / 0.5 | 40,946; 10.6 / 4.3 |
| V1 pre-emptive flip, FV opposes ≥ 1.5 | −139,840; −13.7 / −29.7 | −206,997; −32.6 / −35.8 | not run |
| V2 hold while FV agrees ≥ 1.5 | 270,229 (= D1, never fires) | 269,778; 39.4 / 48.7 | 270,348; 39.4 / 48.8 |
| V3 FV entry from flat ≥ 2, spread ≤ 2 | 270,229 (= D1) | 270,129; 39.4 / 48.8 | 270,129; 39.4 / 48.8 |
| V4 = V1 2.0 + V2 1.5 | 93,711 | 14,727 | not run |

R2 (no longer a constraint): V1 −130k…−386k, V2/V3 ≈ D1 (26.4k–28.2k). V1 flips into wide spreads after
inserts and reverses often (R3 lots 0.49–0.79M vs D1 0.44M). V2/V3 are no-ops because live FV is rarely
≥ 1.5. **All FV variants rejected** (no R3 gain; V1/V4 lose 177k–477k).

## Objective change (owner, applied after the runs above): R3 only

New predeclared objective: maximise R3 public PnL; the change must not reduce R3 eval (t ≥ 2400 s) by more
than 2 PnL/s; plateau over neighbouring parameters; R1/R2 informative only; no regime gate (it lost on B).
Under it (R3 total Δ vs 270,229; eval Δ):

| candidate | R3 total (Δ) | eval Δ | plateau | status |
|---|---|---|---|---|
| **P1 lin 1.0** (`r3_alpha_follower_p1.py` default) | **318,172 (+47.9k)** | **+7.4** | 0.6 / 1.4: +35.8k / +38.1k, eval +2.9 / +3.7 | **best; passes** |
| P1 lin, model refit t < 1200 s, 0.6 / 1.0 / 1.4 | 277.7k / 282.3k / 285.9k (+7.5…+15.7k) | 0.0 / +1.8 / +3.1 | yes | passes (smaller) |
| P1 sym 0.6 / 1.0 / 1.4 | 288.5k / 290.6k / 286.4k (+16…+20k) | −1.7 / −0.8 / −2.4 | yes | passes at 0.6/1.0 |
| P1 sym, refit t < 1200 s | 253.3k / 252.8k / 221.7k | −8.6 / −8.9 / −15.1 | — | fails |
| P1 tree 0.6 / 1.0 / 1.4 | 281.5k / 262.7k / 256.4k | +3.5 / −2.0 / −1.9 | collapses | fails plateau |
| P4 lin 1.0 + early exit −2.5 | 297.6k | −0.4 | — | worse than P1 |
| P3 extend only | 272.6k | +0.7 | — | negligible |

The R3 fit-window part of every full-window P1 gain is in-sample for the model (fit t < 2400 s); the honest
out-of-sample R3 evidence is the eval window (+7.4 PnL/s ≈ +26.6k over 3,600 s for lin 1.0).

## Selection disclosure

Margins 0.6/1.0/1.4, P2/P3/P4 settings and the 2 s horizon were declared before any policy run. After
seeing P1 results I added (a) a half-window refit and (b) the mirror-symmetric model as robustness checks
(motivated by the lin intercept/drift bias found afterwards). Calling P1 lin 1.0 "best" and making it the
default of `r3_alpha_follower_p1.py` is selection on R3 eval.

## Verdict

- **Model**: stronger only at short horizons and at A events (A-row R3 eval corr 0.34 at 2 s, 0.41 at
  0.5 s); at 2 s the grid signal is no better than the prior linear model. Boosting overfits; the cheap
  ridge (or mirror-symmetric ridge) is the right runtime form.
- **P1 lin passes the acceptance rule** at all three margins (R3 eval +2.9…+7.4, R2 +2…+5.5 / +9…+13, R1
  +5…+11), **but it is not robust**: the same policy with a mirror-symmetric model (same skill, no drift
  bias) loses on R3 eval (−0.7…−2.4) and a model refit on t < 1200 s loses on R2 eval (−2…−8), while
  the symmetric half-window model loses −9 to −15 on R3 eval. The R3-eval gain of P1 lin is within the
  spread caused by model-fitting details; it should not be expected on private R3-like flow.
- Consistent part: on R2/R1-like flow (flips worth less) the gate saves more cost than alpha with the
  full-window models (R2 +9…+14 eval; R1 +4…+12). On R3-like flow it is −15…+7 depending on the fit.
- P2 (no-op: D1 is flat 1.7% of the time), P3 early exits (churn) and P4 are rejected.
- Original recommendation (R3 eval + R2 rule): keep D1 as the default; P1 = R2/R1-protection candidate.
- **Under the owner's R3-only objective (final)**: P1 lin 1.0 is the best R3 candidate — R3 318,172 vs
  270,229 (+47.9k, of which the fit window is in-sample), eval +7.4 PnL/s, plateau over margins 0.6–1.4
  (+2.9…+7.4 eval), drawdown −8.6k vs −13.5k, 10/10 positive 600 s blocks. Its half-window refit also
  passes (eval 0…+3.1); the symmetric model passes at 0.6/1.0 (−1.7/−0.8) but its half-window refit fails
  (−8.6…−15.1). Upload `r3_alpha_follower_p1.py` to B to confirm; expected out-of-sample gain is the eval
  rate (≈ +7 PnL/s on R3-like flow), with real risk of ≈ 0 or negative if B differs from the fit window.
- FV ladder V1–V4: rejected; live FV cannot see the screen's marketable/deep inserts, and FV flips lose.

## Limitations

One public R3 tape, one chronological split, 600 s blocks autocorrelated; deltas are single paired runs
(no SEs). Recorder insert detection = new id near touch (orders drifting into the 2-tick window can be
read as new; identical live and in fitting). Non-reactive tape. R1/R2 are proxies for private mix.
Next test (cheapest): upload `r3_alpha_follower_p1.py` to validation B (D1 there: +272,176); reject the
flip gate if B PnL < D1's. Optional: refit `lin` on all of R3 public (t < 6000 s) before a private
submission only if B confirms.
