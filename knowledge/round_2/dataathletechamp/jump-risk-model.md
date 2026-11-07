# Round 2: an independently reproduced risk screen, then monetary tests

**Finding:** nondirectional next-second endpoint risk is more learnable than
the weak return-mean screen, and microstructure improves proper losses beyond
volatility alone on both consumed-A blocks. This justifies a small executed
policy test, not a guaranteed profitable submission.

The supplied memo's AUC0.898 was not reproduced from its missing CSV/script.
These are our own same-SDK observations, feature definitions and first40% fit;
do not silently relabel the memo's 3000s split as this run.

## Fixed fitting and measurement

`jump-risk-screen-v1`, official no-order 50ms standing-book observations.
Take a nonoverlapping one-second clock with25ms offset. Label
`abs(mid_at_actual_next_1s_sample - current_mid)>=5ticks`.
This is an **endpoint** label, not any intrasecond excursion or first passage:
a large spike/reversal can end close to its start and be labeled0.
The 50ms base sampling cannot establish a5ms warning lead.

Prefix features/actual targets before2399.9984052s; maximum fitted target
2399.025s. Selection ends4199.9972091s. Late A is already profiled/consumed,
not pristine holdout. Scaling from the fit rows only. One fixed L2 logistic
fit per model, coefficient1/intercept exempt, no threshold/model sweep.

Volatility-only uses log1p past60s returnSD. Full adds absolute prior3s move,
log1p minimum BBO depth, spread, absolute QI, log1p absolute executed
flowEMA0.2s, log1p absolute OFIEMA0.2s and largest top-order concentration.
This is not a larger directional Ridge or a model of our conditional fills.

Calendar observations5998; missing endpoint labels8; unavailable past features
300, including63 jump labels. Those excluded states cannot be called safe.
In the implementation trial, unknown risk is explicitly conservative, not
zero volatility/probability.

| Model | Selection ROC AUC | Late ROC AUC | Selection Brier | Late Brier |
|---|---:|---:|---:|---:|
| Prefix base rate | 0.5000 | 0.5000 | 0.081511 | 0.045461 |
| Volatility only | 0.7882 | 0.8119 | 0.072870 | 0.042550 |
| Full microstructure | 0.9052 | 0.9464 | 0.069697 | 0.036976 |

Full-versus-vol Brier gain4.36%/13.10%, exceeding the predeclared1% screen in
both blocks. Logloss also improves: selection0.249405->0.221044,
late0.163625->0.125719. Full averageprecision0.3927/0.3606 versus
block base rates0.0875/0.0477. Fit labels108/2338;
selection152/1738; late77/1613. These are correlated tape observations,
not independent-market repetitions or a private win probability.

Using a prefix-frozen90th-percentile alert threshold, full-model alerts cover
21.58%/10.60% of selection/late observations, with precision33.60%/38.01%
and recall82.89%/84.42%. Actual alert budget drifts with the market regime.

**Calibration is imperfect despite the AUC:** in selection, predicted-score
0.7--1 averages0.852 but observed frequency is0.392; in late that bin has only
six cases, prediction0.897 versus actual0.333. Treat thresholds as experimental
risk-score categories, not authenticated probabilities on C.

## Why the first policy ladder is small

[Actual accumulation fill diagnostics](execution-diagnostics.md) are negative
in high/undefined volatility across all three consumed-A blocks. QI/flow
agreement is still negative on those selected fills. More directional
aggression is therefore not the first intervention.

`risk-overlay-v1/plan.json` freezes three arms after an equivalence control:

| Arm | Only intended intervention |
|---|---|
| volatility_capacity | Vol-only risk score; capacity100/70/35 at0.03/0.15 |
| microstructure_capacity | Same capacity mapping, full8-feature risk score |
| microstructure_width | Same full score; both base quotes1tick deeper at>=0.15, fixed100 capacity |

This compares the detector's economic value and quantity against widening,
instead of asserting that either wins from paper abstracts. No parameter grid,
R1 price-alpha change, permanent short, IOC activation or risk expansion.

Risk is reviewed every50ms; volatility is past-only exact1s calendar SD.
Actual callbacks/own interventions differ from the null fitting stream.
Runtime invalidates a return spanning an observed missing side, including
subgrid gaps the screen may not see. Unknown history means cap35 for quantity
arms or width1 for the width arm; missing book follows immediate safe cancel
handling. All costs of unavailable history remain in the monetary comparison.

Trim younger accepted children before a safe old head when a soft budget falls.
Whole orders may require cancellation; no assumed partial-shrink acknowledgement.
Canceled/inflight quantities remain fully reserved until private status.
Hard checks require `q+allRemainingBuys<=100`, `q-allRemainingSells>=-100`;
opposite-side reservations never net. A soft target below the current position
does not instantly unwind it.

The flags0 version **exactly reproduced every result field of the -143178
Final control**. All four files passed conservative preflight, Ruff, strict
mypy and four focused race/queue/headroom/causal-clock tests.
Actual monetary overlay outcomes are recorded separately under immutable IDs.
Save a new positive public leader only after exact reproduction; no automatic
upload, Final flag, private profit or first-place claim.

## Reproduction

Successful command:

```bash
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/jump-risk-screen-v1/analyze.py
```

Source SHA256:
`6cec36da63380ef3a0388d4de69c9b95c0e67fb06c11eea0c1ad97f77d83f45b`.
Result:
`986a991480ac36f646730f3ff35a40ee68d37adc9938c4c048eba6cf7f1456b4`.
Input NPZ:
`90b7f0b14a557b436ab9e6339a99ddf83d0573d865dac59a5cac4899ad2868aa`.
Two target-boundary/tied-score tests passed. Initial Ruff B905/E501 failure
was preserved before correction; it produced no model result.
Use a new output/version to reproduce, never overwrite the completed file.

Raw experiment code/results remain local per contributor layout. B identity/
reuse and C distribution/performance remain UNKNOWN. Repeated B feedback would
consume selection evidence; no current B feedback was used.
