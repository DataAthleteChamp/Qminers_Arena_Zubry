# Official larger-quote wave:449661 verified public PnL checkpoint

Original Round1 tape SHA256:
`362e8208be1eeec32ad190d097774e26448f0d5149575a8e1b1efd1db1735940`.
All results below use the unchanged official engine, public-depth20,5ms actions,
100 penalty-free inventory,1000 acceptance wall,10000/second breach rate.
No private score or win probability is available. All windows are consumed public.

## First4800s development: actual results, not the independent C++ estimates

| Variant | PnL |
|---|---:|
| queue control95 / skew0.01 | 129851 |
| nominal128 | 145983 |
| nominal160 | 152055 |
| nominal200 | 160919 |
|200 with full-headroom top-ups,2 slots/side | 164303 |
|200 with full-headroom top-ups,3 slots/side | 166457 |
| supplied V2-style200 / skew0.05 / width0.5 / depth0 | 124321 |
| V2-style200 / skew0 / width0.5 / depth0 | 133305 |
| V2-style200 / skew0 / width0.5 / depth0.25 | 95782 |
| V2-style200 / skew0.01 / width0.5 / depth0.5 | 138528 |
| full-headroom3-slot / skew0.005 / width0 / depth1 | 171650 |
| full-headroom3-slot / skew0.001 / width0 / depth1 | 169529 |
| full-headroom3-slot / skew0 / width0 / depth0 | 159252 |
| full-headroom3-slot / skew0.01 / width0.5 / depth0.5 | 139515 |
| skew0.005 /4 slots | 172566 |
| skew0.005 /8 slots | 172459 |
| skew0.005 /8 slots /1-lot minimum top-up | 172561 |
| skew0.005 / flow-price weight0.125 | 176067 |
| skew0.005 / flow-price weight0.25 | 176071 |
| skew0.005 / flow-price weight0.5 | 175253 |

Every row penalty0. Sizes>200 cannot add capacity inside the100 envelope.
The supplied Round0 microprice0.25/zero-skew headline did NOT transfer to this
Round1 test: it is below the matched V2-style zero-skew control. Retain the failure.
Reducing skew helps the large-capacity maker, but eliminating skew/depth does not.
The4-point development difference between flow0.125 and0.25 is not strong evidence.

## Original FULL tape: completed actual results

| Policy | Whole public PnL |
|---|---:|
| previous95 queue incumbent | 343269 |
| previous corrected ridge hybrid | 344438 |
| nominal200, ordinary30-lot top-up threshold | 411534 |
|200, full-headroom2 slots | 429954 |
|200, full-headroom3 slots | 434519 |
| full-headroom3 slots, skew0.001 | 441066 |
| full-headroom3 slots, skew0.005 | **449661** |

All new full results penalty0. Further flow/slot checks are not yet ranked here.
Do not call prefix176071 a full score or assume its whole-tape outcome.

## Exact449661 artifact and independent reconciliation

Source SHA256:
`46309d3232983388433f5bfde55da75a1c9011640e1fbc323260f0d1ff9d8165`.
Retained exact copy: `strategies/round_1/dataathletechamp/pnl_449661_full_capacity_maker.py`.
No code was cleaned/retuned after this result.

Actual full command:

```
uv run --locked python experiments/round_1/dataathletechamp/evaluation/run.py --id cp3-skew005-full --strategy experiments/round_1/dataathletechamp/capacity-pricing-v3/variants/skew005.py --tape data/round1/round1.csv --stage consumed-original-full-combined-recheck
```

Independent transparent observer reproduction:

```
uv run --locked python experiments/round_1/dataathletechamp/evaluation/trace_final.py --file experiments/round_1/dataathletechamp/capacity-pricing-v3/variants/skew005.py --expected-pnl 449661 --id trace-capacity-skew005-v1
```

Both reproduced449661. Independent cash-553239, ending inventory100,
actual mark10029 give`-553239+100*10029=449661`.
Actual and reserved extrema were±100 at every callback, no rejection,
zero time above100,24590 filled orders and2446536 lots.
Capture1240330 minus carry790619 minus terminal adjustment50 reconciles449661.
That is an accounting identity against an approximate50ms reference, not alpha proof.

Material risk change: abs position is exactly100 for41.1% of observed time.
The hard cap is unchanged, but larger orders increase boundary occupancy and
holding exposure. Higher public PnL is not identical private-path risk.
Later-window checks and final immutable top-three publication follow this checkpoint.

## Reproduction without local scratch tooling

From a fresh clone with the original tape:

```
uv run --locked python -m tools.preflight strategies/round_1/dataathletechamp/pnl_449661_full_capacity_maker.py
uv run --locked exchange-simulator --strategy strategies/round_1/dataathletechamp/pnl_449661_full_capacity_maker.py --backtest data/round1/round1.csv --log-dir experiments/round_1/dataathletechamp/your-fresh449661-recheck/logs --no-logs
```

Use a fresh path. No upload or Final selection was performed.
The ten first-stage and four combination sources were frozen before replay.
Two later questions separately registered3 finer-replenishment and3 flow-price arms.
Source arrays/params, commands/hashes and every raw outcome remain in local experiments;
curated lessons and verified retained files are the shared handoff.

Static generation failurev1 (E501) and the initial cancel-test design error are
retained. New formatted sourcev2 passed strict typing/lint/preflight. Corrected
13 focused protocol cases passed;5 mixed-IOC/actual-SDK contract tests passed.
