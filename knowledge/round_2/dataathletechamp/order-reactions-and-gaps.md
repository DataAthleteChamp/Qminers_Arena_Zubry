# Order reactions: observable fragility, not a news oracle

**Yes:** visible order additions, consumption, withdrawal, depth and price gaps
can indicate vulnerability before another execution. **No:** this venue gives
no newsfeed, authenticated asset identity or scheduled announcement times.
Trump/Iran is an analogy, not a signal we can import.
External orders are anonymous MARKET-tagged tape orders, not identifiable people
or other competing teams. The tape does not strategically react to our orders,
although our fills mechanically consume available liquidity.
Cancel/shrink only **our** orders; we cannot delete others' book entries.

## Four verified sources, and what was actually read

**Cartea, Donnelly, Jaimungal, Enhancing trading strategies with order book
signals, Applied Mathematical Finance25(1),1--35(2018).**
[DOI](https://doi.org/10.1080/1350486X.2018.1434009),
[KCL accepted manuscript](https://kclpure.kcl.ac.uk/ws/files/115267447/Enhancing_Trading_Strategies_CARTEA_Accepted_24_Jan_18_GREEN_AAM.pdf).
Read accepted24Jan2018 main sections1--5, equation1, section2.2/figures4--5,
controls13 and section4.3/equation17; appendices/proofs not audited.
Nasdaq calibrationJan--June2014/testJuly--December. Authors relate imbalance
to aggressive direction and **10ms after-trade** responses. Zero-latency/
initially certain fills and later Bernoulli fills are not our FIFO matcher;
this does not prove pre-onset warning. Publisher403; no final-body verification
or permissive redistribution licence verified. No copied implementation.

**Huang, Lehalle, Rosenbaum, Simulating and analyzing order book data:
The queue-reactive model.**
[arXiv1312.0563v2](https://arxiv.org/abs/1312.0563v2),3September2014;
JASA110(509),107--122(2015),
[DOI](https://doi.org/10.1080/01621459.2014.982278).
Read main1--4, especially queue generator2.1, intensity2.3/cross-side2.4,
cancellation assumptions2.5 and reference-price transitions3.1--3.2.
Proof/final-body audit not complete. State-dependent arrivals and depletion
motivate a small hazard model; historical flow is an extension, not the basic
state-only model. Large-tick Euronext2010--March2012 and assumed cancellation
selection do not calibrate our fills. ArXiv nonexclusive distribution grant,
not a CC implementation licence; HTML2026 display date is not version history.

**Farmer, Gillemot, Lillo, Mike, Sen, What really causes large price changes?**
[cond-mat/0312703v2](https://arxiv.org/abs/cond-mat/0312703v2),15April2004;
Quantitative Finance4(4),383--397,
[DOI](https://doi.org/10.1080/14697680400008627).
Read v2I--VII/openingVIII, equations/tables/captions; plots/rest conclusion
not audited. Sixteen LSE SETS stocks1999--2002, fully transparent book.
Authors distinguish size's effect on **probability of a move** from magnitude
conditional on moving. Empty best level reveals a gap; canceling the last
best order can have the same quote effect as trading it. These are event/
contemporaneous findings, not calibrated post5ms warning. Assumed arXiv
nonexclusive grant, no verified general reuse licence.

**Lv, Li, Zhou, Liquidity withdrawal before scheduled macroeconomic
announcements, Economics Letters268,113256(October2026).**
[DOI](https://doi.org/10.1016/j.econlet.2026.113256),
[publisher](https://www.sciencedirect.com/science/article/pii/S0165176526004520).
Authentic online19September2026; **abstract/highlights/metadata only** read.
Openaccess CC BY4.0; PDF browser challenge/text endpoint400 prevented body
reading, not a demonstrated paywall. Abstract reports78announcement times
in2024 E-mini data. Final10s **before** release: depth-8.7%, spread+5.3%
relative to minutes1--10 before. First10s **after** release:31.2% execution
depletion and64.0% cancellation/non-trade quote-update contributions to absolute
adjustment. Fifty-eight release-free control windows. Do not call64% a proven
pre-release cancellation share, intention, or causal trading edge.

These are verified external claims/read scopes, not actual Qminers profit.
No external code/notebook was executed or unlicensed material copied.

## Measurement before more models

Aggregate all same-price MARKET orders, exclude our liquidity. Order ID is not
participant identity. First-seen age is censored; disappearance outside the20tick
window is not cancellation. Reconcile actual Trade makerIDs/quantities before
calling removals execution; unresolved withdrawal stays UNKNOWN.

Raw event OFI is in **lots**. The supplied+/-0.3 threshold has unspecified
normalization; do not paste it as a raw-lot gate.
Separate price-level relocation, additions, executions and confirmed removals.
Matched maker quantity is not requested IOC volume.

If bid depth45 disappears and next occupied bid is3ticks lower, best bid moves3;
with ask unchanged midpoint moves1.5, **not3**. No second level within20ticks
is censored, not an infinite gap. Gap warning need not predict the jump sign
correctly, but must precede the action's actual effectiveness.
Record0--5ms, post5ms, late/missed warnings and false alarms; recognizing a
jump underway is not avoiding its first move.

## Current bounded implementation

Start from the reproduced Grid, not the validation-failed risk/Ridge.
`grid-fragility-v1` freezes a flags0 equivalence control, FIFO replenishment,
then the same replenishment plus finite visible gap protection.
Keep old accepted same-price head; add deficit>=8 as a separate child, max2
children/price and6/side. Aggregate quantity and all cancel/submit-pending
residuals remain under the same100 envelope.

Warned side: aggregate L1<=100 and next observed distinct gap>=2; cap its
state-specific per-level quantity at12. Other side stays unchanged. No new
directional target, quote-price formula, wall anchor or news time.
When oversized, cancel younger accepted children first; retain an eligible head
where possible. Old quantity remains reserved until actual terminal ACK.
These constants are a predeclared test, not optimized gap probabilities.

Actual paired liquidation-net PnL decides whether protection beats lost fills,
FIFO and inventory costs. AUC, fewer orders and higher surviving-fill averages
do not. A is already consumed; B is outcome-only selection feedback; C blinded.
No new B market-statistics inference or automatic Final switch.

## Shrink API contract: verified, but not atomic

Two focused official-SDK **synthetic contract tests** passed:

```bash
env -u VIRTUAL_ENV uv run --locked pytest -q experiments/round_2/dataathletechamp/shrink-contract-v1/test_shrink.py
```

Market20 ahead / user50 / market30 behind. A shrink25 at13000us precedes
SELL35 at14000us; own15fills prove old FIFO priority survives.
In a second fixture, a pre-modification SELL fills40, leaving10; requested25
then becomes invalid and produces **no MODIFIED ACK**. A later fill leaves9,
which the private partial-fill message correctly reports.

Thus never replace reserved remaining quantity with requested shrink quantity.
Partial fills can already satisfy the reduction; an implementation must handle
that obsolete request without getting stuck waiting forever. Current trading
prototype uses cancel-ACK-replace, **not an untested modifier-pending state**.
Synthetic tests establish mechanics, not competition profitability.
