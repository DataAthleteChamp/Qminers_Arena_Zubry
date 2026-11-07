# Trend, drift and regime-aware selection

**Status: do not infer persistence from one favorable path.**

## Signature and candidate

A drift persists across comparable periods, is visible before positions are
chosen, and clears execution/capital costs. Compare a bounded directional
position/hold policy against any active overlay. A busy maker may forgo the drift
or repeatedly sell the winning inventory.

Fit drift and regime diagnostics only on past observations. Prefer a simple
observable health monitor to a complex detector trained on hindsight labels.
Explicitly define when it stops adding risk, reduces exposure or disables a component.

## Evaluation

- Held-out directional performance versus hold/no-signal baselines.
- Attribution separates intended carry from spread capture.
- Opposite drift, jumps, widened spreads, terminal valuation and position-cap stress.
- Compare performance by session/product, then remove the largest contributor
  for diagnosis. Concentration is not automatically wrong and has no universal cutoff.
- Validate the combined portfolio and its pending-order worst-case exposure.

## Failures

Calling a deterministic-looking training path a law; mistaking changing anchors
for mean reversion; lagging regime labels; selecting a switch on the held-out day;
or assuming later rounds preserve earlier mechanics.

## Sources

`une-baguette-fromage`, `prosperity-concentration`, `alpha-search-process`:
competition mechanisms, carry/capture, rejected signals and concentration.
Outcomes are external author reports, not independently rerun evidence.
`optiver-market-data`, `optiver-adversarial-research`: public descriptions of
non-stationarity, conditional execution and decay.
