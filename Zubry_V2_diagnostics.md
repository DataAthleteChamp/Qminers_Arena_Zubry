# Team Zubry — V2 diagnostics and capacity experiments

Analysis of `zubry_v2.py`, `results.zip`, and `sample_v2.csv` supplied on 7 November 2026.

## Provenance — do not mix datasets

- `results.zip`: **private-backtest run** on `/work/backtest.csv`, ending at simulated 5739.942903 seconds, PnL +10,798. First exchange event 0.002285 s. This reproduces the playground leaderboard score.
- `sample_v2.csv`: distinct supplied tape, spanning 0.027441–5749.896405 seconds. First event and end prices differ. No simulator run against this uploaded tape was available here. Therefore no reported performance improvement is measured on `sample_v2.csv`.

## V2 baseline — measured, not hypothetical

| Measure | Value |
|---|---:|
| PnL | +10,798 |
| Inventory breach penalty | 0 |
| Traded volume | 15,226 lots |
| Result JSON `fills` | 7,629 |
| Detailed trade rows involving user | 7,687 (includes multi-part fills) |
| User orders submitted | 15,099 |
| User cancellation requests | 7,534 |
| Successful user cancellations | 7,500 |
| Cancellation failures | 34 |
| User maker trades | 7,687 |
| User taker trades | 0 |
| Maximum observed signed inventory | +12 / -12 |
| Time-weighted absolute inventory: median / p95 / p99.7 | 1 / 5 / 10 |
| Ending inventory | +2 |
| Maximum one-second sampled drawdown from running maximum | 12 PnL units |
| Approximate final PnL / traded lot | 0.709 |

Note: `fills` in `result.json` measures a different unit than individual `trades.csv` rows, so do not report these as the same event count.

Across essentially every five-minute interval, PnL grew by about 500–600 units. This is relatively stable profitability, not evidence of one lucky trade.

## New sample tape — potential room for higher size

- Rows: 2,000,000; duration ~95.83 minutes.
- Resting (`G`) inserts: 1,033,029; immediate-or-cancel (`F`) inserts: 34,503; cancels: 932,468.
- IOC volume median 41 lots, mean 108.7 lots; 70% of IOC orders have 20 or more lots; 44.7% have 50 or more lots.
- These are incoming aggressive *order sizes*, not necessarily available volume at your queue position. Do not assume an order of 32 lots will always fill.

## Code constraints

`QUOTE_SIZE = 2`, `MAX_INVENTORY = 20`, `IMBALANCE_WEIGHT = 0`, `INVENTORY_SKEW = 0.05`, `HALF_WIDTH = 0.5`.

The most direct capacity constraint is **QUOTE_SIZE=2**. Current observed inventory never exceeds 12, far below the penalty-free ±100. Raising `MAX_INVENTORY` *alone* should have little impact; test increasing the order quantity while maintaining a safe inventory cap.

V2 has at most one pending/resting order per side, tracks actual fills, and sends cancel requests when the quote target changes. This design makes scaling quantity relatively straightforward, but the resulting profit cannot be linearly extrapolated: bigger quotes can create adverse selection, partial fills and slower inventory reversion.

## Candidate controlled experiments

These candidates modify **only quote size and safety cap**. They preserve the exact existing V2 algorithm and its Python sandbox-compatible imports.

| Strategy file | Quote size | Inventory cap | Purpose |
|---|---:|---:|---|
| `zubry_v2.py` | 2 | 20 | Baseline |
| `zubry_quote8.py` | 8 | 80 | Conservative capacity increase |
| `zubry_quote16.py` | 16 | 90 | Medium capacity increase |
| `zubry_quote32.py` | 32 | 95 | Aggressive but penalty-free target |

Run using your already-installed official simulator:

```bash
mkdir -p logs/zubry-v2 logs/zubry-q8 logs/zubry-q16 logs/zubry-q32
uv run exchange-simulator --strategy strategies/zubry_v2.py --backtest data/sample_v2.csv --log-dir logs/zubry-v2 --no-logs
uv run exchange-simulator --strategy strategies/zubry_quote8.py --backtest data/sample_v2.csv --log-dir logs/zubry-q8 --no-logs
uv run exchange-simulator --strategy strategies/zubry_quote16.py --backtest data/sample_v2.csv --log-dir logs/zubry-q16 --no-logs
uv run exchange-simulator --strategy strategies/zubry_quote32.py --backtest data/sample_v2.csv --log-dir logs/zubry-q32 --no-logs
```

The variants need to be copied from these attachments into your repo's `strategies/` folder first; copy the CSV into its `data/` folder. If the file is a private-round tape, do not add it to Git.

Compare `result.json`: `pnl`, `pnl_se`, `fills`, `traded_volume`, `inventory`, `breach_penalty`, inventory quantiles. Inspect `pnl.csv` for sampled max drawdown and worst periods.

## Interpretation and next step

1. **First** check whether increasing size improves PnL on the *same* tape. It may be that profit rises rapidly even with a zero-penalty cap.
2. Retain a 5–20 lot safety margin to the ±100 threshold when testing high-volume passive quoting. The provided V2 headroom check accounts for its own known orders but should still be stress-tested against partial fills and delayed cancellation.
3. If capacity scaling raises drawdown or loses money, compare post-fill 10/50/100 ms price markouts and fill sizes to see whether your larger positions are getting adversely selected.
4. Only **after** measuring capacity-constrained profits should you investigate deliberate ±100 breaches. Penalty is 10,000 PnL per simulated second, so there is no advantage to breaching while your strategy is profitable at tiny inventories.
5. Commit baseline, experiments and rejected variants with honest notes at least every 30 minutes; no rebasing or history rewriting. Keep round data private.

### Decision rule for deliberately breaching inventory

`expected_additional_PnL_after_all_execution_costs > 10_000 * expected_extra_breach_time_in_seconds + risk_margin`.

Also include the risk of the exit not filling, latency (all order/cancel actions are delayed 5ms) and liquidity-dependent liquidation markout. Do **not** optimize this rule on public data alone.

## Disclaimer

The output variant files were syntax-checked using Python 3.13, **but they have not been run through the Qminers simulator in this environment**, so no PnL projections or guarantees are made. The publicly hosted simulator repository is viewable, but its source package could not be retrieved into this runtime.
