# Qminers Algo Trade Arena 2026 — Round 1 execution, FIFO, and forecasting research

**Team Zubry — November 7, 2026**  
**Source data:** public `round1.csv` (4,411,336 market events), reconstructed public market-only book sampled every 100 ms, historical Round 0 diagnostics, user-supplied latest Round 1 submission `a48c93eb` (+344,438 public PnL).  
**Status:** analytical research and independent replay experiments; new Python candidates pass syntax/mock tests only. **They have NOT been executed through the official Qminers exchange-simulator, and no expected private PnL is asserted.**

## Executive recommendation (ordered by risk / expected information gain)

1. **Repair observed trade-flow accounting in your existing submitted code**, without changing order prices/sizes. Original line filters `taker_owner == market AND maker_owner == market`. This discards external aggressive trades against your own maker quotes. Replace with `taker_owner == market`. This is a feature distribution-shift issue caused by your own success at capturing flow. Test official simulator before retaining.
2. **Audit user-as-taker fills** in full `trades.csv` before fixing imagined self-crossing. Qminers *never matches your orders with your own orders*. A stale maker LIMIT can nevertheless consume market liquidity on activation; ordinary market-taking may be profitable or unprofitable.
3. **Test a strict own-opposite-price guard alone**, turning it off as the ablation. Don't assume it improves results. Similar independent FIFO replay policies observed only 1–3 marketable user orders over the whole Round 1 tape, and zero crossed-own states; these counts are NOT from the latest submitted bot.
4. **Test queue-aware cancel/keep vs baseline alone**, not in combination with every other change. Aggressively preserving old quotes lowered modeled PnL in previous proxy tests; queue value is real but so is lost opportunity.
5. **Test a two-horizon flow+imbalance estimator**, and optionally a third slow regime estimate, after validating the flow fix. Evaluate not just directional prediction accuracy but *maker-fill-conditioned* post-fill PnL, inventory balance, queue age, and cancellation churn.

Don't burn all dashboard submission attempts on variants. Make many **local** runs first. Keep one final successful strategy available and comply with required half-hour commits/no history rewriting.

## 1. Formal Qminers exchange rules: important invariants

From [official Qminers README](https://github.com/QminersOrg/qminers-algo-arena):

- All requests—new LIMIT/IOC, cancel, modify—activate after the simulated 5 ms delay at the first market event at or after that time.
- Price-time priority; submitted LIMIT can cross and execute existing *market* resting orders when it activates. Residual LIMIT rests; IOC residual cancels.
- **Your orders never trade against one another.** Matching excludes self-match but can execute *external* resting liquidity on your newly activated order.
- A modify reduces remaining size while retaining FIFO position; increasing size requires another order at the back of the queue.
- The strategy observes individual order ownership and market trade ownership; `on_private_order_update` is the only reliable source of actual fills.
- Position penalty `10,000 × duration_seconds(|inventory|>100)`. Absolute exposure acceptance ceiling ±1,000; competition-safe default ±100 worst-case.
- End PnL is cash + liquidation value against **market** resting liquidity − penalties; negative cash is allowed by the documented scoring model. The market tape does not adapt strategically to your orders.

**Inventory safety**:

```
remaining_bid = sum(remaining BUY size, including sent, live, and pending cancel)
remaining_ask = sum(remaining SELL size, including sent, live, and pending cancel)
safe_new_buy <= 100 - current_filled_inventory - remaining_bid
safe_new_sell <= 100 + current_filled_inventory - remaining_ask
```

These are **separate worst-case directional bounds**; don't net opposing pending orders together. A cancel request frees **no** inventory headroom until acknowledged.

## 2. Latest submission audit — factual and diagnostic

Latest public submission, user-provided dashboard:

| Metric | Actual public evaluation |
|---|---:|
| PnL | **+344,438** |
| Filled orders | 24,076 |
| Traded volume | 1,714,284 lots |
| Ending inventory | +100 |
| Cash | −658,462 |
| Liquidation mark | 10,029 |
| Penalty | **0** |
| `|inventory|` q50 / q68 / q95 / q99.7 | 38 / 61 / 100 / 100 |
| Simulation runtime | 97.2 s |

Check: `−658,462 + 100 × 10,029 = 344,438`, with sufficient terminal bid depth at the mark price reported by the server. This is terminal **liquidation valuation**, not an actual terminal buy/sell instruction.

### Issues discoverable directly in your submitted Python source

- `QI_GATE = 2.0` is ineffective: top-level imbalance is always within [−1, +1]; checks `qi > -2` and `qi < 2` always pass in a valid book.
- `FLOW_WEIGHT = 0.0`: recent flow **does not adjust the quoted fair-value center**. However, the ridge model does use exponentially smoothed flow to tilt quote sizes by ±15 lots.
- `HYSTERESIS`, `MIN_REST_US` defined but never used. Existing quote replacement occurs on every 1-tick target-price change, risking repeated queue loss.
- `BASE quote = 95`, `size_tilt <= 15`: the tilt may be entirely **clipped by remaining inventory headroom**. Example: at inventory +60 with no existing BUY, max BUY capacity is 40; both desired 80 and 110 become 40, eliminating the buy tilt. Thus your fitted predictive model is often *incapable of affecting the filled direction*.
- Existing code does correctly track private fills, pending cancels, and separate side headroom. Do **not** throw away this accounting to implement fancier models.
- Filtering `maker_owner == 'market'` discards market-taker fills against **your own** resting liquidity. For a successful, increasingly large maker, that changes the observed signal distribution compared with the same tape replayed without you. For signal estimation, prefer all fills with `taker_owner == 'market'`, including `maker_owner == 'user'`. Verify via full trade log.
- Current prices target `buy <= market best bid` and `sell >= market best ask`; they are not intended to cross current market liquidity. Activation latency can still produce incidental taker fills, so inspect them, not simply disable both sides.

## 3. Is the perceived self-cross an expensive strategy trap?

**Not direct self-trading.** The exchange explicitly skips own-vs-own matches. But a stale quote plus newer opposite quote can cause *market-taking* against a third party; every such fill should be inspected for execution price, adverse markout, and inventory effect.

To determine if this happens in **your actual submission**, download full logs from the official simulator of that exact code, then compute:

```
user-taker volume = sum(quantity where taker_owner == 'user')
user-maker volume = sum(quantity where maker_owner == 'user')
user-market maker-taker price crossing = all user-taker trades by price and time
cancellation failure rate = rejected cancels / issued cancels
```

The research-only C++ replay of the prior simpler pricing family found:

| Proxy quote target | External marketable-order activations | External taker volume | Crossed-own order states |
|---|---:|---:|---:|
| 95 | 3 | 157 | 0 |
| 200 | 1 | 44 | 0 |

Those are **surrogate model results, NOT the latest actual source**; evaluate latest `trades.csv` before deciding this is a large loss source.

### Why a blanket cross guard may hurt

- 5 ms later, the market may offer a better price than your quote; market-taking is sometimes economically favorable.
- A guard comparing your new bid against **your old ask** may pull the new bid far below touch even though your old ask is itself about to fill or cancel.
- Worst-case protection is worthwhile if measured user-as-taker losses are material, otherwise preserve the unguarded strategy.

**Controlled experiment**: keep original model and other parameters fixed; change only the guard; inspect `taker_owner=user` volume and official PnL.

## 4. Actual Round 1 signal statistics (no future data in strategy)

Research feature construction uses market-only top-level depth `QI=(bid_qty−ask_qty)/(bid_qty+ask_qty)`, signed external aggressive-flow ratio over the **trailing** second, and forward mid-price changes from a separate offline reconstructed market-only book.

Sampling used **one observation per second** for 1-second forward returns, yielding ~12,000 observations. No future labels are used in an online strategy. To avoid optimistic standard errors, 95% uncertainty ranges below were estimated by resampling 60-second time blocks.

| Conditional state | n | Mean next-1s change | Block-bootstrap 95% interval |
|---|---:|---:|---:|
| QI >0.4, signed flow >0.25 | 1,616 | +0.422 ticks | +0.379 to +0.466 |
| QI <−0.4, signed flow <−0.25 | 1,611 | −0.449 | −0.491 to −0.408 |
| QI >0.4, signed flow <−0.25 | 1,322 | +0.069 | +0.018 to +0.118 |
| QI <−0.4, signed flow >0.25 | 1,330 | −0.031 | −0.077 to +0.018 |

**Inference:** consistent book imbalance + executed flow is more predictive than the contradictory case. The asymmetric sign suggests a natural regime flag for asymmetric quoting and inventory targets. Predictive direction is **NOT fill-conditioned profit**; it can overstate a maker edge because the worse fills are selected by informed takers.

Other verified Round 1 properties from reconstructed market-only public tape: ~93% one-tick spread; median market best-side depth ~900 lots; 96,088 IOC inserts with median request 61 lots. The full market tape has 4,411,336 rows over approximately 12,000 simulated seconds. One-tick spread means attempting price improvement often converts a passive order into a taker action.

### Market-taking benchmark

If spread=1, a BUY IOC at the current ask pays roughly +0.5 tick above the midpoint *before* latency/slippage. Aligned positive-signal group predicts only +0.422 next-second midpoint change **unconditionally**. Therefore an ordinary IOC-to-midpoint trade has estimated markout approximately `0.422 − 0.5 = −0.078 tick/lot` at one second even *before* discounting latency or final liquidation. A full round-trip of immediate buy then immediate sell costs approximately one full tick if the price doesn't change. Selective taker execution requires an unusually strong additional edge or compelling inventory-reduction value; do not blindly cross the spread on QI.

## 5. Correct maker objective: conditional fill markout, not raw accuracy

For candidate bid order `(p,qty)` at time t, with evaluation/hedging horizon H:

```
ExpectedValueBid ≈ P(fill before T | queue_ahead, flow, depth, age)
                 × qty_filled_conditional
                 × E[mid_(fill+H) − fill_price | bid filled, state]
                 − incremental inventory/liquidation costs
                 − any penalty risk
```

Similarly for ask replace with `fill_price − mid_(fill+H)`.

The subtle requirement is **condition on fill**. Buy orders tend to fill when sell flow is arriving; that flow may predict a subsequent decline. Thus `E[price movement|now]` and `E[price movement|my bid fills]` are different quantities; unconditional prediction R² cannot choose optimal bids by itself.

Measure post-fill markout at 0.2s / 1s / 3s (be explicit about horizon and whether the fill timestamp equals the earliest eligible action time). Measure separately by **price level, inventory, queue-ahead, order age, spread, aligned/conflicting flow and volume-weighted PnL**. This directly addresses adverse selection.

## 6. FIFO mechanics and cancel/keep decision

- New order joins the **back** of the queue at its price; the position of existing orders ahead determines earliest fills.
- Changing an order price means cancel/repost, hence losing its old queue position after at least 5ms delay.
- Reducing size retains priority, but has its own 5ms delay.
- For a maker at the touch, high existing depth can mean long wait. However market cancels ahead may rapidly advance position.
- Old queue position is valuable only if its *current expected fill price* is still attractive, given toxicity and competition for flow. A one-tick price move may overwhelm queue value.

**Cancel rule candidate**:

```
Keep if expected PnL of eventual fill at old price
       minus expected toxicity > value of replacing the order
AND old price remains near executable touch
AND old position is plausibly ahead in FIFO.

Cancel urgently if old quote became materially worse than new fair estimate,
or queue toxicity exceeds its future spread compensation,
or position-risk constraints require removing the quote.
Otherwise consider keeping for a short hysteresis window.
```

Independent Round 1 FIFO replay ablation (similar pricing family, not exact latest bot):

| Proxy case | PnL | Submitted orders | Cancels |
|---|---:|---:|---:|
| q200, replace on 1-tick target shift | +370,367 | 50,283 | 42,809 |
| q200, preserve favorable older orders | +285,403 | 18,863 | 13,570 |
| q200, controlled price improvement when spread>=3 | +374,193 | 50,496 | 43,006 |
| q200, staged FIFO replenishment | +373,668 | 56,460 | 48,860 |

Thus *more cancellations are not automatically inefficient*, and better queue age alone is not the goal. Selecting the right **price** and **side** is essential. These results are from an independent approximation, not the server engine.

## 7. Forecasting: what statistical models are practical?

### A. Linear/EWMA state estimator (first choice)

Use input state:

```
QI_top = (bid_qty - ask_qty)/(bid_qty + ask_qty)
QI_depth = (all_market_bid_depth - all_market_ask_depth)/total_market_depth
flow_200ms = signed market-taker executions in trailing 200ms
flow_1s = signed market-taker executions in trailing 1s
flow_3s = signed market-taker executions in trailing 3s
mid_departure = mid - 3s EMA(mid)
position = actual filled signed inventory
```

Estimate expected mid changes for at least 0.2s and 1s separately, with chronological train/validation. Your existing Ridge coefficients can serve as baseline but must be retrained on a feature definition matching **all external aggressor executions**. 

Multihorizon policy: `alpha=0.5 alpha_200ms + 0.4 alpha_1s + 0.1 alpha_3s` is an **untuned exploratory setting**, not measured optimal. Use prediction disagreement to reduce directional sizing and widen vulnerable quotes, but do not cancel automatically.

### B. Conditional fill hazard (second choice)

Model probability an incoming opposite market order reaches your FIFO position within T. Useful variables: quantity ahead, quantity at touch, exponentially smoothed contra-side IOC rate, recent cancel intensity, queue lifetime, time since quote admission, absolute inventory. Estimate from **actual official order logs**; replay market-only snapshots cannot reproduce your exact queue position once you trade.

Simple model: `P(reach)=1-exp(-lambda_eff × T)` conditional on visible queue-ahead buckets and contra-side flow; estimate empirical hazard or isotonic probability table. Do not call this precise until trained and validated.

### C. Reconciliation of hierarchical time forecasts (research optional)

A one-asset market has no cross-sectional price hierarchy. Temporal coherence can be applied to future **incremental returns**: `E[Δmid_0→1s] = sum_{k=1}^5 E[Δmid_0.2(k-1)→0.2k]`, using shared features and a consistency regularizer. But optimizing time-series reconciliation is *not the same* as maximizing conditional maker PnL. A simple EWMA/linear model plus a robust inventory policy is the appropriate first experiment, with reconciliation as ablation if enough time remains.

### D. One-step lookahead / small dynamic program (later)

Represent state `(inventory bucket, top QI bucket, flow bucket, quote age/queue bucket)` and actions `keep, cancel, shrink, new limit, IOC`. Estimate transition probabilities and conditional fill rewards from logs. Bellman update:

```
Q(s,a) = expected incremental cash/markout reward(s,a)
       + discounted E[V(s_next) | s,a]
       − inventory/risk cost(s,a)
```

Do this **offline** to train a tiny action lookup table, not by running a branching simulator every market event in the submission. Cross-state value estimates need careful off-policy validation because your strategy changes which orders fill.

## 8. Experiments to run on the official Qminers simulator — minimal controlled design

| Priority | Candidate | Single changed mechanism | What falsifies it |
|---|---|---|---|
| 0 | Existing `a48c93eb` code | Control +344,438 public | Never overwrite the final before a successful alternative |
| 1 | `zubry_r1_flow_complete.py` | Include `taker_owner=market, maker_owner=user` external flows in feature | No PnL gain; feature distribution shift not material |
| 2 | `zubry_r1_flow_complete_guard.py` | Disallow posted bid>=live own ask and vice versa | Reduced maker volume or worse PnL with few user-taker fills |
| 3 | `zubry_r1_flow_complete_fifo.py` | Retain favorable older quotes for ≤1 tick | Fewer fills; cancel drop but PnL falls |
| 4 | `zubry_r1_flow_complete_forecast.py` | 200ms/1s/3s conditional flow fair-value adjustment | No positive held-out gain, excessive churn |
| 5 | `zubry_r1_flow_complete_forecast_fifo.py` | Combined model, ONLY after individual tests | Complex combination worse than best single change |

**Important:** These new files share a *reconstructed* baseline implementation, not bit-for-bit copies of your pasted latest strategy. To isolate the most reliable first experiment, apply the one-line `maker_owner` filter change directly to your **exact current source** and test *that* against `a48c93eb`.

Command (inside your actual cloned Qminers repo):

```bash
uv run exchange-simulator --strategy strategies/YOUR_CANDIDATE.py \
  --backtest data/round1.csv --log-dir logs/candidate --no-logs
```

Then read `logs/candidate/result.json`. Use full logs (omit `--no-logs`) only for a few diagnostic runs because they are large.

Metrics beyond total PnL: `pnl_se`, cash, markout, position q50/q95/q997, user maker/taker volume, order-age distribution, number of rejected cancels, average trade-to-mid profit at 200ms/1s/3s, separate results over 4 chronological windows, sensitivity to parameters. **Avoid live hyperparameter tuning on server-private feedback.**

## 9. Niche ideas / additional controlled research

1. **Markout-conditioned cancellation**: use observed toxicity of *your actual fills* to define an urgent cancel threshold; train on one time block, compare next blocks.
2. **Queue-ahead survival**: count market cancellations/trades ahead and estimate expected time to fill; no FIFO reordering possible, so the only decision is keep/reprice/withdraw.
3. **Shadow liquidity wall filter**: compare top-depth QI with capped/log-depth QI in the presence of 100k-lot synthetic walls; use conditional hazard to discount fleeting walls.
4. **Replenishment threshold**: tune 15, 30, 60 remaining lots; new order joins queue at the back and does **not** enlarge the original order.
5. **Asymmetric inventory target**: target q positive/negative based on robust signed alpha; test directional exposure only if extra markout exceeds missed maker spread capture.
6. **Forecast disagreement detector**: if 200ms and 1s alphas conflict, favor reducing size *on the dangerous side* instead of pulling both quotes.
7. **Rare IOC at actionable edge**: restrict to predicted executable profit after 5ms > half-spread + slippage + uncertainty + inventory risk; current unconditional alpha (~0.42 ticks in aligned states) rarely suffices for the 0.5-tick initial taker cost of a 1-tick market.
8. **End-game inventory**: terminal markout is a depth-weighted liquidation; test reducing position before backtest end if expected liquidation slippage exceeds resting exit costs. Do not hardcode specific public timestamps or future prices.
9. **Training mismatch test**: compare the distribution of external market-taker executed volume with and without your posted liquidity; retrain signals on the ownership-consistent definition.
10. **Prediction probability calibration**: model `P(up),P(down),P(unchanged)` separately from magnitude. An expected move of 0.4 may come from 40% chance +1 or 10% chance +4, with different fill dynamics and toxicity.

## 10. Source literature and public implementation links

**Foundational papers** (specific transfer shown above):

- [Moallemi & Yuan, *A Model for Queue Position Valuation in a Limit Order Book* (2017)](https://moallemi.com/ciamac/papers/queue-value-2016.pdf) — queue priority affects static selection and dynamic option value. No universal "keep longer" rule.
- [Donnelly & Gan, *Optimal Decisions in a Time Priority Queue* (2018)](https://doi.org/10.1080/1350486X.2018.1506257) — cancel vs keep based on queue state.
- [Cartea, Donnelly & Jaimungal, *Enhancing Trading Strategies with Order Book Signals* (2018)](https://doi.org/10.1080/1350486X.2018.1434009) — volume imbalance, next market order direction, inventory-penalized liquidity provision.
- [Cont, Kukanov & Stoikov, *The Price Impact of Order Book Events*](https://arxiv.org/abs/1011.6402) — order-flow imbalance features.
- [Stoikov, *The Micro-Price* (2018)](https://doi.org/10.1080/14697688.2018.1489139) — microprice is **not simply** weighted top-of-book mid.
- [Huang, Lehalle & Rosenbaum, *Queue-Reactive Model* (2015)](https://arxiv.org/abs/1312.0563) — state-conditioned order arrivals/cancels and queue depletion.
- [Kolm, Turiel & Westray, *Deep order flow imbalance* (2023)](https://doi.org/10.1111/mafi.12413) — forecast multiple horizons on stationary flow features; not evidence that a large neural network helps in this tiny submission.
- [Bacry & Muzy, *Hawkes Model for Price and Trades* (2014)](https://doi.org/10.1080/14697688.2014.897000) — decaying flow and feedback; EWMA is a low-cost approximation worth testing before fitting Hawkes.
- [Garriott, van Kervel & Zoican, *Queuing and inventories in limit order markets* (2025)](https://doi.org/10.1016/j.finmar.2025.100982) — late queue positions have worse adverse-selection profile.
- [Forecast Reconciliation Review (2024)](https://doi.org/10.1016/j.ijforecast.2023.10.010) — temporal aggregation is feasible but ancillary to execution PnL.

**Public code (not proprietary trading-firm algorithms)**:

- [Qminers official starter](https://github.com/QminersOrg/qminers-algo-arena) — *authoritative* competition mechanics.
- [hftbacktest](https://github.com/nkaz001/hftbacktest) — queue-position, latency and fill simulation, useful ideas but Qminers already provides exact replay simulator.
- [Hummingbot pure market-making](https://github.com/hummingbot/hummingbot) — hanging orders, inventory skew, refresh tolerance, fill delay.
- [Stoikov microprice code](https://github.com/sstoikov/microprice) — conditional finite-state fair-price estimator.
- [IMC Prosperity 4 repo by WindelsArthur](https://github.com/WindelsArthur/imc-prosperity4) — fair price, inventory rebalancing, systematic ablation. **Different engine**; its fleeting-order mechanics do not transfer directly.
- [IMC Prosperity 4 by marcobattiston21](https://github.com/marcobattiston21/imc-prosperity-4) — conditional directional regime, maker/taker overlay. Again, not proof it improves this market.

### Methodology / integrity

Recorded market tape is fixed and does not respond adaptively to Zubry; empirical backtest may understate crowded-market execution risks but must match the competition's defined replay mechanics. Do not inspect future prices or use time-anchored schedule hardcoding. Use public data and your own simulation outputs only. Keep all strategies in your private team repo; retain failed experiments in history and commit at least every 30 minutes.
