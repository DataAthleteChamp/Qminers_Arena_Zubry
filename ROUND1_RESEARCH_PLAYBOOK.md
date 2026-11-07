# Team Zubry — Round 1 quantitative research and execution playbook

**Competition:** Qminers Algo Trade Arena 2026, Round 1  
**Inputs:** `round1.csv` (4,411,336 market events; 12,000 simulated seconds), `sample_v2.csv` (Round 0 public market), `zubry_v2.py`, official Qminers workshop, public Qminers starter documentation.  
**Status:** Research and **independent** replay experiments completed. The Python candidates pass syntax checks but have **NOT** been validated in the official Qminers exchange simulator or evaluated on the private tape.  
**Competition integrity:** Keep your team's repository private, commit experiments at least every 30 minutes, share only within the team and with the organizer, do not squat on participants' private repositories.

## 0. Executive decision: what to run *now*

We recommend a small comparison rather than spending all remaining time on exotic alpha:

| Priority | Strategy file | Core settings | Why |
|---|---|---|---|
| Control | `strategies/r1_q200_base.py` | q200; inventory skew 0.05; microprice weight 0 | Aggressive symmetric maker baseline. |
| **A** | **`strategies/r1_q200_micro_sk001.py`** | **q200; skew 0.01; microprice weight 0.50** | Strong result across four time windows; low complexity. |
| **B** | **`strategies/r1_q200_flow030.py`** | **A + 1-second signed-trade-flow weight 0.30** | Improved independent replay in four windows; aligns with out-of-sample statistical model. |
| C | `strategies/r1_q200_micro025_sk001.py` | q200; skew 0.01; microprice 0.25 | Nearby parameter robustness. |
| D | `strategies/r1_q160_micro_sk001.py` | q160; skew 0.01; microprice 0.50 | Lower inventory turnover/size sensitivity. |
| Experimental | `strategies/r1_q200_clipped2000.py` | A + top-of-book depth clip at 2,000 | Guard against exceptional walls. Estimated gain is tiny; deprioritize. |

**Critical:** Use the provided official simulator for final candidate selection. The replay is only a research proxy; subtle differences in timestamps, queue matching, and callbacks can reverse results. The final private backtest is unseen.

Quick commands in repo root (copy this package's `strategies/*.py` into your team's `strategies/`):

```bash
uv run exchange-simulator --strategy strategies/r1_q200_base.py --backtest data/round1.csv --log-dir logs/r1_base --no-logs
uv run exchange-simulator --strategy strategies/r1_q200_micro_sk001.py --backtest data/round1.csv --log-dir logs/r1_micro --no-logs
uv run exchange-simulator --strategy strategies/r1_q200_flow030.py --backtest data/round1.csv --log-dir logs/r1_flow030 --no-logs
```

Record `pnl`, `cash`, `inventory`, `breach_penalty`, `traded_volume`, `fills`, `pnl_se` from each result. Verify that `breach_penalty==0`, no rejected orders, and submitted strategies use only the permitted imports. A larger public PnL is not sufficient on its own: compare PnL curves, inventory tails, per-interval stability, and whether performance relies on unusual end-of-tape liquidation.

## 1. The most important regime shift: Round 1 is a large-tick market

| Metric | Round 0 public | Round 1 public |
|---|---:|---:|
| Tape length | 2,000,000 events | 4,411,336 events |
| Duration | 5,749.9 s | 11,999.99 s |
| Resting G inserts | 1,033,029 | 2,157,657 |
| Cancellations in tape | 932,468 | 2,157,591 |
| IOC F inserts | 34,503 | 96,088 |
| IOC requested size, median | 41 | 61 |
| IOC requested size, mean | 108.7 | 160.7 |
| G requested size, median | 30 | 14 |
| G requested size, mean | 30.0 | 71.9 |
| G maximum requested size | 40 | 124,248 |
| Average spread (100ms reconstructed book) | 1.588 ticks | **1.070 ticks** |
| Share of valid 100ms snapshots at 1-tick spread | 41.4% | **93.0%** |
| Median best bid queue volume | 768 lots | 902 lots |
| Median best ask queue volume | 766 lots | 899 lots |
| 99th percentile best bid volume | 2,121 | 7,273 |
| 1s future price correlation with top-of-book imbalance | +0.341 | +0.245 |

**Engineering implication:** When the spread is one tick, price improvement usually means crossing into taker territory. Market-making at the touch, selective retreat on the toxic side, robust position sizing, and joining queues early are more important than penny-inside quoting.

The tape is not simply a live market snapshot. It is a sequence of other participants' insertions and cancellations replayed by the official matching engine. Our reconstruction uses market-only orders, FIFO within prices. It excludes the effect of Zubry's orders on the book when estimating ex-ante market features.

### 1.1 Resting-order survival and the unusually large walls

In independent market-only FIFO reconstruction, full fills and cancellation outcomes by *original resting quantity* were:

| G order size | Resting orders | Fully filled before cancel | Cancelled with partial fill | Cancelled unfilled | Mean age on cancellation |
|---|---:|---:|---:|---:|---:|
| 1–9 | 885,340 | 132,110 | 1,297 | 751,904 | 421 ms |
| 10–49 | 744,431 | 103,817 | 8,812 | 631,783 | 424 ms |
| 50–199 | 374,256 | 41,740 | 15,125 | 317,381 | 433 ms |
| 200–999 | 134,110 | 7,826 | 12,373 | 113,909 | 448 ms |
| 1,000–9,999 | 19,223 | 187 | 2,708 | 16,326 | 464 ms |
| 10,000–99,999 | 296 | 0 | 46 | 250 | 491 ms |
| 100,000+ | 1 | 0 | 0 | 1 | 399 ms |

Observations are defined by what happened in the market-only replay: counts are not exchange-provided order statuses. At tape end some orders remain and not all rows fit into the three exit categories. Some cancellation IDs already refer to completely executed orders: **285,676 of 2,157,591 Round 1 cancellation rows** did not find a live market order in the reconstructed book. Do not interpret these as Zubry cancellation failures; the historical tape can contain cancellation requests for previously filled orders.

**Actionable:** A giant best-level wall should not be trusted to last forever. It may occupy a lot of displayed depth but be canceled hundreds of milliseconds later. That *does not imply* a giant wall is universally spoofing; do not infer intent from displayed size alone. Compare *wall age, recent cancellations, executed market flow, and whether the wall survives into your 5ms action arrival*.

Useful low-complexity additions: capped top-level imbalance, log-depth ratio, multiple-depth imbalance; test each against the unmodified model before deployment.

## 2. Measured alpha: imbalance, executed trade flow, and next-price direction

Use **market-only** book volumes at best prices:

\[
I_t=\frac{Q_{bid}-Q_{ask}}{Q_{bid}+Q_{ask}}.
\]

For a one-tick spread, `microprice - mid = 0.5 * I`. We measured the following Round 1 unconditional 1-second forward midpoint changes, by imbalance bucket:

| I bucket | Mean Δmid after 1 s |
|---|---:|
| −1.0 to −0.8 | −0.382 ticks |
| −0.8 to −0.6 | −0.199 |
| −0.6 to −0.4 | −0.125 |
| −0.4 to −0.2 | −0.060 |
| −0.2 to 0 | −0.016 |
| 0 to 0.2 | +0.024 |
| 0.2 to 0.4 | +0.069 |
| 0.4 to 0.6 | +0.134 |
| 0.6 to 0.8 | +0.215 |
| 0.8 to 1.0 | +0.366 |

These are unconditional *midpoint changes*, **not** the edge of a resting order which gets filled under highly nonrandom conditions.

### 2.1 Signed executed flow adds incremental predictive information

Let `T_buy` be shares/lots actually executed by aggressive buyers during the last second, and `T_sell` the shares/lots executed by aggressive sellers (the official `Trade.book_side` maps `ask` -> buy aggressor, `bid` -> sell aggressor).

\[
F_t=\frac{T_{buy}-T_{sell}}{T_{buy}+T_{sell}+\epsilon}.
\]

We fit simple ridge regressions on non-overlapping 1-second observations. **Train:** first 60% of Round 1, excluding a 30s gap. **Test:** last 40%; features use only current/past information.

| Prediction features | Held-out next-1s R² |
|---|---:|
| Best-level imbalance `I` | **0.0547** |
| `I` + executed trade flow `F` | **0.0780** |
| `I` + `F` + normalized OFI + spread + past return | **0.0867** |
| Log depth ratio + `F` + normalized OFI + spread + past return | **0.0882** |

This is **predictive**, not an automatically profitable taking strategy. The linear coefficients for `I + F` are approximately `+0.305*I +0.270*F` ticks at the next-second horizon. Correlations and R² can be statistically meaningful with so much data but still be too small to pay a spread.

### 2.2 Confluence events and why IOC still often fails

Using independent 1-second sampling on the last 40% of the public tape, define a directional signal when `abs(I)` exceeds a threshold and recent signed executed flow agrees in sign. Mark a hypothetical **single** IOC at decision-time touch and value it at the midpoint one second later. This is **not** a complete executed round-trip PnL and ignores additional cost for the later exit, 5ms fill slippage and signaling's selection effects.

| Conditions | Holdout events | Expected directional markout after initial half-spread, before latency and exit |
|---|---:|---:|
| `abs(I) >= .70`, aligned flow >=500 | 422 | +0.006 ticks/lot |
| `abs(I) >= .80`, aligned flow >=500 | 333 | +0.020 |
| `abs(I) >= .90`, aligned flow >=500 | 205 | +0.120 |
| `abs(I) >= .95`, aligned flow >=500 | 127 | +0.213 |

**Caution:** A directional markout of +0.213 ticks is **not** enough to pay another ~0.5 tick to cross the opposite side and flatten; profitability requires a credible passive exit, a longer-lived signal, or some inventory-reduction benefit. The smaller thresholds are even less compelling. For Round 1, prioritize **making** over indiscriminate taking.

## 3. Why integer-tick rounding matters much more than elaborate ML

Our family of safe strategies computes:

\[
\widehat m_t = m_t + \alpha(\text{weighted-mid}-m_t)+\beta F_t-\lambda I_{inventory,t}
\]

and selects the maker quotes:

```python
buy_price  = min(best_bid, math.floor(fair_value - 0.5))
sell_price = max(best_ask, math.ceil(fair_value + 0.5), buy_price + 1)
```

**Counterintuitive discontinuity:** Suppose the market is `bid=10,000`, `ask=10,001`, `mid=10,000.5`. The symmetric center posts at bid 10,000 and ask 10,001. A center increase of **only +0.001** will leave the bid at 10,000 but, after `ceil`, move the sell quote to 10,002. So a tiny positive signal results in a full tick of retreat on the sell side. A negative signal symmetrically retreats the bid one tick. This is extremely meaningful in a market with 93% one-tick spreads.

Consequently, the values of `alpha`, `beta`, and `lambda` control **when** your quote changes price level, not just a continuous abstract fair-value estimate. Do not optimize on correlations alone. Measure actual order submissions, cancellations, lost FIFO priority, per-fill markouts, volume, and final PnL.

## 4. Independent replay experiments completed

**Replay contract:** We used a separate C++ FIFO book implementation with 5ms delayed actions, persistent resting orders, per-fill inventory, full-book liquidation markout, and a strict ±100 user limit. It approximates the public rules but is **not identical to and not a substitute for** the Qminers server or starter repository. Its numbers are research comparisons only.

| Round 1 candidate | Replay PnL | Max abs inventory | Penalties |
|---|---:|---:|---:|
| Original V2: q2, cap20, skew .05, alpha0 | +11,216 | 11 | 0 |
| q200, cap100, skew .05, alpha0 | +331,376 | 100 | 0 |
| q200, cap100, skew0, alpha0 | +347,788 | 100 | 0 |
| q200, cap100, skew .025, alpha .5 | +345,733 | 100 | 0 |
| q200, cap100, skew .01, alpha .25 | +360,980 | 100 | 0 |
| **q200, cap100, skew .01, alpha .5** | **+370,367** | **100** | **0** |
| q200, skew .01, alpha .5, flow beta .2 | +377,919 | 100 | 0 |
| **q200, skew .01, alpha .5, flow beta .3** | **+381,071** | **100** | **0** |
| q200, skew .01, alpha .5, flow beta .5 | +379,393 | 100 | 0 |

The best flow-adjusted candidate improved the q200 microprice-only baseline by **2.9%**, and improved the q200 original-pricing baseline by ~15%. Even more important, the PnL improved in four separate 3,000s windows:

| Time interval | q200 microprice only | + flow beta .30 |
|---|---:|---:|
| 0–3,000 s | +84,539 | +85,699 |
| 3,000–6,000 s | +91,565 | +97,267 |
| 6,000–9,000 s | +96,740 | +100,025 |
| 9,000–12,000 s | +97,517 | +98,280 |

**All windows are still the same public tape and feature selection used the public data.** These splits establish some stability, not independent private performance. The flow feature should be the first **experimental** addition to the strongest low-complexity baseline, not the only candidate.

### 4.1 Failed or negligible modifications (do not repeat blindly)

- **Naïve toxicity cancellations** when imbalance crosses 0.3–0.95: materially reduced estimated PnL. It eliminated many favorable maker executions and discarded FIFO priority. Only revisit with **fill-conditional** adverse-selection estimates and hysteresis.
- **Inside-spread improvement**: mostly unavailable at a one-tick spread; an earlier unconditional improvement policy was below the main q200 baseline.
- **Blind extended quote retention**: degraded earlier replay PnL; position value is real but price competitiveness also matters.
- **Clipping top-of-book sizes at 2,000 lots**: microprice/flow-free q200 skew .01 alpha .5 improved from 370,367 to ~371,272 in one replay, under **0.3%**; likely too weak to prioritize.
- **Large uncontrolled inventory**: no evidence of enough incremental edge to justify a breach penalty at $10,000/s. Use a strict worst-case ±100 envelope first.

## 5. FIFO, queue value and cancellation with 5 ms latency

### 5.1 What happens mechanically

1. All market and user resting orders share the same price-time FIFO queue.
2. The simulator applies submitted orders, cancellations, and shrink modifications at the **first market event at or after** `now + 5ms`.
3. On execution, an order fills at the resting order's price.
4. **Increasing** quantity requires a new order and loses priority for the additional quantity. **Shrinking** an existing order with `modify_order` preserves position. **Cancelling then reposting** loses it.
5. During the 5ms between cancel request and acceptance, the old quote is still executable; count its entire residual quantity against the risk envelope.
6. A large queue ahead is not necessarily permanently bad: orders ahead may cancel before your quote would be reached, but the probability of getting filled can depend on whether the queue is disappearing due to **market taking** (toxic risk) or **benign cancellations**.

### 5.2 Direct latency measurements from your market-only data

For uniformly spaced 100ms potential decision times, compare the market's best prices to their state just before the next event eligible to apply an action after 5ms:

| Result | Round 0 | Round 1 |
|---|---:|---:|
| Either best price changed | 0.760% | 1.229% |
| BUY at old ask becomes too low | 0.162% | 0.296% |
| SELL at old bid becomes too high | 0.202% | 0.323% |
| Mean market events before 5ms action is applied | 1.74 | 1.84 |

Relatively low price-staleness rates do **not** eliminate the cost of waiting in the queue, an unacknowledged cancel, or selection bias in the executions you actually receive.

### 5.3 Exact conservative exposure envelope

If filled inventory is `I`, total potentially executable **buy** outstanding is `B`, and total potentially executable **sell** outstanding is `S`, including both accepted and in-flight / cancel-in-flight orders:

\[
\boxed{q_{new\ buy}\le 100-I-B}\qquad\boxed{q_{new\ sell}\le100+I-S}.
\]

For instance, at `I=+90`, `B=8`, `S=0`, maximum additional safe buy quantity is **2**, while maximum safe sell quantity is **190**. These are separate worst-case paths (all buys fill, or all sells fill). Do not net simultaneous outstanding bids and asks against each other for safety.

### 5.4 The economic keep/cancel decision

For each quote, estimate **conditional** after-fill edge:

\[
EV_{keep}\approx P(fill\ before\ adverse)\cdot E[pnl\ per\ fill|fill]-P(inventory\ breach)\cdot E[penalty]-E[future\ toxic\ fill\ loss].
\]

Compare with `EV_cancel`, which includes the 5ms race, lost early FIFO slot, and opportunity cost of waiting for a new quote to become active. Do **not** automatically cancel a profitable price level simply because `bid` or `ask` has moved by one tick. Also do not keep a price that's clearly now worse than the best safe replacement solely to preserve FIFO.

The research literature on queue position is relevant for this design but does **not** supply optimal parameters for the Qminers tape. The exchange's event-level data permits empirical estimation using historical queue lifetimes and future contra-flow; the relevant unit is the fill probability and **post-fill markout conditioned on queue position**.

## 6. Proposed niche experiments (ranked by expected benefit vs implementation risk)

| ID | Hypothesis | Precise quick test | Promotion rule |
|---|---|---|---|
| E1 | Flow improves quote-side selection | Compare q200 microprice-only to `r1_q200_flow020`, `flow030`, `flow050` | Positive PnL delta in ≥3/4 windows; no penalty/invalid orders |
| E2 | Moderate inventory skew avoids drift exposure | Sweep `lambda∈{0,.01,.025,.05}` with `alpha=.5`, q200 | Plateau across windows, stable ending inventory and drawdown |
| E3 | Actual executed flow is more useful than submitted IOC size | Use signed **executed** flow only; compare 1s vs 0.25s, 2s lookback | Higher official PnL and better leave-window-out signal consistency |
| E4 | Large walls distort fair value | Cap best-level size at {500,1000,2000,5000} before microprice | Material multiwindow improvement, not just a few hundred units |
| E5 | Queue-aware cancellation beats naïve refreshing | Log `queue_ahead`, `age`, `post-fill markout`; keep near-touch quote only if value positive | Better PnL **and** fewer cancels on both segments |
| E6 | Unfavorable flow merits *size reduction* rather than cancel | `modify_order` toxic side from 100 to 30 lots, retain FIFO | Better realized markout, no loss of total maker opportunity |
| E7 | Multiple small quotes outperform monolithic size | Split 100-lot risk budget across touch and one tick deeper, time-stagger | More PnL after liquidation, without violating exposure |
| E8 | Rare aggressive IOC has positive **round-trip** edge | `|I|>.95`, same-direction executed flow>500, after 5ms actual bid/ask, model passive or IOC exit | Full end-to-end PnL positive on held-out windows, not merely predicted midmove |
| E9 | Position unwinding matters near terminal markout | Compare symmetric quoting vs stop-new-risk late and inventory liquidation | Outperforms after **correct book-walk markout** on multiple split windows |
| E10 | Maker fills cluster in predictable order-flow regimes | Evaluate markouts conditional on queue-ahead, trade burst intensity, top-queue change | Identify a threshold with sufficient executions and stable held-out edge |

**Don't deploy E4–E10 on paper claims alone.** The evidence for E1–E3 is materially stronger at present. In Round 1, simpler pricing with an executed-flow correction seems more promising than adding nonlinear models under time pressure.

## 7. Why the current strategy could fail on private data

- **Market regime shifts:** Round 1 differs from Round 0 on spread and size, and the private Round 1 path is unknown.
- **Tick-rounding cliffs:** `ceil/floor` turns tiny center changes into abrupt one-tick quote retreats; a parameter optimum may be narrow.
- **Adverse selection conditional on fills:** unconditional forward midprice predictions may say "buy" while a maker buy that actually fills is an adverse, informed-flow event.
- **FIFO model discrepancies:** independent replay can differ in delayed action ties, queue placement, and partial fills; only official validation resolves this.
- **No future execution certainty:** an order at the touch may not fill for many seconds despite 5ms placement latency.
- **Overuse of the safe cap:** the inventory envelope prevents penalties but a large ending position can face liquidation depth costs.
- **Fixed event tape effect:** historical traders cannot react strategically to our quotes in this game. This makes the competition backtest unlike a live exchange and can exaggerate large-order execution advantages.
- **Multiple comparisons:** our numerous parameter sweeps are selection on the public tape; differences as small as ~0.3% are not compelling without a holdout.
- **Overlapping labels:** 100ms samples of 1s forward returns have correlated overlapping outcomes. We fit held-out models on 1s-spaced observations and kept a gap, but these are not independent market days.
- **Operational:** Python sandbox bans imports (`os`, `sys`, network, filesystem), `open`, `getattr`, dunder attributes, introspection. Each strategy file must have one no-argument `BaseStrategy` subclass and stay ≤1 MiB; 1 CPU, 2 GB RAM, 15 minutes.

## 8. Research papers: what to *take from them* for this hackathon

1. **Cont, Kukanov & Stoikov — The Price Impact of Order Book Events.** OFI based on order submissions, cancellations and trades explains price changes more robustly than raw net traded volume in their stock-market sample. **Experiment:** measure 100ms and rolling 1s OFI after adjusting for depth. Our first simple OFI improves predictive correlation little over `I+F`, so do not take a long implementation detour. https://arxiv.org/abs/1011.6402
2. **Stoikov — The Micro-Price.** The microprice is a **conditional expectation of future mid-price moves**, not automatically the static opposite-size weighted midpoint used in simple strategy code. **Experiment:** discretize spread × imbalance into bins; estimate next-price-move transition values, then test maker quotes with an offline lookup table. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2970694 ; code https://github.com/sstoikov/microprice
3. **Moallemi & Yuan — A Model for Queue Position Valuation in a Limit Order Book.** Earlier FIFO slots provide both static expected fill value and a dynamic option to remain first. **Experiment:** log queue-ahead and model keep-vs-cancel conditional markout. https://moallemi.com/ciamac/papers/queue-value-2016.pdf
4. **Donnelly & Gan — Optimal Decisions in a Time Priority Queue.** Cancellation policy depends on position, arrivals, cancellation rates, and size. **Experiment:** compare `modify` shrink, keep, and cancel/repost using a queue valuation threshold; naive blanket cancellations underperformed in our first tests. https://doi.org/10.1080/1350486X.2018.1506257
5. **Gao & Wang — Optimal Market Making in the Presence of Latency.** An MDP formalization for large-tick markets with delay. **Experiment:** stress-test whether 5ms cancel latency changes quote value during flow bursts. https://doi.org/10.1080/14697688.2020.1741670
6. **Lehalle & Mounjid — Limit Order Strategic Placement with Adverse Selection Risk and the Role of Latency.** Predicting flow is useful only if a delayed cancellation can still protect the quote. **Experiment:** post-fill adverse markout by flow signal and queue position, compared with the 5ms cancels-in-flight race. https://doi.org/10.1142/S2382626617500095
7. **Huang, Lehalle & Rosenbaum — Queue-Reactive Model.** Order-arrival/cancellation rates condition on queue state. **Experiment:** estimate hazard of queue depletion or cancellation as a function of best-level depth and recent aggressive flow; use to forecast fills. https://arxiv.org/abs/1312.0563
8. **Bacry & Muzy — Hawkes Model for Price and Trades High-Frequency Dynamics.** Self-exciting trade arrivals. **Experiment:** exponential decay / rolling executed-flow intensity rather than only book snapshot imbalance. https://doi.org/10.1080/14697688.2014.897000
9. **Multi-Level Order Flow Imbalance (Oxford research page).** Deeper queues can add out-of-sample price explanatory power; our five-depth *static* imbalance was weaker than level-one, so deeper **changes** are more promising than deeper static totals. https://www.maths.ox.ac.uk/node/34124
10. **HftBacktest — Queue Models and Order Fill.** Distinguishes risk-averse and probabilistic queue advances for L2 books; this competition exposes individual orders and actual FIFO, so prioritize direct queue tracking where observable. https://hftbacktest.readthedocs.io/en/latest/order_fill.html ; code https://github.com/nkaz001/hftbacktest

## 9. Public industry research: Qminers, Alipes, IMC, Tower

These are **published descriptions**, not proprietary model disclosures:

- **Qminers** calls itself a market-making technology company, with quantitative analysts designing price and execution models and C++ engineers implementing algorithms where microseconds matter. Its **Junior Quant Researcher** role explicitly mentions fair value, **quoted price, size, timing, inventory risk, adverse selection and market impact**. This exactly motivates the team's quote-selection research. https://qminers.com/en/algorithmic-trading ; https://qminers.com/en/hiring/junior-quant-researcher
- **Alipes** publicly describes equity and energy automation, machine-learning interpretation of news and fundamentals, and low-latency systems. Its methods are not available in enough detail to imitate. The Qminers single-asset game lacks those external data sources. https://www.alipes.dk/ ; https://careers.alipes.dk/jobs/4698176-senior-algo-trader
- **IMC** describes quantitative research, predictive models and market-making across equities/options. Public Prosperity repositories demonstrate research workflows, but the competition's tick-based mechanics are not identical to persistent FIFO. https://www.imc.com/eu/careers/jobs/4792587101
- **Tower Research Capital** supports diverse independent quant teams across many products, regions and frequencies using simulation, predictive signals, latency engineering and risk control. No single Tower strategy is disclosed. https://tower-research.com/quantitative-trading/
- **XTX Markets** publicly describes ML-based price forecasts across thousands of instruments and using those forecasts both to trade on venues and price liquidity to clients. **Transferable idea:** learn a future-price estimate, then separately convert it into a quote/position policy that accounts for spread, inventory, and adverse selection. Their proprietary production coefficients are not public. https://www.xtxmarkets.com/ ; https://www.xtxmarkets.com/careers/
- **Hudson River Trading (HRT)** publicly describes automated market making and customized liquidity/execution quality. **Transferable idea:** measure not just raw prediction accuracy but *execution-conditioned fill quality*, effective spread, and inventory outcomes. Do not assume its client-facing execution model maps directly onto this simulator. https://www.hudsonrivertrading.com/liquidity/
- **Citadel Securities** publicly emphasizes systematic options pricing, continuous liquidity, execution quality and risk management. **Transferable idea:** maintain reliable quoted inventory capacity with automated protections and detailed trade attribution; the real firm is far more complex and multi-asset than this contest. https://www.citadelsecurities.com/what-we-do/options/

**What the public industry evidence does *not* tell us:** any of these firms' private signals, precise thresholds, risk limits, or profitable parameters. The competition-specific 1-tick spread, flat inventory penalty, deterministic 5ms action delay and fixed historical market tape dominate how their high-level principles translate here.

Useful **IMC Prosperity 4** public repos:

- https://github.com/eliasroub/imc-prosperity-research — microstructure features (OFI, VPIN, queue pressure), segmented attribution, and a warning that naïve local fills can overstate live profitability by orders of magnitude. Adapt **ablation discipline**, not multi-asset options code.
- https://github.com/Leo-Hawking/IMC-Prosperity-4-Review — top-0.5%-reported retrospective with a concrete **probe → visualize → hypothesize → backtest → review** workflow; the useful niche idea is to contrast the largest resting walls with the best displayed prices when fair-value quotes are distorted by transitory near-touch small orders. Test *lagged depth changes*, not memorized public price paths.
- https://github.com/fabianbaiertum/IMC-Prosperity-4 — market-making modes and validation of fair-value estimates; useful idea: **compare competing quote modes only in suitable regimes**.
- https://github.com/AbhinavGupta707/IMC-Prosperity — a reproducible test harness, plateau intersection and PnL diagnostics; final source code is intentionally withheld, so don't claim otherwise.
- https://github.com/nkaz001/hftbacktest — real queue/latency modelling concepts, but this competition already gives an exact exchange implementation.

## 10. Next experiment and decision workflow (safe for the contest)

1. **Run official simulator** on `r1_q200_base.py`, `r1_q200_micro_sk001.py`, `r1_q200_flow030.py` immediately; keep the fastest stable submission ready.
2. Reject anything with a nonzero penalty, excessive rejections, blown inventory or a reproducibility failure (unless the additional expected value is explicitly demonstrated and justified). **Our candidates intend zero penalties.**
3. Compare PnL-vs-time curves, total traded volume, fills, ending position, markout and cancellation status. A total-score winner driven by a single anomalous late fill needs scrutiny.
4. If flow .30 wins, compare .20/.50 to establish a parameter plateau; if flow loses, choose the simpler microprice-only candidate.
5. If the difference is small (<1–2%), prefer the simpler and more stable code. Preserve every failed experiment and rationale in the private repo; commit at least every 30 minutes.
6. On the final submission, select the **working** candidate on the dashboard, not necessarily the most recently edited source file; verify it was accepted on public. The true private outcome is only known after submissions close.

### Source/implementation provenance

- Independent replay implementation is in `tools/independent_fifo_replay.cpp` and the optional experimental extensions in `tools/replay_flow.cpp` / `tools/replay_gate.cpp`.
- Reconstructed 100ms market features were generated from historical market tapes by `tools/reconstruct_book.cpp` and `tools/analyze_book.py`.
- Run details: `tables/round1_replay_sweep.csv`, `tables/round1_window_validation.csv`, `tables/round1_flow_window_validation.csv`, `tables/rare_ioc_signal.csv`, `tables/round1_imbalance_buckets.csv`.
- Raw public round data is **not** embedded in the package; keep it in the ignored `data/` folder.
- Analysis scripts are permitted in the development repository, **not** in the submitted single-file sandbox. Published literature motivates the tests; all numerical estimates in this document come from the supplied competition tapes and independently implemented reconstruction/replay.
