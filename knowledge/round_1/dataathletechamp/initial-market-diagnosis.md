# Round 1 initial market diagnosis

Source: original local public tape, 161,219,988 bytes, SHA-256
`362e8208be1eeec32ad190d097774e26448f0d5149575a8e1b1efd1db1735940`.
The official engine is unchanged. Raw audit and no-order streaming replay:
`experiments/round_1/dataathletechamp/intake-v1/`.

## Confirmed observations

- 4,411,336 event rows, strictly ordered distinct timestamps, about 12,000 seconds.
- 1,078,675 resting buy inserts, 1,078,982 resting sell inserts, 48,068 buy IOC
  inserts, 48,020 sell IOC inserts and 2,157,591 cancels.
- The official null replay produces 375,234 trade matches and 13,446,993 traded lots.
- A causal 50 ms grid contains 239,995 complete sampled books. About 93.03% have
  a one-tick spread; mean spread is 1.0705 ticks. These are sample-time statistics,
  not a weighting by all raw message rows.
- Midpoint spans 9990.5-10094.5. Discovery and validation means differ substantially;
  this is not evidence of a known fixed 10000 fundamental anchor or FX identity.
- Median best-level depth is about 900 lots; distribution is extremely right-skewed
  and has rare huge orders. Mean depth must not be mistaken for typical executable size.
- Nonoverlapping one-second midpoint changes have standard deviation 0.923 ticks,
  mean 0.0024 and lag-one correlation about 0.009. Variance ratios are near one.
  Strong global mean reversion or deterministic drift is not established.
- Jarque-Bera iid-reference tests reject a normal distribution. This is a discrete
  return distribution and an asymptotic reference, not an identified exact generator.
  Ljung-Box-20 does not reject autocorrelation at the same reference level; failure
  to reject does not prove independence.
- Best-queue imbalance correlates with 0.5-second later midpoint changes:
  discovery 0.3321, chronological validation 0.3325. Total-depth imbalance is
  weaker, about 0.12; short decayed external volume flow is about 0.27.

## Prediction versus trading

A ridge linear model fit ONLY on 0-4800 seconds uses queue/depth imbalance and
0.2/1/3-second decayed external flow. Its 0.5-second prediction on 4800-8400 has
correlation 0.437 and MSE 0.359 versus zero-forecast MSE 0.443. Mean absolute
forecast is only about 0.235 ticks: a correlation is not enough to justify paying
the spread. Passive quote selection is a more natural first experiment.

The first discovery maker wave was declared before execution, with 12 variants:
midpoint, inventory skew/size, depth/flow, queue hysteresis and minimum-rest policies.
All were penalty-free on 0-4800:

| Variant | Public discovery PnL |
|---|---:|
| Midpoint 2 lots / cap20 / skew0.05 | 4346 |
| Midpoint 10 lots / skew0.02 | 19807 |
| Midpoint 20 lots / skew0.02 | 36982 |
| Midpoint 40 lots / skew0.02 | 67073 |
| Midpoint 20 lots / skew0.01 | 35369 |
| Midpoint 20 lots / zero skew | 33252 |
| Depth weight0.5 / 20 lots | 42687 |
| Depth weight1 / 20 lots | 46282 |
| Depth0.5 plus flow / 20 lots | 44676 |
| Queue-imbalance side gate0.6 / 20 lots | 25040 |
| One-tick queue hysteresis / 20 lots | 30339 |
| Minimum rest50ms / 20 lots | 36044 |

These are discovery results, not final selection or private-round evidence.
Initial size/skew choices are experimental, not universal trading constants.
The cap80 strategy reserves in-flight orders and has only one outstanding order
per side. Even if both sides fill in any order, it must stay inside that cap.

## Chronology and limitations

- Discovery: 0-4800 s; selection validation: 4800-8400 s.
- Reserved final strategy outcome block: 8400-12000 s, opened only after selection.
- Full-tape descriptions consume some distribution information; the last block
  is not advertised as a pristine scientific holdout.
- Window runs preserve all original earlier event rows for book warmup and gate
  only the candidate's trading start. No naive event slicing/empty initial book.
- Every model/variant/failed trial remains in the contributor experiments folder.
- No tick annualization, inferred private z-score or bootstrap P(win) is valid.
- Identity remains anonymous. Structural analogy: large-tick FIFO order book;
  equity/futures/FX labels cannot be authenticated from anonymized prices.

## Commands

```bash
uv run --locked python experiments/round_1/dataathletechamp/intake-v1/profile.py
uv run --locked python experiments/round_1/dataathletechamp/evaluation/run.py \
  --id <new-id> --strategy <frozen-experimental-file> \
  --tape experiments/round_1/dataathletechamp/evaluation/tape-through-4800.csv \
  --stage discovery-0-4800
```

Output IDs deliberately refuse overwrites. Reproduce under a new experiment
folder/script path rather than modifying old completed evidence.
