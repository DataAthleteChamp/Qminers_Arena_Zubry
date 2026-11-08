# R3 hidden-IOC probe (negative result)

Experiment `20261108-r3-w5-probe-001` (branch `r3-da-probe`), owner dataathletechamp, 2026-11-08.
Strategy: `strategies/round_3/dataathletechamp/r3_follower_probe.py` (sha256 7deee03e…4371; flag
`PROBE_ON`, default **False** = incumbent U4 `r3_alpha_follower_p1_sw3.py` e4dfd2ce…574f, unchanged).

## Question and mechanism

Tape screen (from the raw tapes; Lifespan F = IOC, G = resting limit, G never crosses): market IOC
limits that do not reach the opposite touch are invisible to a live strategy but were reported to
predict against their side. R3 public, spread >= 2: buy IOCs with limit in [ask-1, ask) n=814,
signed 1 s mid move -1.49 ticks (R2 -1.70); limit < ask-1 n=230, -2.24 (R2 -4.30).
Market takers match user resting orders (price-time), so a 1-lot LIMIT probe at bid+1 / ask-1 makes
such IOCs visible. Per market taker that fills a probe: `mkt` = also trades with market orders
(marketable sweep), `lim` = its remainder rests (G insert), `hid` = neither (non-marketable IOC).

Implementation: probes only when the market spread >= `PROBE_MIN_SPREAD` (2), cancel/re-place on
touch change, separate order book-keeping, probe trades excluded from the follower's taker groups,
probe residual |inventory - target| <= `PROBE_TOL` (5) left alone until the next target change,
follower sends cut (same-side probes cancelled) so inventory incl. pending never exceeds 100.
`PROBE_USE`: `none` (c, cost control), `a` (hidden event = A event in direction -taker side),
`gate` (b, hidden event within 1 s allows (same dir) / blocks (opposite) an opposite-A flip).

## Data, engine, commands

R3 `round3_public.csv` 1021586b…2d15, R2 `round2_public.csv` 88ff641e…f9f4, `simulator/simulator.py`
c37b2262…c4d4. Fit window t < 2400 s, eval t >= 2400 s (per-second figures). Official engine
in-process (5 ms, depth 20, +-100, 10,000/s) via the wave runner, grid `grid_screen.json`:
`runner.py --strategy <abs r3_follower_probe.py> --grid grid_screen.json --tapes r3,r2 --workers 2`.
Default check: `exchange-simulator --strategy r3_follower_probe.py --backtest data/round3/round3_public.csv
--no-logs` -> pnl 330,208, penalty 0, fills 1,666 (identical to U4). `tools.preflight` passed.
The screen ran on a pre-lint revision of the probe code; after the lint-only refactor the committed
file re-ran (c) on R3 = 306,555 (identical) and the default CLI = 330,208 (identical).

## Results (official engine, no penalties anywhere)

| variant | R3 total | R3 fit/s | R3 eval/s | R2 total |
|---|---:|---:|---:|---:|
| U4 / default (PROBE_ON False) | 330,208 | 51.6 | 57.3 | 109,317 |
| (c) probes on, signal unused | 306,555 | 47.9 | 53.2 | 94,912 |
| (a) hidden event = A event | 297,540 | 52.9 | 47.4 | 18,980 |
| (b) hidden event flip gate | 260,459 | 43.9 | 43.1 | 85,178 |

Probe-fill classes in (c): n, then mean taker-side-signed mid move at 0.5 / 1 / 2 s in ticks.

| class | R3 n | R3 0.5/1/2 s | R2 n | R2 0.5/1/2 s |
|---|---:|---|---:|---|
| mkt | 8,192 | +0.82 / +0.94 / +1.02 | 6,962 | +0.94 / +0.91 / +0.96 |
| lim | 5,799 | +0.81 / +1.03 / +1.22 | 5,213 | +0.58 / +0.53 / +0.55 |
| hid | 1,309 | +0.50 / +0.47 / +1.02 | 1,231 | -0.19 / +0.02 / -0.39 |

Probe fills: R3 17,510 lots, R2 15,469 lots, filled ~0.19 ticks better than the send-time mid but
followed by ~+0.9 tick adverse moves (91 % of probe-filling takers are `mkt`/`lim` informed flow).

## Verdict

Rejected against the predeclared rule (R3 > 330,208, R3 eval/s >= 56.3, R2 >= 87,000). The hidden-IOC
signal is **not confirmed** in the official engine: the `hid` class is in the taker's direction on R3
(+0.47 ticks at 1 s) and ~0 on R2, not -1.5 to -1.7 against it. Probes alone cost 23.7k (R3) /
14.4k (R2) through adverse selection; using the signal makes it worse. Flag left off.

Limitations: only 0.4 % of market IOCs have volume 1 (R3 and R2), so fully absorbed marketable IOCs
cannot explain the gap; the discrepancy with the tape screen (selection by probe presence/latency,
conditioning or sign convention of the screen) was not resolved within the 35-minute budget.
Public tapes only; not a private-round estimate.
