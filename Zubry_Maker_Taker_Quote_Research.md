# Zubry | Qminers Round 0: quote size, fair value, maker/taker decision

**7 November 2026.** Research memo for Team Zubry. The files in this package are experimental candidates **not validated with Qminers' official `exchange-simulator`**. Do not treat the replay figures as private scores.

## Executive decision

- Retain a **passive market-making core** and a strict worst-case exposure envelope of ±100 filled lots. Size 200 is a convenient *requested* maximum, NOT a 200-lot executable order from a flat inventory: actual size is capped by directional remaining headroom.
- Move to **pricing experiments** next: alter microprice weight and inventory skew independently. In our independent Round 0 public replay, q200, cap100, skew0.05, microprice0 produced +221,070; skew0, microprice0.25 produced +252,305 (+14.1%). Even the latter is **not an official result** and is selected on the same public tape.
- Do not blindly use market-taking IOC orders as an alpha strategy. On both Round 0 public and private books, a simple top-level-depth-imbalance signal's predicted midpoint move did not reliably cover crossing the spread. Use IOC chiefly for rebalancing, or if a stronger validated signal predicts executable profit net of spread/latency/liquidation.
- Retain existing early FIFO positions if their expected post-fill edge is positive; shrinking retains priority, but cancel/repost gives up priority. Conditional cancellation should depend on staleness, toxic flow, inventory and queue-ahead estimate.

## Measured experiments

### Fixed quote-size sweep (independent C++ FIFO replay on public `sample_v2.csv`, 2,000,000 market rows)

| Quote-size target | Replay PnL | Traded volume | Max abs inventory |
|---:|---:|---:|---:|
| 2; max inventory 20 | 10,395 | 15,030 | 13 |
| 32; max inventory 100 | 97,465 | 158,981 | 56 |
| 64; max inventory 100 | 140,577 | 243,708 | 83 |
| 96; max inventory 100 | 173,209 | 307,989 | 100 |
| 160; max inventory 100 | 208,032 | 373,320 | 100 |
| 200; max inventory 100 | 221,070 | 398,962 | 100 |
| 300–1000; max inventory 100 | 221,070 | 398,962 | 100 |

A target greater than 200 makes no difference in the tested **single bid + single ask** algorithm under a ±100 worst-case envelope. This is a capacity saturation, not proof that larger positions would be uneconomic with a different risk regime.

### Pricing sweep on q200 + ±100 (54 independent replay configurations, *same public tape*)

| Pricing rule | Estimated public PnL | Traded volume | Mean PnL/lot |
|---|---:|---:|---:|
| Inventory skew 0.05, microprice weight 0 (previous baseline) | 221,070 | 398,962 | 0.554 |
| Inventory skew 0, microprice weight 0 | 238,110 | 439,002 | 0.542 |
| **Inventory skew 0, microprice weight 0.25** | **252,305** | **293,993** | **0.858** |
| Inventory skew 0.01, microprice weight 0.50 | 233,287 | 382,024 | 0.611 |

`center = mid + microprice_weight * (microprice - mid) - inventory_skew * filled_inventory`, with `microprice=(ask*best_bid_volume+bid*best_ask_volume)/(best_bid_volume+best_ask_volume)`. Buy/sell quotes remain *at or beyond* the market's best bid/ask, so the candidate does not intentionally cross the spread. Because quotes are tick-rounded, small changes in these parameters can cause discontinuous price and fill changes. Microprice-weight 0.25 and 0.50 produced identical results with skew=0 in this replay—check behavior in the official engine rather than generalizing.

**Three-period restart sanity check** (public tape, not an untouched holdout):

| Candidate | First ~3,450 s | Next 1,150 s | Final ~1,150 s |
|---|---:|---:|---:|
| 0.05 / 0 | 137,033 | 44,417 | 42,398 |
| 0 / 0 | 147,202 | 47,753 | 46,992 |
| **0 / 0.25** | **153,182** | **50,955** | **50,470** |
| 0.01 / 0.5 | 143,555 | 48,099 | 46,562 |

**Warning:** zero inventory skew may be more sensitive to directional trends; public and private Round 0 price paths differed substantially. Compare private outcome through allowed submissions and use results from subsequent rounds. Repeat an official simulator run before selecting the final file.

### Maker vs simple taking proxy

From the **actual V2 private backtest** we observed 7,687 maker-fill rows (7,629 counted fills in `result.json`, because these are not necessarily the same counting convention) and no user taker trades. Average signed future-mid markout per traded lot was **~+0.71 ticks** at 1s and **~+0.70 ticks** at 5s, using 1-second reconstructed private-market snapshots. This is an *execution markout proxy*, not a realized round strategy PnL per lot.

Hypothetical **IOC at observed touch** on a 1-second order-book snapshot, direction `sign((best_bid_depth-best_ask_depth)/(sum))`: mean signed future-midmark minus entry price:

| | Public 1s | Private 1s | Public 10s | Private 10s |
|---|---:|---:|---:|---:|
| Every snapshot | -0.646 | -0.658 | -0.612 | -0.624 |
| Absolute imbalance >= 0.5 | -0.396 | -0.404 | -0.341 | -0.393 |
| Absolute imbalance >= 0.75 | -0.272 | -0.283 | -0.207 | -0.290 |

**Important limitations:** This hypothetical taking analysis does not apply 5 ms action latency, does not attempt to reproduce actual IOC fills, does not include execution depth for larger orders, nor account for inventory/reversals. It is sufficient to reject naive imbalance-directed taking as the default, **not** to rule out all aggressive strategies.

## Implementation plan: separate edge, risk and execution

### Strict zero-penalty directional inventory reservation

For signed inventory `I`, current live and in-flight BUY quantity `B`, and current live and in-flight SELL quantity `S` (including cancellation requests pending acknowledgement):

```
BUY_HEADROOM  = max(0, 100 - I - B)
SELL_HEADROOM = max(0, 100 + I - S)
```

Do NOT net buys against sells, because one side could fill first. An outgoing cancel remains executable for at least 5 ms. Every new order must be capped by these bounds. Actual cash can be negative; terminal PnL uses cash + depth-based liquidation markout - inventory-penalty.

### Maker: expected value of keeping / shrinking / canceling

For each order estimate from real market-book data and official backtests:

```
expected_maker_value = P(fill within horizon | queue_ahead, price, flow, state)
                       * E[filled_quantity * signed(future_mid - execution_price) | fill]
                       - inventory_risk_cost
                       - adverse_selection_tail_reserve
```

If too much exposure but quote still attractive, use `modify_order(order_id, new_quantity)` (shrink-only, priority retained) after accounting for 5 ms latency. Cancel an order when adverse-selection risk or risk-limit violation dominates its queue option value, or when the replacement quote has sufficiently higher expected net value to justify losing FIFO position. Do not constantly cancel/repost at the same price.

### IOC: use only when expected advantage exceeds spread and delayed execution costs

For a proposed BUY IOC quantity `q`, estimate **the actual asks expected at arrival t+5ms** and depth-walking VWAP `A_VWAP(q,t+5ms)`:

```
IOC_BUY_VALUE = q * (forecast_exit_liquidation_value_per_lot - expected_fill_VWAP)
                - risk_budget
                - estimated_inventory_penalty_if_any
```

Only send when `IOC_BUY_VALUE > buffer`, and make sure the proposed max execution cannot breach the safe exposure envelope. Symmetrically for sell.

**Recovery IOC** can be rational even when standalone markout is negative if it saves substantial future inventory risk or a 10,000-per-second threshold penalty. Use a separate `risk_reduction` branch rather than confusing this with positive-alpha taking.

### Testing order, not just total PnL

1. Run V2 q2 / q200 with old 0.05/0 pricing settings in **official** simulator; verify PnL, actual inventory, penalty=0, filled volume, order rejections, matching, ending markout.
2. Run q200 zero-skew with no microprice weight: isolate inventory price skew.
3. Run q200 zero-skew + 0.25 microprice weight: isolate toxicity-side quote widening.
4. Run q200 small-skew 0.01 + 0.5 microprice weight: conservative robustness candidate.
5. Repeat on at least three independently generated tapes or round-specific public data; reserve a future portion to monitor generalization. Do not use the organizer's private scoreboard for iterative parameter tuning if you can avoid it.
6. Evaluate *marginal PnL vs traded volume*, fill-weighted post-trade markout, drawdown, ending liquidation depth, inventory distribution, cancellation races and total runtime.
7. Add one IOC recovery test against the same strategy, then an alpha IOC test. Require incremental gains over passive-only and zero risk-limit violations.

## References (public research, not proprietary claims)

1. Official Qminers code/rules: https://github.com/QminersOrg/qminers-algo-arena
2. Sasha Stoikov, **The Micro-Price: A High Frequency Estimator of Future Prices**: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2970694 ; example code https://github.com/sstoikov/microprice
3. Cont, Kukanov & Stoikov, **The Price Impact of Order Book Events**: https://arxiv.org/abs/1011.6402
4. Moallemi & Yuan, **A Model for Queue Position Valuation in a Limit Order Book**: https://business.columbia.edu/faculty/research/model-queue-position-valuation-limit-order-book
5. Garriott, van Kervel & Zoican, **Queuing and Inventories in Limit Order Markets** (2025): https://doi.org/10.1016/j.finmar.2025.100982
6. Cartea, Jaimungal & Sánchez-Betancourt, **Latency and Liquidity Risk**: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3433739
7. hftbacktest, queue and partial-fill models: https://hftbacktest.readthedocs.io/en/latest/order_fill.html
8. Hummingbot, inventory skew and refresh tolerance: https://hummingbot.org/strategies/v1-strategies/strategy-configs/inventory-skew/ and https://hummingbot.org/strategies/v1-strategies/strategy-configs/order-refresh-tolerance/

## Commands to reproduce

From private team copy of official repository, put the Python files under `strategies/` and full Round 0 public file under `data/`:

```bash
for candidate in zubry_safe_q200.py zubry_q200_micro_025.py zubry_q200_micro_025_skew_001.py zubry_q200_micro_05_skew_001.py; do
  name="${candidate%.py}"
  uv run exchange-simulator --strategy "strategies/$candidate" \
     --backtest data/sample_v2.csv --log-dir "logs/$name" --no-logs
done
```

**Commit these hypotheses and failed tests** as well as successful versions, at least every 30 minutes, without squashing history. Do not commit private round tapes. The above metrics are from independent replay or approximate market snapshots, not actual Qminers official simulator outputs except the original V2 private-result records.
