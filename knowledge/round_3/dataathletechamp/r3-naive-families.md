# R3 naive strategy families screen (experiment 20261108-r3-w6-naive-001)

Question: the field median validation score (>1M per 12,000 s, >83/s) is far above our best
(R3 public 330k, ~55/s; validation 411k). Is there a SIMPLE family we dismissed or never ran in
its simplest form?

Engine: official `simulator.simulator.ExchangeSimulator` in-process via
`experiments/round_3/dataathletechamp/20261108-r3-wave-runner-001/runner.py` (5 ms latency,
depth 20, ±100, 10,000/s penalty). Tapes: R3 public (sha256 1021586b…), R2 public (88ff641e…),
R1 for one check. "fit" = t < 2400 s, "eval" = t >= 2400 s, both PnL/s. Every family uses the
full tape (no slicing). All variants are kept in the experiment folder (grid1-3 JSON, results.jsonl).

Strategy file: `strategies/round_3/dataathletechamp/r3_naive_flow_follower.py`
(sha256 330d8ee5…); `FAMILY` selects mom | ema | mr | flow | obi | sweep | mm | wide | jump |
obimm | obiflow. Default = flow, 200 ms, 600 lots.

## Results (PnL, penalty 0 unless stated)

| Family / variant | R3 | R3 fit/s | R3 eval/s | R2 | R3 lots |
|---|---:|---:|---:|---:|---:|
| **flow 200 ms, ±600 (default)** | **279,902** | +45.8 | +47.2 | **170,949** | 285,900 |
| flow 100 ms, ±400 | 308,925 | +42.5 | +57.5 | 123,650 | 445,900 |
| flow 100 ms, ±600 | 273,793 | +39.2 | +49.9 | 164,046 | 245,500 |
| flow 300 ms, ±600 | 289,825 | +46.9 | +49.2 | 145,550 | 317,500 |
| flow 500 ms, ±1000 | 179,919 | +28.9 | +30.7 | 56,611 | 166,300 |
| flow 100 ms, ±100 (too fast) | -439,311 | -81.9 | -67.4 | -631,633 | 1,773,010 |
| mid momentum 50 ms/0.2 s … 1 s/5 s | -68k…-133k | <0 | <0 | -31k…-281k | 139k-704k |
| EMA trend 1/10, 5/60, 30/300 s | -139k, -67k, +20k | | | -2k, +87k, +35k | 2k-80k |
| 300 s mean reversion k 15/30/60 | +14k/+8k/+5k | | | -47k/-44k/-20k | ≤6k |
| book imbalance taker (L1-3) th .3/.5/.7 | -1.28M/-0.69M/-0.29M | | | -1.23M/-0.79M/-0.40M | |
| same, sign reversed th .5/.7/.85 | -0.80M/-0.38M/-0.14M | | | -0.90M/-0.45M/-0.19M | |
| touch maker Q5/20/50, improve Q20 | -37k/-166k/-294k/-278k | | | -7k/-52k/-97k/-130k | |
| wide quotes k 2/4/6, 1 s IOC exit | -163k/-63k/-32k | | | -86k/-23k/-15k | |
| fade ≥3-tick sweep 1/5/30 s | -266k/-259k/-209k | | | -164k/-161k/-162k | |
| follow ≥3-tick sweep 5 s; ≥2-tick 5/30 s | +66k; +94k/+98k | | | -26k; -75k/-78k | |
| jump rider 1000 lots (3 variants) | -600k…-838k | | | -574k…-892k | pen 472k-621k |
| OBI-gated touch maker (6 variants) | -19k…-112k | | | -3k…-49k | |
| flow gated by reversed OBI (4 variants) | 104k-256k | | | 9k-161k | |

R1 (calm maker tape) with the default flow file: -119,787 (0/20 positive blocks); our best
`r3_alpha_follower_p1_sw3.py` on R1 in the same runner: -112,045 (2/20), so both followers fail
there alike.

Go-flat timeout after the last ≥600 burst (experiment file `naive_families_v3.py`, flag
FLOW_HOLD_S, not in the committed file): 2 s R3 251,604 (max drawdown only -4.3k) / R2 30,228;
5 s 280,954 / 137,578; 15 s and 60 s equal hold-forever (bursts recur within ~15 s, so the
default is effectively always ±100).

## Findings

1. The simplest signed-taker-flow follower (sum of market-taker signed volume over a short
   window, hold ±100 until an opposite burst) is a broad plateau: windows 100-300 ms ×
   thresholds 400-800 give R3 246-309k and R2 91-172k, penalty 0, 8-10/10 positive R3 blocks.
   It does NOT beat our best on R3 (330k) but beats it on R2 (171k vs 109k), with a third of
   the volume (286k lots, ~1 tick/lot). Both public tapes informed the choice of window and
   threshold (~30 variants), so the public numbers are optimistic.
2. Everything else in its naive form loses. Book imbalance loses ~1.3 ticks/lot in BOTH
   signs: that is execution cost (200-lot flips into thin books), not a contrarian signal.
   Holding 1000 lots through big moves costs far more in penalty than the moves pay.
3. No naive family reaches the field median (>83/s). The gap is not explained by a simple
   family we skipped among these eleven.

Limitations: one public tape per market; R1 negative; no validation upload; the 1 s jump
risk seen on validation B (follower holds ±100 almost always) applies fully to this file.
Commands: see runner usage; grids `grid1.json`, `grid2.json`, `grid3.json` in the experiment.
