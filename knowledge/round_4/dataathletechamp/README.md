# Round 4 knowledge (dataathletechamp)

**Final (submission `71380109`):** Paweł's `r3_final.py`. Its copy is
`strategies/round_4/dataathletechamp/r4_final_pawel_r3_final.py`.
- Validation 1,420,312; public R4 860,599; **private 1,250,605, 37th of 52**. Overall the team finished
  **30th of 61** (weighted z −2.00).
- Start with [round4-retrospective.md](round4-retrospective.md), then
  [r4-validation-feedback.md](r4-validation-feedback.md) for every upload and decision rule.
- After the competition: [data-release-fair-price-regimes.md](data-release-fair-price-regimes.md).
  The organisers' released tapes reproduce all our official scores exactly. The note also covers the
  hidden fair price and the regimes, including the 3-second lull before every burst.

## Market and data

| Note | What it holds |
|---|---|
| [r4-opening-profile.md](r4-opening-profile.md) | R4 public tape profile: momentum, volatility, incumbents |
| [r4-market-diagnosis.md](r4-market-diagnosis.md) | Diagnosis: early stop, trend context, toxic touch maker |
| [r4-bot-fingerprints.md](r4-bot-fingerprints.md) | One generator, TWAP and ladder bots, DEEP8 deep-insert signal |
| [r4-oracle-gap.md](r4-oracle-gap.md) | Perfect foresight vs U7: late entry 71%; execution is timing, not caps |
| [r4-u2-trade-anatomy.md](r4-u2-trade-anatomy.md) | Exact fills: spread costs, whipsaws, jump seconds; anti-chop rejected |
| [data-release-fair-price-regimes.md](data-release-fair-price-regimes.md) | After the round: released tapes, hidden fair price and regime timings |

## The follower line

| Note | Step |
|---|---|
| [r4-trig2-candidates.md](r4-trig2-candidates.md) | TRIG2 on R4 (U2/U3), synthetic stress test |
| [r4-jump-onset.md](r4-jump-onset.md) | Jump-onset detector from order-id gaps (U5/U6) |
| [r4-jump-burst-probe.md](r4-jump-burst-probe.md) | Engine burst probe, tuning, TWAP overlay rejection |
| [r4-validation-feedback.md](r4-validation-feedback.md) | Uploads U1–U9 and Paweł's file; paired B comparisons; final choice |

## Rejected or absorbed

| Note | Result |
|---|---|
| [r4-alpha-refit.md](r4-alpha-refit.md) | Gate refit including R4 loses even in-sample |
| [r4-trend-rules.md](r4-trend-rules.md) | Trend holds and filters: noise or worse |
| [r4-reversal-triggers.md](r4-reversal-triggers.md) | Reversal triggers lose; R4 noise band ±25k |
| [r4-burst-study.md](r4-burst-study.md) | Bursts above 100 lots after huge orders do not pay |
| [r4-hidden-ioc-precursor.md](r4-hidden-ioc-precursor.md) | Hidden IOCs precede big moves (mostly a volatility regime) |
| [r4-hidden-triggers.md](r4-hidden-triggers.md) | Hidden-IOC triggers on U2: all rejected |
| [r4-burst-predictor.md](r4-burst-predictor.md) | Trade-window ML predicts volatility, not bursts; cancels follow |
| [r4-deep8-trigger.md](r4-deep8-trigger.md) | DEEP8: real, but the follower already holds that side |
| [r4-different-families.md](r4-different-families.md) | Oracle imitation, skewed maker, literature review, R4 TRIG2 table, sniping-pool ceiling |
