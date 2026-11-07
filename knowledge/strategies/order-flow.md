# Order-flow and imbalance overlays

**Status: investigate only if the released data supports causal signals.**

## Distinguish the quantities

Static BBO imbalance is `I = (Q_bid - Q_ask)/(Q_bid + Q_ask)` when depth is non-zero.
Event-based order-flow imbalance includes additions, cancellations and trades;
it is not interchangeable with a snapshot size ratio.

Gould-Bonart motivates a simple baseline:
`P(next mid move is up | I) = sigmoid(beta0 + beta1*I)`.
Cont-Kukanov-Stoikov studies contemporaneous flow/price impact; that alone does
not establish a lagged prediction or net trading edge.

## Causal protocol

1. Define observable features at the actual decision time and feasible horizon.
2. Define labels independently of a future-aware decision sampling rule.
3. Fit coefficients/normalization on past observations only.
4. Evaluate later periods against constant-probability/midpoint/simple baselines.
5. Check calibration and loss, then executable after-cost PnL and conditional fills.
6. Ablate the signal and assess decay, latency, depth and regime sensitivity.

The original queue-imbalance paper samples inside intervals bounded by successive
future price changes and randomly splits pooled observations 80/20 (Sections 5.1-5.2).
That supports a research hypothesis, not a ready-made causal stopping rule or
chronological deployment test. Direction prediction also lacks move magnitude:
a high hit rate may still fail to cover the spread.

## Stop/failure modes

Bid-ask bounce, feature/label alignment, changing event rates, stale depth,
non-stationarity, a coefficient that reverses out of sample, or effects smaller
than execution uncertainty. Counterparty identity stories need explicit IDs and
held-out evidence; never hunt hidden schedules or manipulate the book.

## Sources

`gould-bonart-queue-imbalance`: primary abstract/data/methods, not profit evidence.
`cont-order-flow`: distinguish explanation of current moves from prediction.
`queue-reactive-model`: state-dependent event intensities under calibrated assumptions.
`optiver-market-data`: irregular event time and temporal context.
