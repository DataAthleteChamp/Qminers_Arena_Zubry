# Linked instruments, baskets and derivatives

**Status: use only if the released instruments justify the structure.**

Current Arena replays one anonymised instrument. Multi-asset/derivative ideas are
background knowledge, not deployable hedges in the current interface.

## Structural versus statistical

A contract-defined payoff/composition relation is stronger than a fitted price
correlation. Even a true relation does not guarantee simultaneous execution,
financing, available shorting/hedging or profitable fees. Statistical baskets
need stable held-out residuals, not a good regression on all observed levels.

## Minimal candidates

- Known composition: derive synthetic fair from executable legs and all costs.
  Test passive-lean versus aggressive multi-leg execution with explicit leg risk.
- Statistical relation: use the simplest residual model and fit coefficients
  only on past data; see the mean-reversion card.
- Binary payoff: start from `E[payoff | current information]`, with bounds,
  expiry convention, dependence and collateral specified by the actual rules.
- Options: use parity, monotonicity/convexity and a justified pricing model only
  when the payoff, measure, dynamics and tradable hedges support it.

Do not import Black-Scholes/Margrabe drifts, a vol surface or continuous delta
hedging into a physical-generator, unhedgeable binary game by habit.
Verify analytic pricing against an independently coded reference or Monte Carlo
under the SAME stated generator. A correct pricer still needs execution validation.

## Tests and stops

Known-answer payoff/expiry/boundary tests; conservation/no-arbitrage where the
contract actually implies it; covariance/leg risk; fees/financing; discrete ticks;
held-out combined PnL; stress hedge outages and relationship breaks.
Stop if a required hedge, payoff identity, capital rule or pricing assumption fails.

## Sources

`own-imc`: conditional cluster hybrids and a near-constant basket relation,
with profit constrained by position limits and dominated by another product.
`akuna-public-task`: participant-published binary/RFQ/FOK/collateral description,
not official Qminers rules and not licensed code to copy.
`avellaneda-lee-primary`: statistical factor residuals, not a guarantee of arbitrage.
`headlands-system-and-signals`: model-based pricing plus execution costs/queue issues.
