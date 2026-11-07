# Adaptive fair-value market making

**Status: candidate baseline, not a default profitable strategy.**

## Signature and data

There is no defensible fixed anchor. Current prices, depth, events and related
instruments may help estimate a short-horizon fair value. Confirm whether data is
L1, aggregate L2 or individual-order L3; do not infer missing queues or identities.

## Minimal candidate

Start with midpoint as a baseline. A simple size-weighted BBO heuristic is
`(ask*bid_size + bid*ask_size)/(bid_size + ask_size)` when depth is available.
This heuristic is NOT the full estimated dynamic Stoikov micro-price model.
If total depth is zero, mark the feature unavailable; never quietly use zero.

Quotes combine estimated fair, inventory adjustment, tick rounding and a
fee/adverse-selection buffer. Sizing and all outstanding orders pass common risk.
Improving the touch can increase toxic fills; tighter is not automatically better.

## Tests

Compare midpoint, heuristic and any temporal signal using causal observations.
Then compare net executed PnL, not just prediction MSE. Inspect signed markouts,
fill rate by quote distance, holding periods, inventory and capture/carry.
Preserve the same decision code and inspect queue/latency/partial-fill sensitivity.

Adverse selection is conditional: `E[value - price | filled]` can differ materially
from the unconditional model edge. A model's best quotes may be the trades it loses.

## Failures and stop

Queue optimism, stale prices, accumulating inventory in jumps, or an edge entirely
caused by rebate assumptions. No-passive-fill stress removes making itself:
use it for attribution, not an automatic rejection criterion.
Abstention is a candidate only if the actual competition contract permits it.

## Sources

`headlands-system-and-signals`: public educational signals and system architecture.
`optiver-adversarial-research`: conditional execution, venue rules and model decay.
`optiver-market-data`: snapshots versus temporal event dynamics.
`hftbacktest-fill-models`: replay has no self-impact and modeled queue uncertainty.
`jmerle-backtester`: IMC-specific fill switches, not Qminers matching rules.
