# Spread repair disproof and next bounded queue test

**Current Final:** participant reports validation **43782** for the gap/FIFO
file whose public score is103998. This improves the prior supplied Grid B28827
by14955. Seven shared upload slots remain per the latest owner response.
No latest export/source-hash was supplied; this is reported feedback, not a
new raw validation tape. The Final was not changed by the agent.

## Isolated repair-policy results

| Official A arm | Net PnL | Filled orders | Penalty |
|---|---:|---:|---:|
| Current gap/FIFO control | 103998 | 16010 | 0 |
| Spread2, single inside10 | **-18422** | 24850 | 0 |
| Spread>=3, both inside10 | 62216 | 20370 | 0 |
| Spread>=3, both requested20 | **-6659** | 21021 | 0 |

The flags0 version exactly reproduces all control fields. Each arm holds fixed
forecast, EMA target, hard100 and original gap guard. The20 variant can be
clipped to12 on a warned side; these are requested maxima, not always20 fills.
All plans and failures remain under `spread-repair-v1/v2` and immutable run IDs.

**Do not submit these repair arms to B.** All lose to the same A control;
more executions do not mean better economics. Episode duration greater than5ms
does not prove favourable fill selection. We did not collect full trade logs
for these failed arms, so their losses cannot be fully attributed to particular
G/F fills rather than changed core execution/inventory.

A repairing G order may cross our already-resting inside quote before any
remainder rests. A decision-time inside LIMIT may instead take on5ms activation
if the market has already repaired. These are hypotheses explaining adverse
selection, not an invented decomposition of these outcomes.

## Why the experiment was feasible but not profitable

Atspread2 onlyone strict integer insideprice exists. We chose actual
inventory-reducing side, or forecast sign when flat, and retained the opposite
outside quote. Atspread>=3, pricesbid+1/ask-1 are distinct; both sides were tested.
New inside submissions were blocked against **all** live/inflight/cancel-pending
opposite own orders. No self-cross credit or optimistic cancel release.

Preflight/Ruff/strictmypy and three integer-spread/cancel-pending tests passed.
Initialv1 reused an OptionalSide variable and failed strict types; those four
artifacts were preserved. Freshv2 used a separate `repair_side`, without casts
or changing trading-policy parameters. No failed build was labelled trading
evidence.

Source actually reviewed:
Eisler/Bouchaud/Kockelkoren, *The price impact of order book events: market
orders, limit orders and cancellations*, arXiv0904.0900v3,17September2010;
Quantitative Finance12(9),1395--1419(2012),
[DOI](https://doi.org/10.1080/14697688.2010.528444).
Researcher read v3I--VIII/AppendixA and AppendixB text/captions; no reproduction
or digitized plots. Nonexclusive distribution licence, no copied implementation.
Their response mixes immediate impact, subsequent flow and changing gaps;
their sample excludes approximately0.3% marketable limit orders, unlike this
venue's G which can cross our quotes. Paper results are not executable venue PnL.

## Reproducible original successful commands

```bash
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-repair-reference-A-v2 --strategy experiments/round_2/dataathletechamp/spread-repair-v2/artifacts/reference.py --tape data/round2/round2_public.csv --stage repairflag0-103998-equivalence
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-repair-spread2-one10-A-v2 --strategy experiments/round_2/dataathletechamp/spread-repair-v2/artifacts/spread2_one_side10.py --tape data/round2/round2_public.csv --stage uniqueinside-spread2-reducing-side10
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-repair-wide10-A-v2 --strategy experiments/round_2/dataathletechamp/spread-repair-v2/artifacts/wide_both10.py --tape data/round2/round2_public.csv --stage both-strict-inside-wide-repair10
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-repair-wide20-A-v2 --strategy experiments/round_2/dataathletechamp/spread-repair-v2/artifacts/wide_both20.py --tape data/round2/round2_public.csv --stage both-strict-inside-wide-repair20-existing-fragilitycap
```

Inputs remained unchanged. New repetitions require fresh IDs, not overwrite.

## Next limited question

`queue-reference-v1` preserves the successful exact prices, quantities and hard
envelope while testing minimum top-up1, four-child capacity, their interaction,
and an EMA reference updated only onspread1/bothdepth>=100. Aggregate requested
quantity at each price remains32/16/12. More child entries are not more allowed
inventory or unlimited external fill volume.

The EMA test separates mechanical one-sided wide-spread midpoint motion from
the inventory trend reference; it does not alter short-price forecasts/history
or claim a latent efficient price. The peer handoff reports its original
coefficients fitted on first3000publicseconds, target250ms/regularization100,
with crossing labels purged. This is reported provenance, not a new independent
verification of model fitting.

A is consumed development evidence; B feedback already consumed, C blinded.
New higher public results require exact reproduction and human B comparison
before changing Final43782. Doubling validation profit has not yet been achieved.
