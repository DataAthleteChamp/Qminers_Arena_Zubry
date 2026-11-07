# Team Zubry — FIFO, 5 ms latency, adaptive quoting, and size-sweep research

**Qminers Algo Trade Arena 2026 · 7 November 2026 · Internal team research**

> **Status / reproducibility warning.** The numerical experiments below were produced by a **separate, independent C++ replay implementation**, not by Qminers' official `exchange-simulator` executable. It uses the documented price/time FIFO rules, persistent orders, delayed 5 ms send/cancel actions, bounded inventory, cash and liquidation markout; it does **not** claim byte-identical output to the official engine. No private-backtest score improvement is claimed. The Python candidate files pass syntax checks, but they have **not** been executed here through the official Qminers simulator. Run the official paired tests on your machine before choosing a submission.

## 1. Executive conclusions: what to implement right now

1. **Increase passive quote size first.** The exact V2 price logic with a target size of **200 lots**, but a hard **±100 worst-case actual inventory cap**, made **221,070** estimated PnL on the Round 0 public tape versus **10,395** for the original V2 configuration (2 lots; internal cap ±20).
2. **Do not intentionally pay inventory penalties by default.** Every zero-penalty size-sweep candidate incurred **zero** penalty; already capturing larger portions of profitable flow is enough to generate a large improvement.
3. **Do not assume bigger orders get better FIFO priority.** Queue rank depends on **price first, arrival time second**, not submitted quantity. Bigger size earns more fills *after* the opposing flow has passed the lots ahead of you.
4. **Cancel/repost only for demonstrable advantage.** Same-price replacement loses priority. The competition allows delayed **shrink** modifications which keep priority; increasing size requires an additional order at the back or cancel/repost. However, our simple one-tick sticky/hysteresis heuristic lost PnL; "queue preservation" is not universally profitable.
5. **A proposed adaptive model must beat the fixed-large-size baseline on distinct time windows**, not merely show more fills. Higher fill count may mean worse execution prices and worse post-fill markouts.
6. **5 ms is order delivery latency.** A quote is placed/modified/cancelled immediately before the first market event at or after `t + 5ms`. A cancellation request does not protect you before acknowledgement.

## 2. Directly documented rules and mechanics

Source: **Qminers Algo Trade Arena Getting Started (51-page workshop PDF)**, especially pp. 17–19, 27–36; and [official starter README](https://github.com/QminersOrg/qminers-algo-arena).

| Feature | Qminers implementation |
|---|---|
| Asset | One anonymous asset; market tape fixed independently of our strategy |
| Matching | Price-time priority; maker's resting price determines execution price |
| Resting order | LIMIT residual joins back of same-price FIFO queue |
| Taking liquidity | IOC; unfilled residual cancelled |
| Same-owner fills | Our own buys do not execute against our own sells |
| Latency | Every send/cancel/modify action takes effect at first market row `>= t + 5 ms` |
| Public feed | Individual order IDs, owner, prices, sizes, bids and asks within 20 ticks of touch |
| Private feed | Accepted, partial/full fill, cancelled, modified, rejected |
| Modification | **Reduce** size only; keep old queue priority; action delayed 5 ms |
| No fees | Spread and adverse selection remain real trading costs |
| Safe inventory | `-100 <= I <= 100` lots, no inventory penalty |
| Penalty | `10000 * integral( abs(I(t)) > 100 ) dt` PnL units, seconds |
| Order acceptance | Reject if `abs(I + s * (same-side resting + requested)) > 1000` |
| Score | `cash + liquidation_markout(inventory) - accrued_penalty` |

**No documented cash borrowing cap.** The simulation permits negative cash resulting from long inventory; that is not itself a loss or penalty. Final `markout` walks the opposite **market** order-book depth, best prices first, rather than valuing every lot at one midpoint price.

### 2.1 Correct worst-case exposure envelope

Let `I` be **filled signed inventory**, `B` be all potentially executable BUY lots already live or in flight, and `S` all potentially executable SELL lots live or in flight. Include cancel-pending orders **until cancellation is confirmed**.

- Maximum possible long exposure from currently live/pending orders: `I + B`.
- Minimum possible short exposure: `I - S`.
- To prevent penalties under any ordering of future fills, enforce:

```python
assert I + B <= 100
assert I - S >= -100
new_bid_qty = max(0, 100 - I - B)
new_ask_qty = max(0, 100 + I - S)
```

The sums are **per side**; do not subtract opposite-side order quantities because both sides need not fill together. A cancel request **does not** remove its reserved quantity until confirmed. This is the safe envelope for arbitrary fill ordering; it is stricter than the documented 1000-lot order-acceptance rule.

**Example:** `I=+90`, active/pending bids totaling `B=8` and active/pending asks totaling `S=50`. You may add up to **2 new bid lots** and up to **140 new ask lots** without violating the ±100 safe envelope (140 = 100 + 90 − 50). On a long +90 position, an ask fill is inventory-reducing, but you must still protect the **opposite extreme** if all asks fill before any bid fills.

### 2.2 Order lifecycle and 5 ms race conditions

```
on_order_book_change at time t
  -> submit BUY LIMIT q at bid (pending: count q in B now)
  -> exchange processes market events between t and t+5ms
  -> action applied just before first event >= t+5ms
  -> ACCEPTED, fills may occur, remaining LIMIT rests at queue back
  -> on_private_order_update updates filled inventory, cash indirectly by simulator
```

Cancellation:

```
request CANCEL at t
  -> original order remains live and fillable for at least 5ms
  -> partial/full fill might occur before cancel activation
  -> only then cancellation executes or is rejected
```

Use actual fill events, not intention, to update inventory. Never overbook by releasing reserved capacity upon requesting cancel. In the PDF's example, an order is filled 2.1ms after a cancel request and the later cancel is rejected.

## 3. Price-time FIFO: what size, rank and quote placement really mean

At bid price `10000` there are market orders with remaining sizes `[30, 40]`, then your order of 100. A market sell of 90 lots executes first 70 against market orders and then 20 against you. Changing your order to 200 at the **same instant and price** still fills 20, not 120. Price/arrival rank is unchanged.

Ways to improve execution:

1. **Join earlier** at an attractive price when the order-book is quiet; your timestamp is immutable while the order rests.
2. **Avoid needless cancel/repost** at unchanged price, since reposting goes to the FIFO tail.
3. **Shrink** rather than cancel when only the remaining volume is too large; Qminers documents shrink retains rank, but the change still arrives 5 ms later.
4. **Post an additional order** behind the existing one to expand total same-price volume without destroying the old order's priority. Apply the exposure envelope across **both** old and new orders. This is allowed in principle; the advantage over single-order V2 has to be measured.
5. **Improve quote price by one tick** only if the additional fill probability outweighs the surrendered tick and adverse selection. If the spread is one tick there is **no empty inside-spread price**; improving the bid to the ask is liquidity taking, not passive queue jumping.
6. **Reassess queue rank after send latency.** The line you saw at decision time is *not* the line you receive 5ms later. Start measuring queue position from the `ACCEPTED` observation, not the submit timestamp.

### 3.1 Compute exact visible queue ahead

The Qminers feed is market-by-order, not only aggregate market-by-price. If your own order is visible within the configured 20 ticks, you can compute its actual current queue rank at a price using `order_id`.

```python
# Pure helper for analysis / prospective strategy use.
def visible_queue_ahead(snapshot, order_id, side, price):
    levels = snapshot.bids if side == Side.BUY else snapshot.asks
    ahead = 0
    for o in levels:
        if o.price != price:
            continue
        if o.order_id == order_id:
            return ahead
        # Includes market orders and any of our earlier same-price orders.
        ahead += o.quantity
    return None  # Not necessarily absent: may be outside visible 20 ticks.
```

The economic question is *not* "How big is my order?", but **how much contra-side marketable flow arrives at this price before my quote becomes stale or gets cancelled?**

Define `A` as current queue-ahead quantity, `q` as own remaining order size, `V_h` as future opposing executable order volume that reaches this level within horizon `h`, after market cancellations and other book changes. In a simplified fixed-price setting,

`fill(q,A,V_h) = min(q, max(0, V_h - A))`.

For real market data, fit the conditional expectation `E[fill | A, spread, imbalance, volatility, marketable-flow rate, age, side, inventory]`. Queue changes and price movements make the formula an approximation, so **fit fill rates from the actual simulator order events**, not only the tape's requested IOC sizes.

### 3.2 Why a later queue position can be worse, not just slower

- A small incoming market order fills the *front* first.
- Large market orders reach *later* queue positions, and large aggressive orders may contain more directional information.
- Thus, being filled late in a queue can carry worse subsequent price markout: **adverse selection**.
- Earlier queue priority is a tradable economic option; position can be worth a substantial fraction of the spread for large-tick assets.

**Research basis:** Moallemi & Yuan (2017), Donnelly & Gan (2018), Garriott et al. (2025), and Gao & Wang (2020). References below.

## 4. Complete quote-size sweep — Round 0 PUBLIC tape

**Data:** `sample_v2.csv` (2,000,000 rows, 5,749.87 s). **Engine:** the included standalone C++ FIFO replay model, not official Qminers simulator. **Policy:** original V2 pricing and cancel when the desired price changes, unless noted. `mode=0`. Position capped at 100 for q >= 16; original q2 uses cap 20.

| Target q | Estimated PnL | Executed volume | Max abs inv | Penalty | Cancel success |
|---:|---:|---:|---:|---:|---:|
| 2 | 10,395 | 15,030 | 13 | 0 | 8,038 |
| 8 | 36,879 | 53,696 | 26 | 0 | 8,793 |
| 16 | 62,781 | 95,021 | 41 | 0 | 10,071 |
| 24 | 82,931 | 130,702 | 54 | 0 | 10,813 |
| 32 | 97,465 | 158,981 | 56 | 0 | 10,816 |
| 48 | 122,940 | 206,587 | 73 | 0 | 11,000 |
| 64 | 140,577 | 243,708 | 83 | 0 | 10,849 |
| 80 | 158,160 | 275,522 | 100 | 0 | 11,011 |
| 96 | 173,209 | 307,989 | 100 | 0 | 10,937 |
| 120 | 188,282 | 340,171 | 100 | 0 | 10,455 |
| 160 | 208,032 | 373,320 | 100 | 0 | 9,896 |
| 200 | **221,070** | **398,962** | 100 | **0** | 8,980 |
| 300/500/1000 | 221,070 | 398,962 | 100 | 0 | 8,980 |

The result plateaus at q >= 200 because, for an inventory in `[-100,100]`, the **maximum same-side new-order headroom is 200** (when inventory is at the opposite boundary); at flat inventory, the available size is at most 100. This is not an exchange prohibition on submitting 200 lots; it is the *self-imposed zero-penalty envelope*.

The quote-size effect persists in independent temporal segments:

| Variant | Train 0–3450s | Validation 3450–4600s | Holdout 4600–5750s |
|---|---:|---:|---:|
| q2/cap20 | 6,310 | 2,150 | 1,924 |
| q32/cap100 | 59,507 | 19,364 | 18,830 |
| q96/cap100 | 106,303 | 35,253 | 33,198 |
| q160/cap100 | 128,539 | 41,231 | 39,944 |
| **q200/cap100** | **137,033** | **44,417** | **42,398** |

For each segment, preceding market events were replayed to warm up the book but **team trading started only at that segment's beginning**. A segment PnL includes terminal liquidation of that independently restarted segment, so segment figures are not meant to sum exactly to full-tape PnL.

### 4.1 FIFO queue-ahead diagnostics

Instrumented after simulated order acceptance at its exact price:

| Target q | Median lots ahead | p90 lots ahead | Own orders with at least one fill |
|---:|---:|---:|---:|
| 2 | 742 | 1,641 | 7,528 |
| 32 | 613 | 1,684 | 5,448 |
| 96 | 330 | 1,685 | 4,155 |
| 200 | 401 | 1,784 | 3,629 |

These are **per-strategy queue placements**, not a single market-independent position distribution. The strategy changes *when* and *where* it joins; large size itself does not improve priority. For q200, the initial queue ahead for orders that eventually filled had **median 289 lots**.

### 4.2 Tested adaptive / queue policies (q200 unless otherwise noted)

| Policy | Estimated full-tape PnL | Relative to fixed q200 |
|---|---:|---:|
| Fixed q200 and strict ±100 | **221,070** | reference |
| q200 scaled by imbalance | 190,073 | -14.0% |
| q200 imbalance + inventory-size skew | 210,088 | -5.0% |
| q200 with extra near-limit size reduction | 210,980 | -4.6% |
| Keep existing quote within one tick of target | 172,355 | -22.0% |
| Move both sides 1 tick inside when spread >= 3 | 219,375 | -0.8% |
| Improve imbalance-favored side when possible | 185,415 | -16.1% |
| Replenish same-price orders while preserving old queue | 220,857 | -0.1% |

**Key result:** adaptive quoting as naively implemented did **not** outperform the simple fixed-large-size baseline. No claim is made that every adaptive policy is inferior; these particular alternatives were worse on this sample. `quote_size_sweep.csv` has all other tested sizes, hysteresis settings and operational counts.

## 5. An economically grounded adaptive size rule

Increasing size should maximize expected *incremental* PnL, not fills. For candidate order quantity `q` at price `p`:

`V(q) = E[filled(q)] * expected_net_edge_per_fill - incremental_inventory_risk - opportunity_cost`

where

- `E[filled(q)] = E[min(q,(V_h-A)^+)]` as a starting FIFO approximation;
- `expected_net_edge` is the execution price relative to expected value when that fill occurs, corrected for **post-fill price markout**;
- inventory risk includes terminal liquidation depth, position uncertainty, and if any intentional breach, `10000 * expected_breach_seconds`;
- opportunity cost recognizes that capacity and queue position used here may block better quotes.

At every decision:

1. Estimate next-horizon sign/size of marketable flow **conditioned on spread, queue rank, imbalance, and volatility**.
2. Compute expected marginal fill for order sizes `q in {0,16,32,64,96,128,160,200}`, clipped by strict side-specific inventory capacity.
3. Discount expected fills by conditional adverse selection, especially for queues reached only by unusually large aggressive orders.
4. Choose the `q` with maximum expected net value, **not necessarily largest q**.
5. If no candidate has positive expected value, post no new order on that side, even if room remains.
6. Compare all learned sizing schemes against **fixed q200** on multiple untouched windows.

### 5.1 Cancellation decision as a value comparison

Let `A_old` be remaining queue ahead of the existing order, `A_new` queue ahead if you cancel and repost at a different target price, `p_old/p_new` the prices, and let both 5ms request delays affect execution. Then:

`KEEP_VALUE = E[fill_old * net_edge_old] + queue_option_value - stale_quote_risk`

`REPLACE_VALUE = E[fill_new * net_edge_new] - lost_priority_cost - 5ms_inflight_risk`

Cancel only when `REPLACE_VALUE > KEEP_VALUE + safety_margin` or when current quote violates a hard risk rule. You cannot literally know the future, so fit these conditional outcomes from the public tape / official simulator logs.

**Important asymmetry:** If your buy quote has become too high relative to fair value, cancel quickly (though it remains fillable for 5ms). If your buy quote is below your new desired bid by one tick, keeping may be safer, but the fill rate can plummet; our crude sticky policy underperformed. These are *model hypotheses*, not proven universal rules.

### 5.2 Best-order-book placement options and tested results

- **Join market touch:** the V2 default; queues are long but execution prices are reasonable. **Best result among tested policies.**
- **Post inside a ≥2-tick spread on one side:** price priority over old best bids/asks, but each fill earns less; one-sided heuristic underperformed.
- **Improve both sides within a ≥3-tick spread:** some improvement in fill access, not enough to beat baseline on this tape.
- **Join behind existing queue and hold longer:** potentially valuable if queue ahead rapidly disappears, but risks stale quotes and missed fills. Our uncalibrated sticky policy lost significant PnL.
- **Add a second quote at the same price without cancelling the original:** retains the older queue slot and adds capacity at the tail; roughly tied with simple baseline, more implementation complexity.

## 6. How to measure genuine 5 ms execution performance

For every placed order record: decision time, action effective time, original best bid/ask, arrival best bid/ask, spread, queue ahead at acceptance, initial quantity, resting lifetime, cancellation request/effective time, fills, fill price, inventory at fill, and future mid-price markouts at 50ms / 200ms / 1s / 5s.

For each side and price/queue bucket calculate:

- `P(fill within horizon | A, side, spread, market-flow)`;
- `E[filled quantity | fill]` and `E[filled quantity]`;
- realized adverse selection (market movement after fill);
- PnL per filled lot, not only gross volume;
- cancellation effectiveness: was order filled during 5ms cancel-flight, did repost improve fill rate, and lost queue ahead;
- marginal value of expanding size from e.g. 64 -> 96 -> 160 -> 200;
- worst-case current signed inventory and live/pending same-side exposure.

The original Round 0 comparison found best-quote changes within a 5ms window to be uncommon (~1% of sampled observations), but this **does not remove the 5ms cancel/fill race**. Recalibrate latency hazards on each round's public tape; do not hardcode Round 0 assumptions in later rounds.

## 7. What public industry systems and papers support

We cannot verify proprietary internal strategies of firms such as Jane Street, IMC, Optiver or Qminers. The following are published models and open-source systems, not claims about secret implementations.

### Papers

1. **Moallemi, C. & Yuan, K. (2017), *A Model for Queue Position Valuation in a Limit Order Book*.** FIFO priority has both instantaneous execution-value and option-value components; more advanced queue rank can be worth a large fraction of spread. [Columbia working paper](https://moallemi.com/ciamac/papers/queue-value-2016.pdf).
2. **Donnelly, R. & Gan, L. (2018), *Optimal Decisions in a Time Priority Queue*.** Study optimal place/keep/cancel as queue position changes, including endogenous adverse selection. [Journal / DOI](https://doi.org/10.1080/1350486X.2018.1506257).
3. **Gao, X. & Wang, Y. (2020), *Optimal Market Making in the Presence of Latency*.** Latency modifies the value of a quote and optimal decisions for large-tick assets. [Journal / DOI](https://doi.org/10.1080/14697688.2020.1741670).
4. **Huang, W., Lehalle, C.-A. & Rosenbaum, M. (2015), *Simulating and Analyzing Order Book Data: The Queue-Reactive Model*.** State-dependent intensities of limit order arrivals and cancellations; motivates fill-hazard conditioning on queue state. [DOI](https://doi.org/10.1080/01621459.2014.982278).
5. **Garriott, C., van Kervel, V. & Zoican, M. (2025), *Queuing and Inventories in Limit Order Markets*.** Empirical study of queue rank, adverse selection, and inventory decisions; highlights why later queue positions can be worse even when they fill. [Open access](https://doi.org/10.1016/j.finmar.2025.100982).
6. **Avellaneda, M. & Stoikov, S. (2008), *High-Frequency Trading in a Limit Order Book*.** Reservation price / inventory-aware skew and order arrival intensities; useful baseline, but doesn't by itself solve exact FIFO + 5ms. [DOI](https://doi.org/10.1080/14697680701381228).
7. **Bonart, J. & Gould, M. (2017), *Latency and Liquidity Provision in a Limit Order Book*.** Studies how market order arrival influences subsequent liquidity provision. [DOI](https://doi.org/10.1080/14697688.2017.1296177).
8. **Yueshen, B. Z. (2025), *Queuing Uncertainty of Limit Orders*.** Studies latency uncertainty and queue ordering; a conceptual caution against blindly joining the tail. [DOI](https://doi.org/10.1287/mnsc.2023.03371).

### Open-source references

- **Qminers official simulator:** https://github.com/QminersOrg/qminers-algo-arena — ground truth for all mechanics; prefer over any third-party replay.
- **HftBacktest:** https://github.com/nkaz001/hftbacktest and [fill/queue model documentation](https://hftbacktest.readthedocs.io/en/latest/order_fill.html) — latency-aware execution, partial fills, market-by-order versus market-by-price, risk-averse versus probabilistic queue models. Qminers data has individual orders; don't replace its exact FIFO with a probabilistic model when you can measure it.
- **Hummingbot pure market making:** https://github.com/hummingbot/hummingbot-site/blob/main/docs/strategies/v1-strategies/pure-market-making.md — adaptive inventory skew, refresh tolerance, hanging orders, multiple quote levels.
- **Hummingbot quote optimization:** https://github.com/hummingbot/hummingbot-site/blob/main/docs/strategies/v1-strategies/strategy-configs/order-optimization.md — price improvement / jumping inside top quotes. Our Qminers replay comparison shows this needs a direct PnL test, not a default toggle.
- **ABIDES:** https://github.com/abides-sim/abides — agent-based market simulator; useful context, not the contest's matching engine.

A targeted GitLab search did not yield a directly verifiable Qminers-compatible FIFO market-making implementation; the strongest relevant code examples found were on GitHub. Avoid asserting that a third-party repository exactly reproduces Qminers rules.

## 8. Exact paired official-simulator commands you should run

From your team's private copy of `QminersOrg/qminers-algo-arena`:

```bash
# Download public round tape from the Arena dashboard into data/.
# This example assumes your uploaded file is at data/sample_v2.csv.

uv run exchange-simulator --strategy strategies/zubry_original_v2.py \
  --backtest data/sample_v2.csv --log-dir logs/zubry_base --no-logs
uv run exchange-simulator --strategy strategies/zubry_safe_q32.py \
  --backtest data/sample_v2.csv --log-dir logs/zubry_q32 --no-logs
uv run exchange-simulator --strategy strategies/zubry_safe_q96.py \
  --backtest data/sample_v2.csv --log-dir logs/zubry_q96 --no-logs
uv run exchange-simulator --strategy strategies/zubry_safe_q160.py \
  --backtest data/sample_v2.csv --log-dir logs/zubry_q160 --no-logs
uv run exchange-simulator --strategy strategies/zubry_safe_q200.py \
  --backtest data/sample_v2.csv --log-dir logs/zubry_q200 --no-logs
uv run exchange-simulator --strategy strategies/zubry_adaptive_fifo.py \
  --backtest data/sample_v2.csv --log-dir logs/zubry_adaptive --no-logs
```

Compare `result.json` fields: `pnl`, `breach_penalty`, `fills`, `traded_volume`, `abs_inventory_q95`, `inventory`, `cash`, and `mark_price`. Confirm **zero penalty** and ensure no unexpected REJECTED orders. For serious debugging, rerun your top variant *without* `--no-logs` and inspect `book_deltas.csv` / `events.csv` in the explorer.

**Competition submission constraints:** one `.py` file, one no-argument `BaseStrategy`, Python 3.13, imports restricted to public simulator API/allowed libraries. The included Python strategies only use `math`, public `simulator.models`, and `BaseStrategy`. Their syntax was checked locally, but the contest's validator is authoritative.

## 9. Practical decision for Team Zubry

**Default candidate:** `strategies/zubry_safe_q200.py` (copy it into your repository; run the official simulator). It makes only two parameter changes to your working V2; therefore its engineering risk is lower than an unverified new order manager. Test q160 as a fallback if q200 worsens on a new round.

**Research candidate:** `zubry_adaptive_fifo.py` shows bid/ask size adaptation using top-level depth imbalance. It is **not** currently the preferred candidate; the related independent replay underperformed fixed size. Improve its conditional fill model (queue ahead and marketable flow) before promoting it.

**Advanced experiment:** `zubry_addon_fifo.py` adds at the same price without sacrificing an existing older FIFO slot. It has more order-state complexity and was essentially tied with q200. Reject it if official simulator returns unexplained fills, order rejects, more risk, or lower PnL.

**Never confuse a public-tape optimization with the private-backtest result.** The public and private Round 0 tapes had similar aggregate microstructure but different price paths. Fixed-large-size maker trading may generalize if their fill and spread distributions remain similar, but the magnitude of PnL improvement remains unverified until the official private evaluation.

## 10. Audit / limitations of the independent replay

The bundled `tools/independent_fifo_replay.cpp` is a local independent reproduction used for *relative experiments*, not the official simulator. It maintains a full market-and-user price-time book and applies delayed user actions before the next eligible market row. Potential discrepancies include untested edge cases in user/self-matching, pending modify/cancel statuses, terminal depth fallback, event-log fields, edge-case timestamp tie order, and the public snapshot's exact 20-tick visibility. It does not implement all official `BaseStrategy` callback mechanics verbatim. This is why **do not treat 221,070 as an official achieved PnL**.

To reproduce the independent reference sweep (research only):

```bash
c++ -O3 -std=c++17 tools/independent_fifo_replay.cpp -o replay
./replay data/sample_v2.csv 0 2 20 1
./replay data/sample_v2.csv 0 96 100 1
./replay data/sample_v2.csv 0 160 100 1
./replay data/sample_v2.csv 0 200 100 1
# args: FILE MODE TARGET_QUOTE_SIZE INVENTORY_CAP PRICE_HYSTERESIS_TICKS
# mode 0 = original V2 price rules, fixed size
# mode 1 = imbalance-dependent size, mode 2/3 = additional inventory-dependent size
# mode 4 = sticky quote; 5/6/7 = price improvement experiments
# mode 9 = add same-price volume without replacing existing orders
```

The original Python V2 is also included unchanged to make baseline comparisons and git history transparent. Commit each experiment separately and include negative results, as required by Qminers' research-repository rules. Do not squash or force-push during the competition.

### 10.1 Small FIFO unit-test example

A separately bundled **six-event synthetic tape** verifies a basic queue property in the independent engine: the market has two bids of 30 and 40 lots at 100 before our bid; a 90-lot IOC sell arrives after the 5 ms order-delivery threshold. The q2 strategy receives 2 lots; q32 and q96 each receive **20 lots**, not 32/96, because **70 lots were ahead**. Run `python tests/test_fifo.py`. This is a unit test for the *research engine*, not a substitute for validating the official Qminers simulator.
