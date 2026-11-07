# Round 2 public tape: microstructure profile for strategy design

Question: what does `round2_public.csv` look like, what changed versus Round 1,
and which mechanisms are worth building into a Round 2 strategy?

## Data and provenance

- File: `data/round2/round2_public.csv` (untracked raw input, unchanged), 78,512,311 bytes,
  2,193,064 rows, SHA-256 `88ff641e962540c66fa1cc4a3547585d31838d0929340150690cabb4f3cfb9f4`.
- Comparison tape: `data/round1/round1.csv`, SHA-256 `362e8208…1735940` (see Round 1 provenance).
- Simulator: official `simulator/` at repo commit `91a1861` (unchanged).
- Scripts and raw logs: `experiments/round_2/luklen123/20261107-round2-public-tape-profile/`
  (`reconstruct.py`, `analyze.py`, `analyze2.py`, `regime.py`, `out_*.log`). They are not committed.
- Window: the full public tape, 0–6000 s. Everything here is in-sample, measured on the one public
  path. None of it is evidence about private PnL.

The book reconstruction follows the simulator's market-only matching: price-time FIFO, fills at the
resting order's price, the remainder of an IOC (`F`) is discarded, a GTC (`G`) rests. It produced
2,042,588 book events and 197,588 fills from 51,336 taker orders.

## Tape facts

| Metric | Round 1 (12,000 s) | Round 2 (6,000 s) |
|---|---|---|
| Events/s, insert:cancel | ~367, 51:49 | ~366, 51:49 (flat in every 10-min block) |
| Volume distribution | median 15, p99 ~973 | identical |
| IOC share of inserts | 4.3% | 4.8% |
| Mid path | 10000 → 10029, range 104 | 10000 → 9689.5, **range 552** |
| 1 s mid σ (ticks) | 0.92 | **3.80** |
| Spread = 1 tick (time share) | 93% | 84% (spread 2: 12%, ≥3: 4.6%) |
| Median L1 queue (lots) | ~920 | ~720, ~350 in stressed blocks |
| Lag-1 sign autocorrelation of mid changes | +0.07 | **+0.24** (moves run in streaks) |
| Vol clustering: corr(trailing 10 s vol, next 60 s vol) | 0.01 | 0.20 |
| L1 queue imbalance → 1 s mid, corr | **0.24** | 0.04 |
| Maker markout at 10 s, volume-weighted (ticks/unit) | +0.08 | **−0.53** |

The order-entry process is the same generator: same event rate, sizes, lifetimes (GTC median about
0.3 s) and placement (49% join the best, 34% rest one tick behind, 1.4% improve the spread). What
changed is the **latent price process**. Round 2 has volatility regimes with jumps and crashes:
block 6 fell 9945 → 9584, block 7 reached a low of 9459, block 8 rebounded to 9680. Single 60 s
moves run from −145 to +128 ticks. In those moves the spread averages 2–3 ticks and L1 depth
shrinks to ~150.

Other facts:

- 150,476 cancels refer to orders that had already been fully filled. They are harmless no-ops,
  and the same pattern appears in Round 1.
- Walls of 2,000 lots or more at the best price live ~0.3 s and fill 2%. Their directional effect
  is ≤0.18 ticks, so they carry no usable signal.

## Mechanisms: evidence and verdicts

1. **The plain join-the-touch maker loses.** The v2 maker (`strategies/zubry_v2.py`, 2-lot quotes,
   cap of 20) scored **−4032 PnL** on the R2 public tape (15,359 fills, penalty 0,
   `pnl_se` 1830). The same file scored **+11,206** on the R1 tape (22,716 fills, `pnl_se` 200).
   The official `trend_follower.py` scored **−391** (1,303 lots) on R2.
   Taker flow explains this. Measured at 10 s, takers of 18 lots or fewer give the maker
   +0.6 ticks/unit, but takers above 183 lots give −0.49. A small order at the back of a
   700-lot queue is mostly filled by the large, informed sweeps.
2. **Big-taker continuation survives the 5 ms latency.** These are mid moves in the taker's
   direction, measured from t+5 ms to t+10 s:

   | Taker size (lots) | Continuation (ticks) |
   |---|---|
   | <50 | +0.14 |
   | 50–200 | +0.52 |
   | 200–500 | +0.80 |
   | 500–1000 | +1.44 |
   | ≥1000 | +2.16 |

   In R1 the same effect was only 0.1–0.6 ticks. A taker that crosses the spread to follow them
   roughly breaks even, apart from ≥1000-lot takers at 10 s: net about +0.77, but n=753 and
   unstable at 60 s. **The main use is defensive:** after a large sweep, pull or skew the quote
   on the side that was hit.
3. **A volatility and spread regime filter is the most promising lever.** The maker's 10 s markout
   in the top quartile of trailing 60 s vol is −1.03 ticks/unit, against +0.07 in the second
   quartile. The current spread works as an instant, ex-ante detector: the mean |10 s move| is
   4.7 ticks at spread 1, 10.9 at spread 2 and 14.2 at spread 3. High-vol episodes cover 31% of
   the time and their median length is ~60 s, long enough to react to.
4. **Momentum and trend do not hold up.** Pooled corr(mid − MA600, next 30 s) is +0.13, but one
   crash drives it. Seven of nine 10-min blocks show negative correlation, meaning mean reversion
   within the block. Do not build a trend bet on this; the private path's direction is unknown.
5. **The Round 1 L1-imbalance alpha does not transfer.** Its correlation is 0.04 in R2 against
   0.24 in R1. Keep it behind a flag; it must not be a core signal for R2.

## Implications for the R2 strategy (hypotheses to test, not results)

- Start from the maker, but gate quoting on regime. Quote only at spread = 1 and with trailing
  vol below a threshold. Otherwise widen or stand aside.
- Use a large-taker trigger: after a taker of roughly 200 lots or more is observed, cancel or
  shift the quote on the side it hit for about 1–10 s.
- Keep the inventory cap well inside ±100. A 100-lot mark-out costs about 1 tick at normal depth,
  but in a crash an inventory of 20 can lose 100+ ticks per lot.
- The predeclared rejection rule for each variant: a paired public-tape PnL that does not beat
  `zubry_v2` (−4032), or any nonzero penalty. Then check chronological halves (0–3000 s and
  3000–6000 s, with book warmup preserved, no row slicing) to avoid fitting the crash.

## Reproduce

```bash
cd experiments/round_2/luklen123/20261107-round2-public-tape-profile
uv run --locked python reconstruct.py ../../../../data/round2/round2_public.csv out
uv run --locked python analyze.py ../../../../data/round2/round2_public.csv out
uv run --locked python analyze2.py out && uv run --locked python regime.py out
uv run --locked python -m simulator.main --backtest data/round2/round2_public.csv \
  --strategy strategies/zubry_v2.py --log-dir <exp>/sim_zubry_v2 --no-logs   # from repo root
```

## Limitations

- These are in-sample statistics from a single 100-minute path. The crash dominates the
  long-horizon numbers.
- The markouts are measured against the mid of the reconstructed public book. They ignore queue
  position and our own latency, so they are only indicative of what a real fill would earn.
- The private R2 tape probably comes from the same generator, judging by R0→R1→R2 continuity, but
  its regime timing, crash direction and magnitude are unseen.
