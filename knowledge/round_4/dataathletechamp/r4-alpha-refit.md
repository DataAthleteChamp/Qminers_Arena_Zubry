# R4 alpha-gate refit on R2 + R3 + R4 (h 2 s / 5 s) — NEGATIVE — 20261108-r4-w3-alpha-001

Owner dataathletechamp, branch `r4-da-alpha` (from 8956e4b), 2026-11-08 07:16–07:35 CET. Official engine,
public tapes only, all in-sample for the refits. Not uploaded; website sandbox not run; private C unknown.

## Question and rule

U7 (`r4_u1_follower_u7_baseline.py`, sha `d2a0fc9c…`) vetoes flips with the frozen ridge `rlin0` (pooled
full R3 + R2, no intercept, h 2 s, FLIP_MARGIN 1.0; see `knowledge/round_3/dataathletechamp/r3-alpha-model.md`).
R4 trends at 5–60 s, so: does a refit that includes R4 (h 2 s, and h 5 s for the longer momentum) give a
better gate? Rule (coordinator, predeclared): ACCEPT if R4 > 821,692 and R3 + R2 ≥ 97% of 580,754 (563,331),
penalty 0. Grid predeclared: FLIP_MARGIN {0.8, 1.0, 1.2} × {h2, h5}.

## Method and provenance

- Data: R4 `round4_public.csv` `61c0b6d1…8a56`; R3 `1021586b…`; R2 `88ff641e…`. Engine unchanged
  (`simulator.py` c37b2262…, `models.py` d66d6155…, `strategy.py` 464830f4…); runner
  `20261108-r4-runner-001/runner.py` 27806eed… (5 ms, depth 20, ±100).
- Features: U7's own 25 live features recorded on R4 with a lots-0 replay of the U7 file (`record_r4.py`
  78b48e2a…; 176,048 rows, 7,676 A rows, 41.6 s). R3/R2: the R3 recordings, identical to U7-based recordings
  (max |diff| 0). Target mid(t + 5 ms + h) − mid(t + 5 ms); rows t ≥ 5 s, full tapes.
- Fit (`fit_r234.py` eb7ac704…): same recipe as `rlin0` (ridge λ 10 on clipped X/sd, no intercept, clip at
  pooled 0.1/99.9%). Check: the R3 + R2 h 2 s fit reproduces `RLIN0_COEF` to 4e-7.
- Attempt 2 (added after attempt 1 failed; `fit_r234_vn.py` a99026a4…): `r234vn`, h 2 s, each tape's target
  rescaled to R3's 2 s SD before pooling (R4 dominates the plain pool: 2 s grid SD R4 9.96, R3 6.68, R2 5.45).

## Model fit (R² / corr; grid rows, A rows; h 2 s target unless noted)

| model | R4 grid | R4 A | R3 grid | R3 A | R2 grid | R2 A | α̂ SD R4 |
|---|---|---|---|---|---|---|---|
| rlin0 (U7; R4 out-of-sample) | .029/.205 | .166/.517 | .029/.178 | .139/.386 | .001/.069 | .030/.210 | 0.90 |
| r234h2 | .116/.375 | .356/.621 | .007/.141 | .068/.331 | −.033/.046 | −.111/.145 | 2.17 |
| r234h5 (h 5 s target) | .078/.310 | .195/.470 | −.009/.094 | −.045/.160 | −.031/.041 | −.060/.105 | 3.16 |
| r234vn | .092/.369 | .301/.617 | .021/.150 | .117/.348 | −.012/.055 | −.029/.165 | 1.57 |

The R4-weighted fits load on inside-spread insert EMAs (ia200 −0.91, ib200 +0.80 std. weight), sweep EMA
(+0.83), fv200 and 0.2 s taker flow, with a negative event-sign weight (−0.52 vs +0.01 in rlin0).

## Policy results (official engine, PnL; U7 reproduced exactly in the same run)

| variant | R4 | ΔR4 | R3 | R2 | R3+R2 (Δ%) | R4 / R3 lots | verdict |
|---|---|---|---|---|---|---|---|
| U7 rlin0 1.0 | 821,692 | 0 | 413,588 | 167,166 | 580,754 | 378.7k / 384.5k | baseline |
| r234h2 0.8 / 1.0 / 1.2 | 805,658 / 804,012 / 778,309 | −16k / −18k / −43k | 331,370 / 333,372 / 344,739 | 122,772 / 112,127 / 113,420 | −21.8 / −23.3 / −21.1% | 412k/433k; 389k/404k; 358k/373k | reject |
| r234h5 0.8 / 1.0 / 1.2 | 804,182 / 815,186 / 816,529 | −18k / −7k / −5k | 348,227 / 335,778 / 328,241 | 97,327 / 102,808 / 101,700 | −23.3 / −24.5 / −26.0% | 382k/403k; 361k/386k; 342k/366k | reject |
| r234vn 0.8 / 1.0 / 1.2 | 811,522 / 816,235 / 814,097 | −10k / −5k / −8k | 353,220 / 364,355 / 348,210 | 129,224 / 134,192 / 112,011 | −16.9 / −14.2 / −20.8% | 412k/424k; 377k/391k; 339k/353k | reject |

Penalty 0 in all 30 runs. No variant beats U7 on R4, even though R4 is in-sample for every refit.

## Verdict and mechanism

**Negative; keep U7's `rlin0` 1.0.** Higher R² on R4 rows did not make a better veto. The refits load on the
same short-horizon flow/insert information that U7's FLOW_TRIG/TRIG1 triggers use, so the gate is less
independent of the trigger. At 0.8–1.0 more flips pass (R3 lots +0.4…+13%); at 1.2 fewer flips pass
(R3 lots −3…−8%) but PnL is still lower, so the selected flips are worse, not only more numerous. This repeats
the R3 alpha v2 lesson. `rlin0`, fitted without R4, already transfers to R4 (A-row corr .52).

Delivered `strategies/round_4/dataathletechamp/r4_follower_alpha_r234.py`. Its defaults are exactly U7
(official CLI R4 821,692, penalty 0, 47 s; preflight passes). MODEL `r234h2`/`r234h5`/`r234vn` are kept
only as research flags. It is not an upload candidate.

## Reproduce (MAIN, `E=experiments/round_4/dataathletechamp/20261108-r4-w3-alpha-001`, gitignored)

```
env -u VIRTUAL_ENV uv run --locked python $E/record_r4.py r4 $E/features_r4.npz
env -u VIRTUAL_ENV uv run --locked python $E/fit_r234.py        # model_block.txt, fit_report.json
env -u VIRTUAL_ENV uv run --locked python $E/fit_r234_vn.py     # model_block_vn.txt
env -u VIRTUAL_ENV uv run --locked python experiments/round_4/dataathletechamp/20261108-r4-runner-001/runner.py \
  --strategy $E/r234_grid_snapshot.py --grid $E/grid_r234.json --tapes r4,r3,r2 --out $E/run_r234 --workers 3
#   attempt 2: r234vn_grid_snapshot.py + grid_r234vn.json -> run_r234vn; tables: table.py <run dir>
```

Limitations: single public tapes, no paired SEs, everything in-sample. I stopped after two failed fits; I did
not search margins or fits further on in-sample tapes. The failed fit script and log (`fit_r234_v1_assertfail.*`,
mismatched clip bounds between horizons) are kept in the experiment folder.
