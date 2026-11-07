# Team Zubry — Aggressive, Penalty-Aware Market Making and Round 0 Public/Private Research

**Competition:** Qminers Algo Trade Arena 2026 (Prague)  
**Date:** 7 November 2026  
**Purpose:** Engineering and research specification for **maximizing net PnL** with larger quotes, inventory budgeting, 5 ms action latency, conditional cancellations, and optional intentional threshold breaches. Includes an independent forensic comparison of Round 0 public and private market behavior.  
**Inputs:** `sample_v2.csv` (public Round 0), `results.zip` (Zubry V2 private backtest logs), `zubry_v2.py`, official workshop PDF and Qminers repository.  
**Scope:** Historical Round 0 observations are **not guarantees** about Round 1–4. Strategies proposed below are **unbacktested research candidates** until run with the official simulator.

## Decision summary — what to do today

1. **First test `QUOTE_SIZE=16, 32, 64, 96` with `MAX_INVENTORY=100`.** The current baseline is 2-lot quotes, cap ±20, and actual inventory only ±12. Use the *same* public tape to compare and inspect fills, PnL, penalty, drawdown. Keep one active/in-flight quote per side as in V2, or implement a full outstanding-order ledger before adding more.
2. **Never confuse negative cash with a loss.** Qminers scores `cash + book-liquidation markout − penalty`. Zubry's real private result is **cash −9,066, inventory +2, mark price 9,932, penalty 0, PnL +10,798**. The extra inventory is *valued* against market depth at the end; the bot is not required to execute a closing IOC to calculate PnL.
3. **For a no-penalty policy, reserve capacity for every own live, pending and pending-cancel order.** Use both same-side worst-case envelopes, **not net outstanding buy/sell quantities**.
4. **Make quoting size and asymmetry conditional on edge.** Round 0 shows a stable top-of-book imbalance signal on public **and** private, but a naive unconditional imbalance-driven IOC loses to half-spread costs in an idealized 1-second test. Prioritize **maker size/skew** over unconditional crossing.
5. **Do not optimize drift or exact timestamps.** Public price moved **+3.5 ticks**, private moved **−67.5 ticks**; their one-second returns had correlation **0.017**. Marginal market mechanics, not the realized path, transferred well.
6. **Deliberate penalties are an optional separate strategy, not the default.** They cost **10,000 PnL per simulated second whenever |I|>100**, regardless of the number of excess lots. Prefer scaling within ±100 first; beyond that demand a calibrated, near-certain exit and positive incremental expected PnL after penalty.

## A. Official mechanics — distinguish verified rules from hypotheses

| Topic | Official rule or documented fact | Implication |
|---|---|---|
| One instrument | Single anonymized traded instrument within a tape | No cross-asset hedging; each round can have different market conditions and challenge mechanics. |
| Initial capital | **No initial cash budget or cash-usage limit is specified** | A negative cash account is possible; **do not** infer unlimited economic capital or external borrowing features. |
| PnL | `cash + markout(inventory) − breach_penalty` | Cash alone is not profit. Markout uses resting **market** bids to sell longs and resting **market** asks to buy shorts; sweeps price levels. |
| Inventory band | `|I| <= 100` | No penalty inside band, **including ±100**. |
| Penalty | `10_000 * exact simulated seconds during which |I|>100` | Flat time-rate, **not per excess lot**. |
| Exchange acceptance | Reject order if `abs(I + side_sign*(R_same_side + q)) > 1000` at acceptance | Hard limit applies to inventory and same-side resting exposure; not the preferred safe trading cap. |
| Matching | FIFO price-time; LIMIT rests, IOC does not | Queue position is valuable. No general market order, but marketable IOC can take liquidity. |
| Latency | Every send, cancel, modify effective after at least 5 ms; at the first event at/after +5 ms | Cancels can be beaten by fills; reducing a quote in place preserves time priority. |
| Observations | Individual book orders, market trades, private order updates | Track **acknowledged fills and order statuses**; sent requests are not executed orders. |
| Pricing | Integer tick prices, integer lot sizes, no fees | Spread and slippage still cost PnL; zero exchange fees do not make IOC free. |

**Official sources:** [Qminers starter repository / exchange documentation](https://github.com/QminersOrg/qminers-algo-arena), the team's uploaded *Algo Trade Arena — Getting Started* PDF pp. 28–36, and organizer rules supplied directly to Zubry. Simulator README also documents end markout beyond visible depth using the last swept or last-traded price. Verify edge cases against your own cloned simulator source before betting on them.

### Cash and liquidation example (from actual result.json)

```text
cash                    -9,066
inventory                   +2
liquidation mark price   9,932
inventory markout        19,864
inventory penalty             0
final PnL               10,798
```

This does **not** mean buying 1,000 lots before the close creates a windfall. A large long is valued by sweeping bid liquidity; a large short by sweeping asks. Markout may deviate sharply from last trade/midpoint, especially as size grows. End-of-round PnL is a valuation, not a promise of fills at a uniform final price. As usual, a position may have negative cash and positive total equity.

### Penalty arithmetic

$$
P=10{,}000\int_0^T {\bf1}(|I_t|>100)dt.
$$

| Breach time | Cost |
|---:|---:|
| 1 ms | 10 |
| 5 ms | 50 |
| 10 ms | 100 |
| 20 ms | 200 |
| 50 ms | 500 |
| 100 ms | 1,000 |
| 1 second | 10,000 |

**Do not conflate the threshold with the hard order exposure:** +101 lots for 50 ms costs 500, and +900 lots for 50 ms also costs 500 (provided each position was admitted), but their slippage/price risk and time-to-exit can be dramatically different.

## B. Round 0 forensics — public vs private

### B1. Exactly which inputs were compared

- **Public:** `sample_v2.csv`, 2,000,000 raw market tape actions including 1,033,029 passive G inserts, 34,503 IOC F inserts, and 932,468 cancels, 5,749.896 seconds.
- **Private:** `results.zip/events.csv` filtered to `source == market`. This log contains **1,033,628 passive market adds** and **931,972 market cancels** over 5,739.945 seconds. **Important:** private IOC requests do not appear as ordinary market `add` rows in this execution log; incoming market taker orders can be inferred only partly from `trades.csv` (33,637 distinct executed market taker IDs). Therefore comparing total raw public events to private `events.csv` market rows directly **would be invalid**.
- **Book reconstruction:** public uses a replay of the input tape with FIFO matching for G/F orders and cancellation; private uses `market`-owned quantities in `book_deltas.csv`. Private book can be affected by Zubry taking/filling liquidity; Zubry traded only 15,226 lots relative to millions of traded market lots, but the reconstructed books are not mathematically identical observables. Both are sampled approximately once per second after available events.
- **Statistics:** Report magnitudes/conditional relationships. Standard KS p-values on book snapshots are descriptive only: 1-second snapshots are serially dependent and not i.i.d.

### B2. Empirical distribution results

| Metric | Public R0 | Private R0 | Interpretation |
|---|---:|---:|---|
| Passive G inserts | 1,033,029 | 1,033,628 | Within **0.06%** |
| Cancellations | 932,468 | 931,972 | Within **0.06%** |
| Mean passive G size | 30.004 | 30.000 | Essentially the same |
| G size median / 5th–95th percentile | 30 / 21–39 | 30 / 21–39 | Same typical size range |
| Buy-side proportion of passive G orders | 50.004% | 50.004% | Symmetric submission flow |
| Median lifetime of canceled G orders | 500.286 ms | 500.577 ms | Difference only 0.29 ms |
| 95th percentile canceled G lifetime | 2,036.67 ms | 2,041.32 ms | Close |
| Replayed 1-second best spread (mean) | 1.583 ticks | 1.601 ticks | Similar |
| Share of seconds at 1-tick spread | 41.83% | 40.05% | Similar |
| Replayed 1-second median best bid volume | 766 lots | 805 lots | Similar but not identical |
| Replayed 1-second median best ask volume | 763 lots | 792 lots | Similar |
| Std. deviation of 1-second mid-price changes | 0.496 | 0.490 ticks | Similar |
| Std. deviation of 5-second mid-price changes | 1.151 | 1.122 ticks | Similar |
| First-to-last mid-price change | **+3.5** | **−67.5** ticks | **Completely different realized trend** |
| Correlation of synchronized 1-second price changes | \- | **0.017** | Essentially independent paths |

**Distribution tests (descriptive):** passive G order sizes KS `D=0.00657, p≈0.535` from 30k randomly sampled additions per tape; best spread `D≈0.0177, p≈0.321`; one-second price changes `D≈0.0140, p≈0.623`. Non-rejection is **not proof** of identical distributions, but small effect sizes plus matching microstructure support a shared or closely related generating process.

**Additional independence check:** align passive insert events by numeric order ID. Recorded order side matches only **~49.95%** of the time and submitted quantity matches exactly **~4.67%**, consistent with separate random realizations. Do not train on exact row IDs, timestamp moves or future trajectories.

**Subtle statistics warning:** full-length 96-minute-bin event counts showed a misleading correlation of ~0.85 caused substantially by the **truncated final minute** in both files. Removing that partial minute reduces per-minute event-count correlation to **~0.17**. Always remove incomplete time bins when comparing activity-rate correlation.

Recommended charts (included in archive):

- `assets/public_vs_private_best_mid.png`: true reconstructed market best-midpoint series, clearly different trend paths.
- `assets/public_vs_private_spread.png`: nearly identical 1-/2-tick spread distributions.
- `assets/public_vs_private_volatility.png`: coarse rolling volatility from minute-level proxy prices.

### B3. What carries over to a new tape or round

**Good candidates for distributional transfer:** typical G order sizes (20–40), cancellation times (~0.5 second median), common spread (1–2 ticks), best-level queue volumes (hundreds of lots), price volatility (similar in the two tapes), and qualitative top-of-book imbalance signal. These are excellent *priors*, to be recalibrated using that round's public data.

**Do not assume:** same absolute price drift, trending direction, precise arrival timestamps, same data-generation seed, same optimum quote size, identical price dynamics, identical Round 1–4 parameters, or equal effectiveness of an alpha signal after 5 ms latency. Round 0 evidence supports a shared **family** of microstructure dynamics, not a literal guarantee for all four rounds.

### B4. Round 0 transferability of a simple predictive signal

Let `I=(best_bid_quantity-best_ask_quantity)/(best_bid_quantity+best_ask_quantity)` using **market best-level** sizes. Estimate next-one-second midpoint changes `Δm` (1-second observations):

| Quantity | Public | Private |
|---|---:|---:|
| Pearson correlation `corr(I_t, Δm[t,t+1s])` | **0.3415** | **0.3390** |
| OLS slope (ticks per unit of I) | **+0.3291** | **+0.3269** |
| Average Δm for `I>=0.6` | **+0.250** | **+0.243** ticks |
| Average Δm for `I<=−0.6` | **−0.255** | **−0.241** ticks |

This is remarkably stable directional signal, compatible with classic queue-imbalance literature. It is **not automatically a profitable IOC signal**. A zero-latency, half-spread-only back-of-envelope calculation for `|I|>=0.8` yielded **−0.26 ticks per hypothetical aggressive entry** at a 1-second markout in both tapes. Real entries have 5 ms latency, possible partial fills, adverse selection and size-dependent sweep costs, so do not treat the idealized estimate as an actual backtest.

**Research priority:** skew maker quote prices/sizes and cancellations according to imbalance, rather than blindly crossing the spread. Consider IOC only when predicted trade-edge after 5 ms and all costs is positive, or when an urgent inventory reduction avoids a larger penalty.

### B5. Quantified 5 ms price staleness on public Round 0

Using **82,535 sampled decision instants**, replaying both sides of the actual market book and comparing to the book just *before* the first market event at/after `t+5 ms`:

| Observable | Public R0 |
|---|---:|
| Median market tape events in delay | 2 |
| 95th percentile market tape events | 4 |
| Any best-bid change | 0.513% |
| Any best-ask change | 0.513% |
| Either best price changed | 1.024% |
| Observed-ask BUY IOC limit becomes too low | 0.251% |
| Observed-bid SELL IOC limit becomes too high | 0.259% |

This indicates price staleness itself was relatively low in **this** market; **FIFO priority, delayed cancellations and adverse-selection fills** still matter. A touch that stays at the same price can change in **queue depth and quantity**. Also, these are randomly thinned event observations (every 20th tape event) and hence slightly activity-weighted; they are not clock-uniform observations.

### B6. Evidence that 2-lot quote size underused executable demand

From the actual 7,687 Zubry maker fill rows on private R0, grouped by matching aggressor order and execution price:

| Quantity that matched **after** our fill at the same price | Fraction of our fill rows |
|---|---:|
| At least 8 additional lots | **78.5%** |
| At least 16 additional lots | **71.2%** |
| At least 32 additional lots | **58.0%** |
| Median remaining matched quantity at same price | **44 lots** |

This is **counterfactual headroom**, *not a claim* that all subsequent trades would have been captured by a larger quote: the larger order would change subsequent state, inventory, fill accounting, and perhaps price-level capacity. It nevertheless makes size expansion an exceptionally high-priority A/B test.

Observed Zubry baseline: `QUOTE_SIZE=2`, `MAX_INVENTORY=20`, `IMBALANCE_WEIGHT=0`, `INVENTORY_SKEW=0.05`, max actual inventory ±12, 7,629 fills in `result.json`, 15,226 lots traded, 0 penalty, **PnL 10,798**. Private 7,687 individual maker trade rows are **not** identical in counting convention to the 7,629 reported fills. Cancellation requests 7,534; cancellation failures 34 (**0.45%**) under this strategy/size.

## C. Exact zero-penalty capacity rule — how to use the full ±100 safely

At every order-book callback or private update, track:

- `I`: **filled** signed inventory: buy fills add quantity; sell fills subtract quantity.
- `B`: remaining potential **BUY** fills across every active, in-flight, pending-modify and pending-cancel order (until terminal acknowledgement).
- `S`: remaining potential **SELL** fills in those same states.
- `B`/`S` must include orders *being cancelled* and orders *not yet accepted*. If they have not been definitively rejected, canceled or filled, they are still potential executions.

**Worst-case inventory envelope:**

$$
I_{max}^{possible}=I+B,\qquad I_{min}^{possible}=I-S.
$$

If we want a **hard invariant of no penalty, regardless of which orders fill and in what sequence**:

$$
\boxed{I+B\le 100\quad\text{and}\quad I-S\ge -100.}
$$

Thus safe capacity for additional quotes (after counting all existing orders):

$$
\boxed{q_{buy}^{max}=\max(0,100-I-B),\quad
q_{sell}^{max}=\max(0,100+I-S).}
$$

**Crucial:** It is **not** correct to net buys against resting sells (`I + B − S`) and assume they will fill together. They may fill in any order. The formulas bound both extrema. Example:

| Filled inventory I | Other possible BUY fills B | Other possible SELL fills S | Safe additional BUY | Safe additional SELL |
|---:|---:|---:|---:|---:|
| 0 | 0 | 0 | 100 | 100 |
| +80 | 10 | 20 | 10 | 160 |
| +90 | 8 | 0 | 2 | 190 |
| −95 | 0 | 3 | 195 | 2 |
| +100 | 0 | 0 | 0 | 200 |

**Yes, a new SELL of 190 is safe at I=+90 if no other sells are pending:** any partially/fully filled sell changes I from +90 to at worst −100. That is not the same as trading 190 lots profitably; the quote still needs positive expected edge and available demand.

```python
# Offline research helper; easy to inline in a legal strategy file.
def safe_extra_sizes(inventory, pending_buys, pending_sells):
    return (
        max(0, 100 - inventory - pending_buys),
        max(0, 100 + inventory - pending_sells),
    )
```

### Can existing V2 handle safe scaling without rewriting the ledger?

Your exact uploaded V2 tracks **at most one order per side**, and refuses to create another order of that side while the old one is still tracked, including during an in-flight cancellation. Its same-side `headroom` calculation is `MAX_INVENTORY - inventory` for buys and `MAX_INVENTORY + inventory` for sells. Under those invariants, setting `MAX_INVENTORY=100` and increasing `QUOTE_SIZE` **provides the strict ±100 envelope by construction**, assuming all private fills are accounted for and the one-order-per-side invariant is never broken. Test partial fills and event status transitions before relying on it. If adding multiple layers/orders per side, that existing headroom logic is **no longer sufficient**; use the full `B`/`S` ledger.

**No-penalty is not necessarily maximum-profit:** a quote should use the maximum *profitable* quantity:

$$
q^*=\arg\max_{0\le q\le q_{safe}}\left[\mathbb E[PnL(q)]-\lambda Risk(q)\right]
$$

### Quote-size selection: quantity is also a price/risk decision

**A practical policy:** choose q from discrete candidates `[0, 2, 8, 16, 32, 64, 96]` plus the safe headroom, rather than blindly posting the full q_safe every time. For each candidate, approximate:

$$
EV_{side}(q,p)=\sum_{k=1}^q \Pr(\text{lot }k\text{ fills while quote remains})\cdot
\mathbb E[\text{future liquidation value} - \text{fill price}\mid \text{fill of lot }k]
-\lambda Risk.
$$

For SELL, reverse the price difference. A high fill probability alone can mean *adverse selection*; model the expected post-fill **markout conditional on being executed**. Fit probabilities by queue-ahead, recent aggressive order sizes, spread, imbalance, and quote age. Use maximum q only where the incremental expected value of the marginal lots remains positive.

## D. Fast action policy — BID/ASK new, keep, shrink, cancel, IOC

### D1. On each book callback

1. Apply previously received `on_private_order_update` events to inventory/remaining qty (never infer fills from a cancel request).
2. Read **market** best bid/ask. Avoid treating your own isolated quote as the market's executable fair price.
3. Calculate `(I, B, S)`, safe headroom per side, and quote prices. Update recent flow and imbalance from **past information only**.
4. Evaluate the expected conditional fill value of existing bids/asks; **do not cancel simply because the midpoint moved by half a tick**.
5. If an order's remaining size exceeds the desired inventory budget, `modify_order` to **shrink in place** (effective 5 ms later, preserving FIFO). If fully undesirable, `cancel_order` but continue to reserve exposure until acknowledged.
6. If no same-side order is live/in flight and a new quote has positive estimated value, submit a size limited by `safe_extra_sizes`.
7. If an urgent reduction is warranted, compare passive waiting vs IOC cost and only submit an IOC if its expected **incremental** PnL is positive (or it avoids larger expected penalty risk). Reserve IOC exposure in the ledger until confirmed.

### D2. Specific asymmetric policy from imbalance

For top-level size imbalance `z=(bid_qty-ask_qty)/(bid_qty+ask_qty)`:

| Market state | Preferred **BUY bid** | Preferred **SELL ask** | Notes |
|---|---|---|---|
| `z >= +0.6` | Can size up a bid if post-fill EV remains positive | Size down/cancel an ask if predicted fair value rises above its price | Beware a bid fill during upward pressure may be rare; ask fill risks selling before a rise. |
| `z <= −0.6` | Size down/cancel a bid at risk of being picked off | Can size up a sell quote | Symmetric adverse-selection logic. |
| `−0.3 < z < +0.3` | Two-sided maker quoting | Two-sided maker quoting | Capture spread; manage inventory. |
| Large inventory near +100 | Limit new bids; prefer profitable sells | May make a much larger sell quote **within** the safe envelope | Cannot assume a passive sell will execute quickly. |
| Large inventory near −100 | May quote a larger bid | Limit new sells | Symmetric. |

These are **candidate conditions, not calibrated optima**. The Round 0 top-book signal predicts future mids, but the exact effect of signal on **conditional fill PnL** has not yet been established by actual strategy comparisons.

### D3. Cancellations: queue value vs adverse selection

For a live quote at price `p`, let:

- `H` = estimated lots ahead in FIFO at its price; lower is usually better for getting filled, but also exposes you to toxic market flow sooner.
- `alpha_after_fill` = expected executable markout conditional on the quote filling.
- `q` = remaining size, `Pfill` = fill probability over the intended quote lifetime.
- `V_queue` = continuation option value of maintaining current queue position.
- `R_inventory` = expected inventory/penalty cost of additional fills.

Roughly:

$$
V_{keep}\approx Pfill\cdot q\cdot alpha_{afterfill}+V_{queue}-R_{inventory}.
$$

- **KEEP** when the order is still profitable and the FIFO position has value, even if a slightly better quote is available.
- **SHRINK** when its size is no longer attractive but some fraction of the current quote has positive continuation value; this preserves queue priority.
- **CANCEL** when conditional post-fill value becomes negative enough to overwhelm FIFO value and inventory/replacement costs, or the order makes the risk envelope unsafe after other state changes.
- **REPRICE** only when the expected improvement outweighs losing existing FIFO position, waiting 5 ms, and the risk of adverse fills before cancellation.

**Cancel race:** Qminers actions take effect 5 ms late. Your actual V2 had **34 failed cancellations / 7,534 requests (~0.45%)**. This is an *empirical base rate for V2*, not a universal rate for much larger orders. When cancelling a BID, its quantity **still counts toward B** until the terminal cancel/fill event. A pending cancel does not protect you from penalty.

A practical debounced quoting engine should use a **minimum quote lifetime**, minimum change in expected value to reprice, and inventory-driven forced exits. Evaluate durations on real data—do not pick a magic 100 ms TTL just because it looks reasonable.

### D4. Immediate IOC vs passive exit when approaching the boundary

When at `I=+95` with `B=5`, you have **zero** remaining safe BUY capacity. A large aggressive BUY would violate the strict no-penalty objective. You can still (i) allow maker SELL orders to reduce inventory, (ii) submit a SELL IOC to reduce inventory immediately at the future execution time, or (iii) cancel/modify bids to free capacity, **but the cancellation itself does not free actual inventory or pending-fill exposure until confirmed**.

If already outside the band, IOC can avoid the penalty clock:

$$
\text{Expected saved penalty} = 10{,}000\cdot\left(T_{passive\ recovery}-T_{IOC\ recovery}\right).
$$

For a long inventory breach, a SELL IOC of `r` lots is economically justified when its extra spread/sweep cost and negative markout are smaller than the expected penalty and risk savings. **Do not compare costs only with nominal 5 ms**; model arrival at the next tape event, available bid depth, partial fill, and the risk of further BUY fills from outstanding quotes.

## E. Optional extreme regime — legitimate penalty-accepting strategy

**Flat threshold:** marginal penalty per added excess lot can be zero **while already outside** the band, but extra exposure can extend expected breach duration and worsen slippage. The first +101st lot starts the clock. The crucial quantity is *incremental probability-weighted time outside the threshold*, not a nominal scheduled holding time.

For an alternative proposed action `a` versus the best strict-in-band action `a0`:

$$
\Delta EV=\mathbb E[\Delta GrossPnL]\ -\ 10{,}000\mathbb E[\Delta T_{outside}]\ -\ RiskReserve.
$$

`ΔGrossPnL` here **already includes** additional executable costs, slippage and liquidation impact. No double deduction for the spread.

**Breakeven examples** (optimistic; before further risk reserve):

| Extra lots beyond 100 | Expected extra net trading edge per lot | Gross incremental advantage | Max additional breach duration |
|---:|---:|---:|---:|
| 50 | 1 tick | 50 | 5 ms |
| 200 | 1 tick | 200 | 20 ms |
| 400 | 1 tick | 400 | 40 ms |
| 900 | 1 tick | 900 | 90 ms |
| 400 | 2 ticks | 800 | 80 ms |

If extra position requires ≥100 ms to unwind, the penalty alone costs 1,000. **Paying the penalty while holding a slowly filling passive order is normally a bad idea.** It may be rational for exceptionally short high-volume opportunities, but demand positive expected *net* advantage under conservative exit-time quantiles. Note that the **5 ms exchange delay starts after the action**, and zero-penalty strict quoting is already capable of holding or quoting hundreds of lots across sides without triggering the threshold.

The current V2 earned ~**0.709 PnL per traded lot** across its full private run, but this is **not** a valid forecast for bigger orders or independent extreme breaches. If you used 0.709 as a **purely illustrative** incremental edge for 400 excess lots, you could afford only about **28.4 ms** beyond the band before break-even—and a strategy with that small a margin is fragile.

**Suggested priority:** baseline no-penalty sizes 16/32/64/96 before implementing any breach-taking. A deliberately penalized version must pass public-tape walk-forward analysis and comparison to the strongest no-penalty strategy; otherwise leave disabled.

## F. Experiment design — exploit mechanism, not a memorized tape

**Candidate ladder using identical V2 logic:**

| ID | `QUOTE_SIZE` | `MAX_INVENTORY` | Imbalance setting | Purpose |
|---|---:|---:|---:|---|
| A0 | 2 | 20 | 0 | Original control |
| A1 | 16 | 100 | 0 | More maker throughput |
| A2 | 32 | 100 | 0 | Aggressive maker baseline |
| A3 | 64 | 100 | 0 | High-capacity maker |
| A4 | 96 | 100 | 0 | Near full single-quote capacity |
| B1 | Best from A | 100 | mild inventory/imbalance skew | Test conditional alpha |
| B2 | Best from A | 100 | cancel debounce / queue preservation | Test cancellation economics |
| B3 | Best from A | optional threshold breach | explicit expected advantage > risk | Test **only if** above works |

**Record for each run:** `pnl`, `cash`, `markout`, `inventory`, `breach_penalty`, `traded_volume`, fills, p95/p99 inventory, ending inventory, max drawdown and per-minute PnL; compute maker fill post-markouts and distribution of cancellations / failed cancels. **Do not assume any candidate outperforms the original without running it.**

**Public/private validation:** public is a single known tape; the earlier private run is one independent tape for the old V2 only. **You cannot accurately compare candidate A2/A3 to the historical private result without re-running candidates on that private tape, which you do not have in input CSV form.** Their public outcome must be judged with holdouts and the current round's fresh private leaderboard when available. Use chronological folds with state reset/warmup where possible. **Avoid tuning a single threshold over hundreds of attempts without recording the number of trials.**

Suggested commands in your **own official Qminers repo**:

```bash
uv run exchange-simulator --strategy strategies/zubry_v2.py --backtest data/round0_public.csv --log-dir logs/a0 --no-logs
uv run exchange-simulator --strategy strategies/zubry_aggressive_safe_q16.py --backtest data/round0_public.csv --log-dir logs/a1 --no-logs
uv run exchange-simulator --strategy strategies/zubry_aggressive_safe_q32.py --backtest data/round0_public.csv --log-dir logs/a2 --no-logs
uv run exchange-simulator --strategy strategies/zubry_aggressive_safe_q64.py --backtest data/round0_public.csv --log-dir logs/a3 --no-logs
uv run exchange-simulator --strategy strategies/zubry_aggressive_safe_q96.py --backtest data/round0_public.csv --log-dir logs/a4 --no-logs
```

Use an actual filename matching your downloaded round tape. Full `events.csv` + `trades.csv` logs are useful for the finalists, but `--no-logs` for fast parameter comparison. The candidate files provided with this archive are **minimal parameter changes and syntax-checked; they have not been run through the real Qminers simulator here**.

### Round 1–4: transferable framework, not guaranteed parameters

The tournament uses private PnL standardized within each round, weighted `0.8, 1, 1, 1, 1.2`. There is still only one anonymized asset per tape, but do **not** assume that Round 1–4 share Round 0's volatility, spread, arrival intensities, or the same signal calibrations: read each new public tape and measure them. Market making and a strict inventory envelope can transfer; specific quote sizing/cancel thresholds are **round-adaptive**.

## G. Research literature and implementation references

| Source | Specific transferable point |
|---|---|
| [Qminers official starter README](https://github.com/QminersOrg/qminers-algo-arena) | Exact matching, 5 ms action delay, penalty, cash/markout semantics, simulator CLI. |
| [Avellaneda & Stoikov (2008), *High-frequency trading in a limit order book*](https://math.nyu.edu/inmemoriam/avellaneda/HighFrequencyTrading.pdf) | Inventory-adjusted reservation price, intensity-sensitive quoting. **Their smooth inventory risk is not Qminers' discontinuous penalty.** |
| [Gao & Wang (2020), *Optimal market making in the presence of latency*](https://doi.org/10.1080/14697688.2020.1741670) | Latency is a state/control constraint, not just implementation overhead. |
| [Moallemi & Yuan (2017), *A model for queue position valuation*](https://moallemi.com/ciamac/papers/queue-value-2016.pdf) | Existing FIFO placement has option value; avoiding needless cancel/repost can improve execution economics. |
| [Donnelly & Gan (2018), *Optimal Decisions in a Time Priority Queue*](https://doi.org/10.1080/1350486X.2018.1506257) | Queue position affects optimal keep-vs-cancel decision. |
| [Cont, Kukanov & Stoikov (2014), *Price impact of order book events*](https://doi.org/10.1093/jjfinec/nbt003) | Short-horizon price changes related to best-level order-flow imbalance; scale varies with depth. |
| [Gould & Bonart (2015), *Queue imbalance as a one-tick-ahead price predictor*](https://arxiv.org/abs/1512.03492) | Imbalance has empirical directional predictive power, particularly in large-tick markets. |
| [Stoikov (2018), *The micro-price*](https://doi.org/10.1080/14697688.2018.1489139) | Future-price estimates can improve beyond raw mid-price. |
| [Huang, Lehalle & Rosenbaum (2015), *Queue-Reactive Model*](https://arxiv.org/abs/1312.0563) | State-dependent queue arrivals/cancellations for simulation and execution calibration. |
| [*The determinants of limit order cancellations* (2023)](https://doi.org/10.1111/fire.12363) | Cancels respond to expected execution value and queue position, not solely time-in-force. |
| [fedecaccia/avellaneda-stoikov on GitHub](https://github.com/fedecaccia/avellaneda-stoikov) | Compact reference implementation; theory, not plug-in strategy for Qminers. |

**External papers do not supply a theorem that permits safe or profitable threshold breaches in this specific exchange.** The ±100 flat penalty, ±1,000 acceptance rule, cash accounting, and 5 ms delay are **Qminers-specific**; derive the appropriate controls directly from the actual simulator and the current data.

## H. Reproducibility, repository layout and caveats

Suggested files to commit (never publish private round tapes):

```text
research/
  Qminers_Aggressive_Risk_Round0_Research.md
  assets/public_vs_private_best_mid.png
  assets/public_vs_private_spread.png
  round0_statistics.json
  compare_round0.py                    # offline analysis (not a sandbox submission)
strategies/
  zubry_v2.py
  zubry_aggressive_safe_q16.py
  zubry_aggressive_safe_q32.py
  zubry_aggressive_safe_q64.py
  zubry_aggressive_safe_q96.py
```

`results.zip`, raw private event logs, and raw Round 0 tapes should be kept under git-ignored `data/`/`logs/` unless the organizer specifically instructs otherwise. **Commit research, negative tests and hypotheses at least every 30 minutes.** Do not squash/rebase/force-push the team's research history.

### Methodology boundaries and status

- The **public** book was reconstructed by replaying raw G orders, F IOC orders and cancels using price-time matching. The **private** book uses aggregate market-owned `book_deltas.csv` from a particular Zubry run and is affected slightly by that run's executions; market-issued IOC records do not appear as standard `events.csv` adds.
- Comparisons use 5,750 public 1-second and 5,740 private 1-second book samples. Adjacent samples are dependent. The reported empirical correlations represent **associations**, not causal proofs of executable alpha.
- The 5 ms results are sampled at public *market event* times, not at uniformly random clock times; they are useful to measure a high-frequency callback environment, not necessarily random wall-clock latency.
- Extrapolating additional fills from volume executed *after* user fills is an **upper-bound-style diagnostic**, not a simulation of larger Zubry orders.
- Actual `result.json` fields, order schema and error restrictions remain authoritative. Cross-check any hand-written policy code against the official simulator and dashboard before a final submission.
- **Only the old V2 strategy has a known private PnL of +10,798.** No numeric PnL improvement has been demonstrated for any proposed aggressive quote variant in the current analysis.
