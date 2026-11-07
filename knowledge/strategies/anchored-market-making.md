# Anchored fair-value making and taking

**Status: conditional strategy hypothesis. Confirmed mechanics are in `competition.json`.**

## Signature and mechanism

A reference price/payoff stays stable across comparable periods, deviations are
large enough relative to executable costs, and the reference is observable before
trading. A fixed price-looking name or low in-sample variance is not enough.
Liquidity provision may earn spread; taking may capture stale relative prices.

## Minimal candidate

Let estimated fair value be `f`, position `q`, and a fitted inventory coefficient
`k`. A candidate quote center is `r = f - k*q`, with side-specific cost/selection
buffers and limits. Compare `k=0` with small alternatives; skew is not free alpha.
Take only when expected value at the executable price clears costs and uncertainty.
Exit/clear logic must respect fees, terminal valuation and risk.

Avellaneda-Stoikov's reservation-price reasoning assumes a particular Brownian
price/utility/fill model. A nearly fixed payoff can make those variance assumptions
inappropriate. Never port its coefficients or horizon units without checking them.

## Evidence required

- Window/source and uncertainty of the anchor; held-out anchor error.
- Net PnL versus a small simple baseline, realistic fills and fees.
- Time at position limits, capture/carry attribution, concentration by day.
- Ablation of the anchor/skew; nearby parameter plateau.
- Stress: anchor shift, one-sided flow, depth loss, late-session valuation.

## Stop conditions

Reference health breaks, persistent adverse markouts, inventory becomes stuck, or
cost/execution assumptions fail. Reduce/disable using a predeclared rule; do not
silently replace the anchor with a new guess.

## Sources

`avellaneda-stoikov`: inventory model and assumptions.
`frankfurt-hedgehogs`: competition-specific take/clear/make example; ideas only
unless licence permission is verified.
`own-imc`: actual component-level hybrid design and concentrated realized PnL.
One exceptional product-day is not replication.
