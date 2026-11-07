# Round 2 source wave 2: validate the claims before importing mechanisms

Completed two further bounded read-only threads on 2026-11-07:
the three named newer publications, and the three named public implementation/
competition resources. No private tape, code, strategy or score was sent in
external queries. No downloaded code/notebook was executed or copied.

Read with [the theory audit](source-audit-theory-v1.md),
[actual fill evidence](execution-diagnostics.md) and
[the independent risk screen](jump-risk-model.md).

## Newer papers: bibliography verified, full-text mechanisms not verified

None of these three substantive full texts was retrieved. Publisher abstract,
highlights, metadata and rights checks support the author-reported claims below,
not unread equations, empirical identification or a causal stress-time rule.

**Ke Xu, High frequency market making during stressed periods (2023),
International Review of Economics & Finance 87, 379--397.**
[Publisher](https://www.sciencedirect.com/science/article/pii/S1059056023001533),
[DOI](https://doi.org/10.1016/j.iref.2023.05.001).
Read metadata, complete abstract, acknowledgement/version footnote and Crossref
record. Earlier title is reported as Who makes the market during stressed
periods? HFTs vs. Dealers; prior manuscript date UNKNOWN.
Author reports less **volume traded at narrow spreads**, including intermittent
participation. This is not necessarily smaller individual posted quotes.
Empirical sample dates and identification UNKNOWN from material read.
All rights reserved; no open reuse licence verified.

**Corey Garriott, Vincent van Kervel and Marius Zoican, Queuing and inventories
in limit order markets (2025), Journal of Financial Markets 75, 100982.**
[Publisher](https://www.sciencedirect.com/science/article/pii/S1386418125000229),
[DOI](https://doi.org/10.1016/j.finmar.2025.100982),
[institution record](https://investigadores.uandes.cl/en/publications/queuing-and-inventories-in-limit-order-markets/).
Read metadata, highlights, abstract, data statement/version footnote and Crossref.
PDF browser challenge and XML 401 prevented body verification.
Authors report Canadian futures queue/inventory interactions and crowding out,
not a general stress-time size-versus-spread comparison or a universal
negative-value gradient at every queue's rear. Exact contracts, dates,
identification and robustness UNKNOWN. Prior title Do high-frequency market
makers share risks?, prior manuscript date UNKNOWN.
Published CC BY-NC-ND 4.0; authors cannot share their underlying data.

**Seyoung Park, Bong-Gyu Jang, Jin Gi Kim, Ho-Seok Lee and Sam Beatson,
Short-term market changes and market making with inventory (2026),
Operations Research Letters 69, 107517.**
[Publisher](https://www.sciencedirect.com/science/article/pii/S0167637726001148),
[DOI](https://doi.org/10.1016/j.orl.2026.107517).
Read abstract, metadata, keywords, data statement and Crossref November issue
record. Nottingham manuscript pointer returned 403; assumptions/objective/FIFO
and terminal conditions were not verified. The publication explicitly reports
**no data used**: it is not a new empirical stress confirmation.
Publisher all rights reserved; no open manuscript licence verified.

**Conclusion:** verified existence is not verified causal or executable
performance. Quantity-first is a falsifiable design choice, not something these
abstracts prove dominates widening on this tape. Test both under the same risk
trigger before asserting superiority. Theory utility/risk benefits and lower
depth do not establish higher raw net competition PnL.

For marginal lot j, use a consistent horizon/unit:
`P(fill_j) * E[signed fill value | fill_j] - inventory shadow cost - lost FIFO value`.
Inventory reduction can have negative shadow cost. Do not subtract liquidation
or penalties twice if already included in fill value. Infinitesimal-order value
cannot simply be multiplied by 100/200: partial fills, position and liquidation
depth vary across marginal lots.

## HftBacktest: pin the tutorial and inspect its execution assumptions

[GLFT Market Making Model and Grid Trading](https://hftbacktest.readthedocs.io/en/latest/tutorials/GLFT%20Market%20Making%20Model%20and%20Grid%20Trading.html):
Read complete rendered text/code and pinned notebook measurement/grid cells
4,6,44,45,48 (zero-based); plots/results not independently reproduced.
Read the Docs successful build 30795001 pins latest deployment to
`5f3ec40b2afb764e0fea112f941ed85523ef4e88`.
The tutorial explicitly preserves a **half-tick versus tick intensity-indexing
error** to keep its published results. Do not copy fitted intensity parameters
or treat crossing-depth counts as our fill probability.

[Extreme-condition price protection, py-v2.0.0](https://hftbacktest.readthedocs.io/en/py-v2.0.0/tutorials/Risk%20Mitigation%20through%20Price%20Protection%20in%20Extreme%20Market%20Conditions.html):
Tag `4f0844fb8f3bb108246a89d9fcc2b038b79c3df0`.
Entire notebook is one markdown cell, ending with example-to-be-added:
**there is no implemented tested protection strategy there**. Spot/futures,
last/mark dislocations and feed-latency deterioration are different assumptions
from a single anonymous instrument with documented action delay.

[Market Making with Alpha - Order Book Imbalance, py-v2.4.2](https://hftbacktest.readthedocs.io/en/py-v2.4.2/tutorials/Market%20Making%20with%20Alpha%20-%20Order%20Book%20Imbalance.html):
Tag `07f8f1d3468d619ae4c57e4ed32fc3a2ffce5708`.
Read whole rendered page and pinned cells 0,1,2,5,8,9,12,14,15.
Implemented alpha standardizes raw depth difference; it is not identical to
introductory normalized QI or event OFI. Read pinned docs/order_fill.rst 1--187
and docs/latency_models.rst 1--65.
MIT licence verified at all three revisions; no code copied.

Its models infer fills against exogenous historical observations without
consuming subsequently replayed depth. Even its partial-fill model leaves
market depth unchanged; no-partial-fill taking can ignore displayed quantity.
These are **not** the organizer's actual price-time matcher.
Fixed external submissions here mean no endogenous market response, not
inexhaustible liquidity: our fills mechanically consume aggressor quantity or
resting market orders. Do not reuse old historical execution as an extra fill
budget after our intervention.

At a one-tick integer spread there is no strictly inside-spread price.
Decision-time passive pricing is not arrival-time post-only/GTX protection:
only LIMIT/IOC are documented, and delayed LIMIT can cross.
Do not transplant rebates, 100ms/500ms/1s decision clocks, control-frequency
latency, spot/mark hedges or undocumented variable feed latency.

## Two public repositories: their evidence is not ours

**lucaspaulien/crypto-market-making**, commit
`5b2c936b6d5085cb90962e22e9c5ce09de1c59f8`:
[README](https://github.com/lucaspaulien/crypto-market-making/blob/5b2c936b6d5085cb90962e22e9c5ce09de1c59f8/README.md),
[accounting](https://github.com/lucaspaulien/crypto-market-making/blob/5b2c936b6d5085cb90962e22e9c5ce09de1c59f8/src/mmsim/pnl.py#L1-L118),
[execution](https://github.com/lucaspaulien/crypto-market-making/blob/5b2c936b6d5085cb90962e22e9c5ce09de1c59f8/src/mmsim/simulator.py#L104-L230).
Read headline, simulator, latency, correctness/limitations; accounting 1--118;
execution 1--41 and 104--230. Results/tests/data not reproduced.
Front-versus-back proxy queue differences exceeding quote-formula changes are
an **author report**; "front" is expressly an optimistic bound.
Trade-through/crossed-book full fills and disclosed in-flight overshoot cannot
be imported into our evaluator. MIT licence read; no code copied.

**Durpie-Git/imc-prosperity-4**, commit
`9d8079e06c8e3553d37fade4d55f75b4035f36ae`:
[writeup](https://github.com/Durpie-Git/imc-prosperity-4/blob/9d8079e06c8e3553d37fade4d55f75b4035f36ae/README.md).
Read lines 1--15,232--305,524--551,1091--1104 and wall/heading locations.
Fourth global/algorithmic ranking is self-reported, not organizer-independent
verification. Wall Mid is dominant bid/ask-wall midpoint, linked there to
Prosperity's internal valuation using unrealized-PnL probing; later hardcoded
anchor failure is also reported. That valuation mechanism is not our
opposite-market-depth liquidation.
No licence found in complete repository tree. No implementation, figures or
selection thresholds copied.

Persistent walls may be an additional causal diagnostic; size/persistence is
not proof of an informed fair value, spoofing or hidden bot identity.
Reject deployment before demonstrating incremental post-arrival information.

## Consolidated next experiments

First test the [frozen risk overlay ladder](jump-risk-model.md): same R1 price
alpha/common hard100, volatility versus full risk-based quantity control,
then triggered one-tick symmetric widening under the same full detector.
This directly tests the unproved quantity-versus-width claim without a grid.

Preserve a safe old FIFO head where possible; trim by canceling younger
accepted children first. Partial shrink may preserve matcher priority, but
failed-modification acknowledgement/race handling must be resolved before using
it to release reservations. Keep every pending quantity fully reserved.

Park persistent-wall pricing, full GLFT intensity fitting, copied queue
probabilities, downloaded notebook strategies and intentional >100 exposure.
Actual full-state net PnL/reproduction outranks research sophistication,
surviving-fill averages, external profits or AUC.
