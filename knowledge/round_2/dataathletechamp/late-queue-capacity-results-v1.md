# Late Round 2 tests: no large breakthrough

**Preserve the last confirmed Final: reportedB43782.** Seven upload slots were
reported, but remaining wall-clock time is now the binding constraint.
None of the results below establishes doubled validation PnL or400k.

Baseline gap/FIFO: public103998, source
`ac3d1814a3566e7e0507e2d2964b89e3aed8e572515f8c659b22aeff6600d8de`.
Same registeredA and unchanged officialSDK, hard100 including every remaining
live/submit/cancel-pending order.

| A arm | Net PnL | Change versus103998 |
|---|---:|---:|
| Minimum top-up1, two children | 102853 | -1145 |
| Four children/price, minimum8 | 102676 | -1322 |
| Four children/price, minimum1 | 102737 | -1261 |
| EMA reference only on NORMAL-quality book | **104703** | **+705** |
| Global quote96 | 94869 | -9129 |
| Global quote192 | 54640 | -49358 |
| New NORMAL quotes192, otherwise original | 94156 | -9842 |

All penalty0, input hashes unchanged. Queue control matches every baseline
field103998. The three preceding inside-spread arms also lost versus baseline:
-18422 /62216 /-6659. Thus more orders, larger exposure and available repair
time are not a demonstrated source of profit. We stopped those mechanisms
instead of spending B submissions on the losing local variants.

The clean-reference arm changes **only inventory EMA updates**: require current
spread1 and both market L1 depths>=100. Price forecast and short lag history
stay unchanged. A one-sided gap midpoint does not update the target's trend
reference; the first valid clean book updates at its actual observed timestamp.
It is not a claim to observe latent efficient price or predict news.

Its +705 is only0.68% of A and **not** persuasive evidence of a large
unseen-market gain. Nonetheless, the exact result was reproduced under
r2-queue-normal-ema-A-repro-v1, all result fields identical and penalty0.
This is the only positive local challenger from this wave, not a new Final.

Retained file:
`strategies/round_2/dataathletechamp/r2_grid_clean_reference_public_104703.py`.
SHA256 `10886b7d213b2426394f43c971a0615a733327725927c7d0ec7c14d8e1cdf780`.
Its B result remains UNKNOWN. It keeps the original prediction coefficients;
peer handoff reports fitting first3000A/250ms target/regularization100, purged
boundary labels, but we did not independently execute that fitting pipeline.

## Actual successful commands

```bash
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-queue-small-deficits-A-v1 --strategy experiments/round_2/dataathletechamp/queue-reference-v1/artifacts/small_deficits.py --tape data/round2/round2_public.csv --stage minimum1-same-FIFO-child-capacity
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-queue-more-children-A-v1 --strategy experiments/round_2/dataathletechamp/queue-reference-v1/artifacts/more_children.py --tape data/round2/round2_public.csv --stage more-working-children-same-aggregate-quantity100risk
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-queue-small-more-A-v1 --strategy experiments/round_2/dataathletechamp/queue-reference-v1/artifacts/small_more_children.py --tape data/round2/round2_public.csv --stage combined-min1-capacity4-FIFO-controlled
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-queue-normal-ema-A-v1 --strategy experiments/round_2/dataathletechamp/queue-reference-v1/artifacts/normal_reference_ema.py --tape data/round2/round2_public.csv --stage trend-reference-excludes-mechanical-wide-midpoints
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-capacity-quote96-A-v1 --strategy experiments/round_2/dataathletechamp/grid-capacity-v1/artifacts/quote96.py --tape data/round2/round2_public.csv --stage larger-top-quantity96-samehard100
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-capacity-quote192-A-v1 --strategy experiments/round_2/dataathletechamp/grid-capacity-v1/artifacts/quote192.py --tape data/round2/round2_public.csv --stage larger-safe-oppositeboundary-headroom192
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-capacity-normal192-A-v1 --strategy experiments/round_2/dataathletechamp/grid-capacity-v1/artifacts/normal_new192.py --tape data/round2/round2_public.csv --stage larger-new-quantity-only-stableNORMAL
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-queue-normal-ema-A-repro-v1 --strategy experiments/round_2/dataathletechamp/queue-reference-v1/artifacts/normal_reference_ema.py --tape data/round2/round2_public.csv --stage clean-reference104703-exact-reproduction
```

Frozen family manifests hold all source hashes. Preflight, Ruff/format and
strictmypy passed for all artifacts. Two clean-reference/queue-capacity tests
and the192+8 opposite-boundary exposure test passed. More requested quantity
does not authorize more actual/potential inventory.

A/R1 are consumed diagnostics; B feedback is selected evidence, C still blinded.
No rawB book exists here, no automatic upload/Final change or evaluator edits.
One manual B comparison of the clean-reference file is the only defensible
next test from this wave; keep43782Final unless its actual B PnL improves.
