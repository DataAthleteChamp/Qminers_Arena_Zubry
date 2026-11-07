# Round 2 source wave 1: six mechanisms, not transferred profits

Two bounded read-only research threads completed 2026-11-07, one on
volatility/inventory/queue control and one on jump/depletion forecasting.
Parent owns actual data and execution evidence. External queries contained
public bibliographic terms only: no private tape, strategy, parameters or scores.
No external strategy code or notebook was copied or executed.

Primary-source sections below were actually read by the source researchers.
Unreviewed appendices and empirical sections remain unreviewed. A paper's
finding is author-reported evidence in its own environment, not an authenticated
human approval or an executed R2 comparison.

## Inventory, queue and latency

**Ching, Gu, Siu and Yang, Trading Strategy with Stochastic Volatility in a
Limit Order Book Market, arXiv 1602.00358v1, 1 February 2016.**
[Primary version](https://arxiv.org/html/1602.00358v1).
Read sections 2.1--2.3, 2.4.3 and 3.1--3.4; appendices not reviewed.
Heston variance plus fill-triggered adverse jumps motivates state-dependent
inventory cost. It is not a calibrated model of this venue's independent
catastrophic jumps, finite orders or delayed FIFO.
Importantly, authors report inventory control can lower profit while reducing
dispersion. Utility improvement is not proof of higher raw monetary net PnL.

**Moallemi and Yuan, A Model for Queue Position Valuation in a Limit Order
Book, author PDF, June 2017 revision.**
[Primary PDF](https://moallemi.com/ciamac/papers/queue-value-2016.pdf).
Read pp.1--16, sections 1--3 and Theorems 1--3, beginning of section 4 only.
Empirical validation and appendices not reviewed. PDF SHA256:
`7bbe1016f68d7d47d1dbaf885f968b501c16ef9ea78ca423955ef3d1855aa9fa`.
Queue value combines fill probability, adverse selection and positional
improvement. The infinitesimal-order and proportional-cancellation assumptions
do not value every marginal lot of our 100/200-lot orders, or guarantee a
delayed cancellation avoids a fill.

**Lehalle and Mounjid, Limit Order Strategic Placement with Adverse Selection
Risk and the Role of Latency, arXiv 1610.00261v3, 2 December 2016.**
[Primary version](https://arxiv.org/html/1610.00261v3).
Read sections 2, 4.1, 5.1.1--5.1.2, 5.2 and latency equation 22.
Later v4 not reviewed. Their observation/control-frequency latency differs
from knowing a cancellation decision but waiting for exchange delivery.
Useful retention/adverse-selection structure; not this SDK's cancel-race price.

**Transfer:** separate quantity, price and inventory controls. Shrink/cancel
only according to confirmed SDK semantics; preserve a safe valuable FIFO head
where possible. A smaller soft target never erases live or in-flight exposure.
Volatility is nondirectional risk information. Do not silently add a separate
jump-variance term to an estimator already including observed jumps.

## Depletion, excitation and first-passage risk

**Cont, Kukanov and Stoikov, The Price Impact of Order Book Events,
arXiv 1011.6402v3, 13 April 2011.**
[Primary version](https://arxiv.org/html/1011.6402v3).
Read abstract, section 1.1, 2.1--2.3, 3.1 and beginning of 3.2; no appendix.
Section 2.1 event contribution includes additions, cancellations and trading.
Equations 1--4 relate same-interval price impact to flow and depth.
They do **not** establish a post-5ms forecast. At a queue, equal market-sell
consumption and bid cancellation are mechanically similar; different subsequent
continuation/refill is a hypothesis to test, not a universal sign rule.

**Bacry and Muzy, Hawkes model for price and trades high-frequency dynamics,
arXiv 1301.1135v1, 7 January 2013.**
[Primary version](https://arxiv.org/html/1301.1135v1).
Read section 2.1--2.2, estimation excerpt in 6, 7.1--7.4 and 8; sections 3--5
and appendix proofs not verified. Publisher fulltext access failed; primary
preprint was used. Equation 7 causal intensity and equations 9--11 separate
excitation, impact, reversion and feedback; Proposition 1 provides stability.
Near-instantaneous trade impact is already occurring when detected. The basic
model omits volume and explicit additions/cancellations. Try fixed multiscale
pressure summaries before fitting a large Hawkes kernel matrix.

**Cont and de Larrard, Price dynamics in a Markovian limit order market,
arXiv 1104.4596v1, 24 April 2011.**
[Primary version](https://arxiv.org/html/1104.4596v1).
Read sections 1--3.2, section 3.3 Proposition 3.5/Remark 3.7 excerpt;
section 4 diffusion limit not reviewed. Section 3.1 Proposition 3.1,
equations 3--4 give depletion-time survival; section 3.2 Proposition 3.3,
equation 7 gives eventual next-up probability under balanced flow.
Independent unit-sized Poisson arrivals, constant one-tick spread and no gaps
are not literal R2 assumptions. Borrow first-passage timing/direction framing,
not the fitted closed forms.

**Transfer:** keep actual execution, cancellation and replenishment separate:
at the same price level, `DeltaQ = additions - cancellations - executions`.
IOC request volume is not executed volume; absent-order cancel removes nothing.
When the best price relocates, comparing different queue sizes is not a
mass-balance equation. Stop typed-flow experiments on an unreconciled ledger.

Joint first-passage probabilities of up/down/neither at a fixed barrier can
capture large balanced tails with near-zero mean. Endpoint direction and
first-passage direction are different labels. Predicting a jump already begun
is not pre-jump warning, though it can inform subsequent continuation.

## Consolidated falsifiable mechanism queue

Use the parent's existing first40% / next30% / late30% A protocol, not
inconsistent new thirds or 60/20/20 proposals. Full A is already consumed
diagnostic/selection evidence. Freeze candidate bytes before B; repeated B
rescue/tuning consumes B. C remains unavailable/blinded.

**1. Past-volatility accumulation capacity.** Preserve forecast/quotes/common
hard100 gate; reduce inventory-increasing marginal exposure in high variance.
The actual fill diagnostic supports this premise across all three A blocks.
Compare against the strongest fixed-large controller and, if needed, a fixed
smaller-cap arm to distinguish timing from simply trading less. Reject on
nonpositive total net improvement; drawdown alone does not rescue it.

**2. Side-specific toxicity and FIFO preservation.** Before fitting a learner,
test whether latency-feasible state and marginal/age bins discriminate bad fills.
Do not call QI/flow agreement safe: the actual aligned accumulation bins remain
negative. Preserve a front position only while its expected execution value
remains useful; it is not an excuse to retain a stale toxic quote.

**3. Depletion/replenishment or post-jump embargo.** First reconcile typed
flow; then compare a small typed-pressure warning with the same pooled-flow
model. Optional fixed two-scale extension only after the basic premise survives.
A one-second embargo after a past large move cannot prevent that first move.
Keep lost profitable reversion fills and pre-arrival losses in monetary scores.

Predeclare at most three one-mechanism policy arms, no combined parameter grid.
Future targets must fit entirely inside the fitting window. Require actual
warm-book paired net PnL and exact frozen reproduction, not better AUC,
conditional surviving-fill average or an agent's opinion.

For rare-risk diagnostics, report natural-frequency Brier/log loss,
directional recall/precision, calibration, distinct episode counts and warning
lead. Accuracy dominated by "neither" is misleading; reweighted labels require
probability correction. Sparse directions imply insufficient evidence, not a
license to lower the barrier after seeing results.

## Intentional penalty hypothesis

Necessary incremental condition against the best in-band policy:

`DeltaExpectedGross - 10000 * DeltaExpectedOutsideSeconds - riskReserve > 0`.

Gross includes actual cash and depth liquidation. Outside time includes partial
exit fills, send/cancel latency, missing liquidity, later re-breaches from old
orders and unresolved inventory through tape end. A reserve is our uncertainty
cost, not an organizer fee. Five milliseconds would cost 50 only **if** outside
time were actually five milliseconds.

Park >100 exposure and aggressive IOC intervention until calibrated incremental
net evidence exists under an explicitly declared common risk policy. The 1000
acceptance wall is not a free target. Never alter the evaluator or bypass risk
to improve a score.

## Licences and parked claims

The arXiv records use perpetual nonexclusive distribution licences, not a
general implementation/code-reuse grant. No reuse permission was verified
for the queue-value author PDF. Use original derivations and paraphrases only.

Park: hardcoded public crash/rebound times, permanent short from ending price,
future-tail filters, naive unconditional reversal, literal Poisson queue formulas,
large Hawkes/HJB/neural machinery and hierarchical reconciliation as new alpha.
Returns already add pathwise; coherence of same-information conditional means
is consistency/regularization, not an independent signal.

Newer Xu/Garriott/Park claims and the supplied HftBacktest/IMC examples are
assigned a separate next verification wave. They are not yet supported by this
audit and no external proxy PnL is imported into the R2 record.
