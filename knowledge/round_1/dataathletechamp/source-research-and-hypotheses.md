# Source research, mechanisms and tested hypotheses

This consolidates the three source-research threads and their data-informed
follow-ups. Papers/repository opinions are references, not executable evidence.
Two implementation workers failed at model connection before producing code;
their approved experiments were completed directly in separate owned worktrees.

## Primary-paper wave: verified read depth

| Source | What was read | Transfer and limitation |
|---|---|---|
| Avellaneda-Stoikov2008, DOI10.1080/14697680701381228 | Published PDF §§2.1-2.5,3.1-3.2, equations8,12,29-30 | Inventory affects quote value; Brownian/exponential-fill/midpoint-terminal assumptions do not reproduce this game |
| Cartea-Donnelly-Jaimungal2018, DOI10.1080/1350486X.2018.1434009 | Accepted manuscript §§3.1-3.3, Eq13, reduced-fill Eq17 | Large-tick order signals and adverse selection; front-of-queue/zero-latency base assumptions need actual FIFO testing |
| Guéant-Lehalle-Fernandez-Tapia, arXiv1105.3115v4 | §§2-5, bounded-inventory quotes and stationary limits | Unit-fill theoretical model, not a justification for linear size/PnL scaling or flat threshold charges |
| Moallemi-Yuan2017, Columbia record | Abstract independently verified | Static adverse selection plus dynamic queue optionality; full calibration not performed |
| Gao-Wang2020, DOI10.1080/14697688.2020.1741670 | Supplied reference; publisher returned403 | No claim that its full model or equations were independently read |

Primary links:

- https://math.nyu.edu/~avellane/HighFrequencyTrading.pdf
- https://doi.org/10.1080/1350486X.2018.1434009
- https://arxiv.org/html/1105.3115v4
- https://business.columbia.edu/faculty/research/model-queue-position-valuation-limit-order-book
- https://doi.org/10.1080/14697688.2020.1741670

Risk-aversion parameters are preferences/experimental choices, not organiser
constants. We do not solve an HJB or claim these approximate controls are optimal.

## GitHub wave: pinned source and licence checks

- `jmerle/imc-prosperity-2` at
  `70c8777c5e22608814bb3fd947f4fc51bec45083`, `src/submissions/round1.py:140-235`:
  inventory/capacity allocation and reported failed regression improvements.
  MIT verified. IMC's snapshot execution is not delayed persistent Qminers orders.
- `TimoDiehm/imc-prosperity-3` at
  `6bbc3abfb1f81cb1c8710fdb0b291079ce943202`, README169-264/879-908 and
  `FrankfurtHedgehogs_polished.py:101-224,275-381`:
  take/clear/make and fair-price reasoning. No licence detected; ideas only.
  A wall-mid from outer prices is not authenticated fair value with20-tick visibility.
- `obalcells/ReadyTraderGo2023` at
  `f6d8d463ef7d7d8ead846e06ab0a41e80ec91520`,
  `ready_trader_go/order_book.py:106-176,242-273`:
  FIFO partial-fill/reduction behavior. AGPL verified; no code copied.
  Its example releasing current IDs on cancel send is a negative lifecycle lesson.

Repository outcomes are author reports/static inspection, not independently
rerun trading performances. Our implementation is own code on the official API.

## Public market-structure wave

- Headlands [Quantitative Trading Summary](https://blog.headlandstech.com/2017/08/03/quantitative-trading-summary/),
  full educational article: book pressure, trade impulse and production reconciliation.
- Optiver [adversarial research](https://www.optiver.com/insights/technology-blog/machine-learning-in-trading-an-adversarial-research-problem/),
  full substantive article: conditional fills, silent counterfactual and venue differences.
- CME [Market by Order](https://www.cmegroup.com/articles/faqs/market-by-order-mbo.html):
  indexed excerpts only; full fetch failed. No CME amendment rule imported.

A large-tick FIFO book is a useful structural analogy to order-driven equities,
futures or some FX venues. Anonymous prices/orders do not authenticate a ticker,
currency, contract multiplier, exchange or exact generating distribution.
Real firms' adaptive counterparts, credit, fees and gateways do not all exist here.

## What the data justified

Best-queue imbalance and short volume flow predict later midpoint changes.
The clean0.5-second ridge fit uses ONLY targets actually before4800s. Mean
absolute prediction is approximately0.235ticks, below the usual aggressive
round-trip spread. Passive quote choice/sizing deserves testing; blind taking does not.

Initial fitting used nominal horizon to test the cutoff. Audit found one
0.5-second target after4800s (also exploratory1/5-second boundary issues).
Final ridge coefficients were corrected using ACTUAL target timestamps.
All old results remain recorded. Correction did not retune policy parameters
against final outcomes; corrective tests use already-consumed data, not a new holdout.

## Hypotheses and outcomes

1. **Inventory/depth maker:** actual positive PnL, including liquidation and fees=0;
   matched100-size validation depth gain14742 over midpoint.
2. **More quote capacity within the band:** large part of profit improvement.
   Size/cap are confounds; do not call the whole gain prediction alpha.
3. **FIFO-preserving bounded top-up:** retain old partial-fill priority, add at
   most one tail order per side; joint reservations include all in-flight residuals.
   Matched95-size validation gain2458; useful, not a universal queue theorem.
4. **Ridge size tilt:** quote-time forecasts rank actual-fill markouts, but
   incremental execution gains are small/mixed. Keep as a tested alternative.
5. **One-tick hysteresis / hard side gate:** inferior discovery results;
   retained experiments rather than threshold-rescue on the final block.
6. **Hierarchical forecast reconciliation:** disjoint increments add; common-fit
   linear forecasts were already coherent to about1e-15ticks. No new alpha created.
7. **Monte Carlo:**500 coefficient-block resamples and5000 paired PnL-block
   resamples describe conditional sensitivity only. No independent tapes or P(win).
8. **Deliberate breaches:** parked. No calibrated incremental recovery/occupancy
   advantage supports a300-900lot out-of-band mode. Inclusive100 is free, not1000.
9. **Fixed10000 anchor, terminal schedule lookup, exact asset identity:** unsupported.

The queue/top-up files retain legacy `HYSTERESIS` and `MIN_REST_US` globals from
their baseline, but their replaced top-up update method does not consume those
two controls. Do not assume changing them activates the old experiments.
Those complete variants remain in the experiments folder; use a new version
and validation before enabling another cancellation policy.

## Economic decomposition and uncertainty

Recommended queue maker: actual PnL343269, independently reconciled.
Against an approximate50ms null-market midpoint reference, diagnostic capture
is922299, carry is-578983 and terminal-liquidation adjustment-47.
Their exact identity is343269; the split is not proof of causal alpha.
It demonstrates why spread capture alone overstates what survives adverse moves.

Ridge minus queue: validation delta-37, conditional60-second block range
[-3429,3542]; final-block delta-1896, range approximately[-5150,1479].
These are selected-tape resampling ranges, not independent confidence guarantees.
The tiny full-public ridge lead does not establish private-market superiority.

## What remains unknown

Private tape, responsive market impact, fresh-regime performance, exact asset
identity and mathematically global maximum. Server static/sandbox validation and
human Final selection still need to happen. No strategy was uploaded automatically.
