# Final structural trial: one-level96 improves public PnL, B still unknown

Owner confirmed the dashboard remained open and named00:15 as the extended
cutoff. The earlier00:00 schedule was therefore not treated as definitive.
Current last confirmed successful Final is clean-reference validation47150.

All tests use the exact clean-reference source, same supplied forecast/EMA
logic and fixed100 actual/worst-side reservation envelope.

| A policy | Actual net PnL | Penalty |
|---|---:|---:|
| Equivalent reference | 104703 | 0 |
| Disable SHOCK quotes | 101514 | 0 |
| Two levels x48 | 118068 | 0 |
| **One level x96** | **121235** | **0** |
| Zero quote-center alpha, preserve SHOCK predictor | 101762 | 0 |

The1x96 trial gains16532(+15.8%) on A. The2x48 control gains13365.
Normal offered capacity stays96; caution offered capacity48.
Recovery16/shock32 are preserved rather than accidentally resized with the
normal-grid change. Common100clips actual requests and all pending quantities.
Different allocation/queue/fill selection can still harm B; no350k forecast.

The refactoring's default flags exactly reproduce every104703 field.
One-level96 exactly reproduced every121235 result field under a fresh ID.
Preflight/Ruff/strictmypy passed on all five frozen files; original matcher and
rawdata were not changed. No new coefficients or private/validation fit.

Ready single-file validation trial:
`strategies/round_2/dataathletechamp/r2_trial_grid1x96_public_121235.py`.
SHA256 `fbaaf56d9297cdbf1907fec73bda0cf7a9beb03371f22357be50c544f3cd01bf`.
One no-argument BaseStrategy,14273bytes, stdlib/public SDK only.
Its B score is UNKNOWN: test manually and keep47150Final unless B improves.
No upload or website Final change was made by the agent.

Original successful commands:

```bash
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-final-reference-A-v1 --strategy experiments/round_2/dataathletechamp/final-structural-v1/artifacts/reference.py --tape data/round2/round2_public.csv --stage final-disabled-flags-equivalence
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-final-no-shock-A-v1 --strategy experiments/round_2/dataathletechamp/final-structural-v1/artifacts/no_shock.py --tape data/round2/round2_public.csv --stage final-no-SHOCK-quotes-only
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-final-grid2x48-A-v1 --strategy experiments/round_2/dataathletechamp/final-structural-v1/artifacts/grid2x48.py --tape data/round2/round2_public.csv --stage final-two-price-levels-sameaggregate96
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-final-grid1x96-A-v1 --strategy experiments/round_2/dataathletechamp/final-structural-v1/artifacts/grid1x96.py --tape data/round2/round2_public.csv --stage final-single-price-level-budget96
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-final-quote-alpha0-A-v1 --strategy experiments/round_2/dataathletechamp/final-structural-v1/artifacts/quote_alpha0.py --tape data/round2/round2_public.csv --stage final-quote-price-alpha0-shock-signal-preserved
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-final-grid1x96-A-repro-v1 --strategy experiments/round_2/dataathletechamp/final-structural-v1/artifacts/grid1x96.py --tape data/round2/round2_public.csv --stage final121235-onelevel-exact-reproduction
```

Full A is consumed selection evidence, not an untouched holdout.
Outcome-only B exports cannot establish its market spread/volatility/trade
distribution. PrivateC remains blinded; no profit-on-every-path claim.
