# Pinned teammate branches: transferable findings and verified comparisons

Read `mkozlow` at7241e7d8b2431e3eb6b75e3b4418847c7b39e903.
The separate reviewer read the immutable `pandrzej` export at
1493cf3fec3dc55242445784b83bfe28d594f21d.
No teammate branch was checked out, merged or modified.

## mkozlow: official reproduction, not just a note

Exact retained midpoint64 source SHA256:
`86bed1db3ca7d2b4bc355bcea6d76b80e94bcba35529450297173ed3bee7bee4`.
Same original Round1 data SHA256:
`362e8208be1eeec32ad190d097774e26448f0d5149575a8e1b1efd1db1735940`.

Command actually run:

```
uv run --locked python experiments/round_1/dataathletechamp/evaluation/run.py --id peer-mkozlow-full-v1 --strategy experiments/round_1/dataathletechamp/peer-mkozlow-reproduction-v1/strategies/round_1/mkozlow/midpoint_maker_64.py --tape data/round1/round1.csv --stage peer-original-full-reproduction
```

**Reproduced206364 PnL, penalty0,30005 filled orders,77.9s locally.**
Their retained policy is one slot/side,64 nominal, no active forecast/taker,
half-width0.5 and20ms minimum age before a changed-price cancellation.
Do not replace our343269/344438 files with this lower public score.

Their handoff reports meaningful mechanisms: predictive models can churn quotes
and lose FIFO value; exact-price anchors failed later periods; same-price
replenishment carries more signal than simple cancellation history.
Reported broad takers and >100 inventory overflow lost heavily after costs.
Those extra trial results are author-reported, not independently reproduced here.

## pandrzej: pinned static evidence and baseline reproduction

The reviewer inspected twelve plans/results/outcomes and six distinct sources.
Full-run metadata contains the SAME original data SHA, not just Round0/sample.
Reported original-full PnLs:

| Source/policy | Recorded PnL |
|---|---:|
| r0_v2_maker small-size passive baseline | 27011 |
| maker_obi_noguard | 21751 |
| maker_obi | 18236 |
| one-lot zubry | -23851 |
| zubry_flow | -173493 |
| zubry_flow_v2 | -173599 |

All twelve logged trials have penalty0. Different engine digest methods and
missing row-consumption traces prevent treating metadata alone as reconciliation.
The baseline and guard-disabled maker can be reproduced for mechanism comparison,
not as contenders above our current public scores.
The frozen baseline was now actually reproduced using:

```
uv run --locked python experiments/round_1/dataathletechamp/evaluation/run.py --id peer-pandrzej-full-v1 --strategy experiments/round_1/dataathletechamp/review-pandrzej-pin-v1/research/experiments/r1-maker-baseline/strategy.py --tape data/round1/round1.csv --stage peer-original-full-reproduction
```

**Reproduced27011 PnL, penalty0,21719 filled orders,35.0s locally.**
This resolves the baseline's cross-platform/engine-result comparison, not all
the other logged trials. It is materially below our own retained large makers.

**Do not borrow flow-v1 risk logic:** its signed pending net can hide opposing
IOC reserves. We require separateBUY/SELL extrema. Its positive Round0 sample
scores reversed on sample_v2 and original Round1. That is valuable negative evidence.
The passive one-slot state structure is stronger: private per-match fills and
terminal confirmation preserve reserve through cancellations.

The reviewer flagged a hypothetical PARTIALLY_FILLED/remaining0 liveness condition,
but did not inspect the current SDK sequence. It is NOT a confirmed engine bug;
test actual IOC partial-then-CANCELED finality before new IOC work.
Current SDK `simulator/simulator.py:1194-1213` emitsFILLED at remaining0 and
CANCELED for unfilled IOC residuals. That hypothetical terminal-partial sequence
is not emitted by this engine; do not retain it as a confirmed peer defect.

## Incorporation

Test fixed-large-size controls, bounded FIFO retention and microprice-sided
widening before another fitted model. Keep each size, price and retention effect
separate. The450k/575k anecdotes are still unauthenticated, not a target achieved
by these inspected artifacts. No outside-team private strategy was solicited.
