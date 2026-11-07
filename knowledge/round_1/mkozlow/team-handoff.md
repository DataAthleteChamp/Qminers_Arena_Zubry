# Round 1 team handoff: maker execution, signals and penalty tests

## Current decision

The strongest completed full-public-tape run is a **64-lot midpoint maker: PnL206,364, zero penalty, no taker activity**. A regression-based maker with value-aware queue retention is close at203,473. Large quote throughput and avoiding unnecessary cancel/repost cycles matter more than prediction error alone.

Retained strategy: [midpoint_maker_64.py](../../../strategies/round_1/mkozlow/midpoint_maker_64.py). This is an exact copy of the tested source, not a cleaned or retuned approximation.

- Strategy SHA-256:`86bed1db3ca7d2b4bc355bcea6d76b80e94bcba35529450297173ed3bee7bee4`.
- Data:`data/round1/round1.csv`.
- Data SHA-256:`362e8208be1eeec32ad190d097774e26448f0d5149575a8e1b1efd1db1735940`.
- Official simulator-source digest:`6dba6395cd6104e47132c53a251f2f0781b4d66d910c34e0025cc7843fbeadb5`.
- Branch during research:`r1/mkozlow/research`.
- Local conservative preflight passed. Server validation/private performance remain unverified.

The result is a selected benchmark on a repeatedly inspected public tape. Zero-forecast has no active fitted alpha, but its size and execution policy were selected on this tape. Do not report206,364 as private PnL or a guaranteed transfer result.

## Exact retained policy

Market-only midpoint is `(best_market_bid + best_market_ask)/2`. Maker fair value equals that midpoint: the active maker forecast is zero.

- Bid:`floor(midpoint -0.5)`; ask:`ceil(midpoint +0.5)`.
- Clamp prices to remain non-marketable against the opposite market touch.
- At one/two-tick spreads this joins the touches; at wider spreads it can improve inside them.
- Nominal quote size64 per side, clipped by available same-side capacity.
- Filled inventory cap±100, including worst-case pending/resting/cancel-pending fills.
- One outstanding order per side; cancellation does not free its slot or reservation.
- Recalculate on each callback; reprice changed quotes after a20ms minimum quote age, waiting for terminal confirmation before replacement.
- Trading begins at the first valid two-sided book. No active taker entry or emergency overflow policy.

The retained file includes disabled experimental branches and unused forecast coefficients from its tested lineage. `TAKER_ENABLED=False` and active maker weights/intercept are zero. Leave those branches disabled for exact reproduction.

## Verified full-tape result

Official engine outcome for the retained source:

- PnL206,364; penalty0; cash-796,536; final inventory+100.
- Book-liquidation mark price10,029, giving`-796536 +100×10029 =206364`.
- Reported filled orders30,005; traded volume1,557,720 lots.
- Maximum actual and reserved exposure100; tracked rejections0.
- Sampled maximum drawdown1,144; this uses one-second PnL samples.
- Cancel requests18,390; quantity filled while cancel-pending18,326 lots.
- PnL changes:95,084 in0–6000s,56,251 in6000–9000s,55,029 afterward.

Cancel requests are counts and cancel-race quantity is lots: do not divide them into a failure percentage. Negative cash is not loss; official PnL includes executable book-liquidation value and penalties. Final liquidation is scoring, not a strategy-submitted closing order.

## Comparable maker results

Full-tape, maker-only, cap100:

- Regression-adaptive64 lots:143,622, segment changes73,299 /36,246 /34,077.
- Regression-adaptive96 lots:167,045, segments83,035 /41,802 /42,208.
- Zero-forecast64 lots:206,364, segments95,084 /56,251 /55,029.
- Regression with value-aware retention32 lots:141,232, segments69,105 /38,111 /34,016.
- Regression with value-aware retention64 lots:203,473, segments93,213 /56,573 /53,687.
- Regression-adaptive nominal200 lots, cap100:186,707, zero penalty. Large orders can reverse inventory within the band; nominal size is not identical to allowed exposure.

Regression variants use coefficients fitted on the first6000s of this public tape, so full totals include their fitting period. Later segment changes carry positions from earlier trading and are not independent backtests.

Earlier controlled tests kept orders disabled before6000s and inventory flat at activation:

- Adaptive5:10,961, later-period changes8,500 /2,461.
- Adaptive16:19,671, changes10,781 /8,890.
- Adaptive32:40,184, changes22,627 /17,557.
- Adaptive64:70,153, changes36,076 /34,077.
- Value-retaining32:72,124, changes38,108 /34,016.

These final-half totals must not be compared directly with full-tape totals. At fixed32-lot size, retention raises PnL about79.5% and cuts cancel requests84,156→2,847. It keeps a quote if forecast edge remains≥0.05 ticks and desired price is less than two ticks away. This is a proxy for queue value, not a fitted conditional-fill model.

At fixed64-lot full-tape size, ordinary adaptive repricing makes159,102 cancels, value retention5,420, and zero-forecast quoting18,390. The predictive model can improve midpoint forecasts while its quote churn destroys more execution value than the alpha adds.

## Research findings worth reusing

### Market structure

The tape contains4,411,336 events over approximately12,000s. Time-weighted mean spread is1.07064 ticks; approximately93.1% of regular samples have one-tick spread. Average touch depth is about1326 bid/1306 ask lots, but depth has substantial variation. Median event gap1.795ms means several events can occur during5ms action latency.

Order sizes are heavy-tailed. Insert quantity median15, p90154, p99973. Orders≥100 lots account for approximately15% of inserts but77% of submitted quantity. Submitted quantity is not executed volume.

### Transfer and price-level fitting

Exact size distributions are stable across chronological thirds, with total-variation distance about1.4–1.5%. Absolute midpoint occupancy differs much more, approximately25–79% between thirds.

An exact price-point future-change table improves30s training error8.6% but worsens later error5–6%. Almost all evaluation price levels were already seen; this is not mainly an unseen-price problem. Absolute price, modulo5/10 and simple round-size features did not improve forward-time tests.

The supplied Round0 public/private report supports shared mechanics with different price paths, but its forensic numbers were not independently rerun here. Treat stable size/queue dynamics as a working transfer hypothesis, not a promise of identical Round1 price frequencies or parameters.

### Signals

Imbalance and recent aggressive flow complement one another. Fixed combined models reduce250ms prediction error about21–22% versus predicting no change; a small nonlinear model reaches roughly24% in two later periods. Plain price-history features do not help. Five-second forecasting gains are much weaker.

Same-price additions add approximately6.3% relative MSE improvement beyond book/flow in later250ms checks, with paired60s-block bootstrap intervals above zero. New-best additions contribute less than1%. These percentages are prediction-error reductions, not trading returns.

### Cancellations and replenishment

Approximately13.24% of cancellation requests target already-absent orders. Use remaining quantity, not original submitted size, when measuring actual withdrawal. Mean cancellation-request age is0.467s and changes little across size buckets; it is not necessarily live order lifetime.

Public snapshots plus maker IDs in trades reconstructed all70,286,924 lots of live touch cancellations and99.987% of touch additions on this tape. Ambiguous visibility/initialization additions were excluded. Engine instrumentation provided validation labels only, not predictors.

Cancellation history adds little directional prediction after current depth/imbalance/flow. Same-price arrivals are more informative. Cancellations remain critical to execution because replacing orders discards queue priority and a pending cancel can still fill.

## Taker and penalty findings

Simple taker signals fail after spread/depth costs even when they predict favorable midpoint movement. Following a large sweep is not equivalent to predicting its next move.

Actual100-lot pure-taker trials lose954,469 with50ms unwind and209,817 with1s unwind, with zero inventory penalty. Maker/taker hybrids also underperform the corresponding five-lot maker:100-lot hybrid1s makes3,719 versus10,961 maker-only. The earlier500-lot hybrid makes1,256 gross but pays13,684.81 penalty, ending-12,428.81.

Maker overflow was tested separately; the taker result was not treated as proof about passive acquisition:

- Adaptive200-lot/cap300 natural recovery: gross301,468; penalty78,952,358.24; net-78,650,890.24.
- Zero-forecast64-lot/cap300: gross210,459 versus206,364 at cap100; penalty78,755,540.27; net-78,545,081.27.
- Adaptive900-lot/cap900,10ms grace then IOC excess reduction: gross-436,344; penalty2,065,633.01; net-2,501,977.01.
- Same adaptive900-lot policy with50ms grace: net-4,707,365.32.
- Zero-forecast900-lot/cap900,10ms grace: gross-2,325,763; penalty6,270,304.01; net-8,596,067.01.

Penalty is10,000 per exact second with actual`|inventory|>100`, independent of excess quantity and without whole-second rounding. All measured breach durations were independently reconstructed from private fills and matched official charges.

Natural recovery is too slow for that clock. Fast emergency reduction lowers duration but incurs adverse fills and repeated forced execution costs; those timed policies lose even before penalty. These results reject the tested broad overflow rules, not every conceivable rare opportunity.

## Correctness and validation

Use the official engine with5ms actions, cap100 penalty boundary, hard potential-position wall1000, zero fees and liquidity-based final markout. Never substitute midpoint valuation for official scoring.

Pending same-side extrema are`I+B` and`I−S`. Opposite-side pending quantities must not be netted away. Keep reservations through cancel/modify acknowledgment. Recompute IOC reduction quantity after cancellation-race fills, not before.

Focused tests cover capacity with opposite orders, cancel-pending reservations, fill/cancel races,500-lot burst reservations, cancellation-safe unwind and excess-only emergency quantity. Runtime assertions check inventory parity, configured exposure and exact penalty duration. All fifteen trials in studies012–016 passed local preflight, preserved strategy/data/simulator hashes and produced successful outcomes. Earlier studies007–010 add thirteen execution trials. Local preflight does not implement the complete server sandbox checker.

## Reproduce the retained baseline

From the repository root with the original CSV available:

```bash
uv sync --locked
uv run --locked python -m tools.preflight strategies/round_1/mkozlow/midpoint_maker_64.py
uv run --locked exchange-simulator \
  --strategy strategies/round_1/mkozlow/midpoint_maker_64.py \
  --backtest data/round1/round1.csv \
  --log-dir experiments/round_1/mkozlow/team-recheck-midpoint64/logs \
  --no-logs
```

Use a fresh log directory and preserve source/data hashes. No network, files or team-module imports are needed inside the standalone strategy. Do not enable unused branches and claim the same tested result.

## Artifact map and team next steps

Completed local experiment directories under`experiments/round_1/mkozlow/`:

- `signal-execution-007`, `inventory-capacity-008`: initial fixed signal/execution and capacity tests.
- `adaptive-hybrids-009`, `taker-horizon-010`: adaptive quoting, aggressive hybrids, horizon check.
- `price-size-distributions-011`: exact price/size/lifetime tables and failed price-anchor fitting.
- `maker-size-queue-012`: matched size and queue-retention tests.
- `full-maker-benchmarks-013`, `queue-preserving-full-014`: full-tape benchmarks and zero-alpha control.
- `maker-penalty-015`, `zero-maker-penalty-016`: natural/timed maker overflow, independent penalty verification.

Plans, frozen sources, provenance, outcomes, fills, PnL and HTML reports remain local experiment artifacts and are not part of the default commit package. This handoff is self-contained; colleagues need the raw tape to reproduce it. Older descriptive inputs remain in the pre-layout`experiments/r1-*` folders and were not moved.

Next: reproduce the retained strategy and confirm server compatibility; compare the same frozen policies across public/private tapes when available; test no-penalty quantity100/200 and conditional fill value before increasing model complexity. If testing penalty again, require a specific rare mechanism that beats the strong in-band maker after both execution costs and the exact clock.

The supplied Round0 report contains a five-weight scoring sequence; current`competition.json` records four private-round weights`[0.8,1.0,1.0,1.2]`. Current official/local configuration takes precedence.

Suggested minimal review/commit package is this handoff plus the retained strategy and owner README. Detailed curated notes in this owner folder may accompany it. Do not stage raw experiments, data or generated reports by default. No Git commit, push or external sharing was performed while preparing this package.
