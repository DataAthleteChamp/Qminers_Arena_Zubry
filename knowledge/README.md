# Curated research, not a strategy zoo

`sources.json` is the canonical public reference index: links, reviewed versions,
read depth where available, use, licence notes and limitations. It was generated
with `tools/import_sources.py` from the research audit; private entries were
excluded. No reference implementation, raw market archive or paper PDF is vendored.

## Current competition facts supersede pre-event unknowns

Use `../competition.json` and the official starter for actual mechanics: one
anonymised instrument, event callbacks, 5 ms actions, persistent orders, no fees,
100-lot penalty threshold, 1000 acceptance wall and liquidity-based markout.
These cards are reusable research hypotheses, not active private-round strategies.
The previous synthetic research-engine demo was NOT copied into this repository.

## Reading order

Humans: [one-page menu](../docs/human/PLAYBOOK.md).
Agents: [research contract](../docs/agent/RESEARCH.md), relevant card, then its
source sections. Source IDs in cards refer to `sources.json`.

| Card | References to inspect |
|---|---|
| [Anchored making](strategies/anchored-market-making.md) | `avellaneda-stoikov`, `frankfurt-hedgehogs`, `own-imc` |
| [Adaptive making](strategies/adaptive-market-making.md) | `headlands-system-and-signals`, `optiver-adversarial-research`, `hftbacktest-fill-models` |
| [Order flow](strategies/order-flow.md) | `gould-bonart-queue-imbalance`, `cont-order-flow`, `queue-reactive-model` |
| [Mean reversion](strategies/mean-reversion.md) | `avellaneda-lee-primary`, `prosperity-concentration`, `pbo-primary` |
| [Trend/regimes](strategies/trend-and-regimes.md) | `une-baguette-fromage`, `alpha-search-process`, `optiver-market-data` |
| [Linked assets/payoffs](strategies/linked-assets-and-payoffs.md) | `own-imc`, `akuna-public-task`, `avellaneda-lee-primary` |

## Public company context

- [Headlands summary](https://blog.headlandstech.com/2017/08/03/quantitative-trading-summary/):
  educational architecture, signal/model/rule combination, capture and reconciliation.
  Historical overview, not a current proprietary strategy.
- [Optiver adversarial research](https://www.optiver.com/insights/technology-blog/machine-learning-in-trading-an-adversarial-research-problem/):
  conditional fills, counterfactual execution and changing markets.
- [Optiver agentic engineering](https://www.optiver.com/insights/technology-blog/engineering-the-agentic-sdlc/):
  context, observable failure, programmatic gates and human risk judgment.
- [Optiver iteration design](https://www.optiver.com/insights/technology-blog/designing-for-latency-and-iteration/):
  shared research/production behavior and explicit iteration cost.

These are public practitioner descriptions, not independently reproduced alpha.
We borrow verification principles, not an enterprise orchestration platform or
an assumption that deep learning, microsecond latency or native code is required.

## Evidence discipline

1. A source must answer a diagnosed question.
2. Record exact section/version and what was actually read.
3. Check model assumptions, units, timing and available hedges before formulas.
4. Observe/falsify on our fitting data; freeze the candidate before held-out tests.
5. Keep negative results. Popularity and self-reported ranks are not profit proof.
6. Every empirical threshold/table needs a checked-in derivation and fitting window.
7. Respect [third-party boundaries](../THIRD_PARTY.md) and current Technical Rules.
