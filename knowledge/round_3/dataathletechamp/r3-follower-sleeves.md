# Round 3 follower sleeves (W9): fast flow sleeve + slow A sleeve. Rejected

Question: the oracle-gap study says 57% of U7's gap is late entry and 36% is 0.75–0.9 s counter-swings during the 5 s
hold. Does splitting U7's single ±100 target into two sleeves capture the 1–5 s momentum and dodge the swings?

- FAST sleeve, `SLEEVE_F` lots. Driven only by FLOW_TRIG/TRIG1. Hold `SLEEVE_HF_S`, extended by same-sign signals;
  opposite signals flip it with no gate. Trailing exit: once the peak favourable mid move is >= 1 tick, exit on a
  1-tick retrace, IOC at once, and block re-entry in that direction for `SLEEVE_HF_S`.
- SLOW sleeve, `100 - SLEEVE_F` lots. Driven only by A events, with the P1 gate and the 5 s hold.
- Target = sum of the two sleeves (|sum| <= 100). Every target change re-quotes the join-touch exit. U7 IOC execution.

File: `strategies/round_3/dataathletechamp/r3_follower_sleeves.py`, sha256 cc9e35d29fcd…75aa (40,205 bytes).
`SLEEVES = False` (default) is U7 (`r3_follower_u7_flow_deepfv.py`, d2a0fc9c…f897) exactly. Runner: R3 413,588 and
R2 167,166. Official CLI on R3: pnl 413,588.00, penalty 0, abs-inventory q50 = 100. Preflight passed.
Data: R3 public sha256 1021586b92a3…, R2 public 88ff641e9625…; `simulator/simulator.py` c37b2262186f….
Official engine (5 ms, depth 20, ±100). The whole public tape is used; the fit/eval split is at 2400 s.

| variant (trail 1/1 unless noted) | R3 | R3 eval/s | R2 | lots R3 |
|---|---:|---:|---:|---:|
| **U7 (SLEEVES off)** | **413,588** | **74.6** | **167,166** | 384,500 |
| F40 HF1 | 275,693 | 48.7 | 69,818 | 418,662 |
| F40 HF2 | 252,065 | 44.8 | 67,732 | 378,578 |
| F50 HF1 | 247,463 | 43.8 | 54,041 | 445,444 |
| F50 HF2 | 217,606 | 38.4 | 49,446 | 393,980 |
| F60 HF1 | 233,802 | 41.8 | 36,890 | 513,728 |
| F60 HF2 | 199,916 | 35.4 | 44,572 | 439,020 |
| diag F50 HF1, no trailing | 308,209 | 54.4 | 87,313 | 449,194 |
| diag F50 HF5, no trailing | 312,971 | 54.0 | 123,338 | 373,938 |
| diag F0 (slow sleeve only) | 357,488 | 63.1 | 107,856 | 313,936 |

Plumbing check: F0 (SLOW sleeve only: A events with the P1 gate) gives exactly U6 on both tapes
(357,488 / 107,856). Penalty was 0 in every run.

Verdict: **REJECTED**. No variant comes close to U7 on either tape: each loses 33–52% on R3 and 58–78% on R2. The
loss grows with F, and HF 2 is worse than HF 1 on R3. No neighbour keeps any gain, so the acceptance rule fails
everywhere.

Why, from the diagnostics:

- U7 is almost always fully positioned. Its abs-inventory median is 100. On R3 it makes only 42 entries from flat
  against 1,886 flips, and its passive exits total 1,285 lots.
- The sleeves keep going flat:
  - the FAST sleeve makes 1.9–2.7k entries on R3 and 1.2–1.4k trailing exits;
  - the SLOW sleeve, without the flow extensions, starts from flat 115 times.
- Every flat interval gives up the drift U7 keeps. Every extra round trip costs about 1 tick per IOC lot.
- The 1-tick trailing exit is the worst part on R3: removing it gains about 61k at F50 HF1. Even so, the split is
  still about 105k below U7.
- Separate routing costs about 100k on R3 and 44k on R2 by itself: F50 with a 5 s fast hold and no trailing still
  lands well below U7.
- Every split variant is also below the A-only F0 (U6) on R3. There, on a 5 s hold, half of the lots on flow triggers
  alone earn less than the same lots on A events. R2 is mixed: F50 HF5 with no trailing makes 123k against F0's 108k.
- The flow triggers are worth more as entry, extension and flip events for the whole 100 lots than as a separate
  short-hold book.
- Takeaway for the oracle gap: fix late entries or counter-swings inside the single always-positioned target, for
  example by timing flips, rather than by carving out a flat-capable sub-book.

Limitations: these are in-sample public tapes. Only one trailing setting (1 tick arm, 1 tick retrace, measured on mid)
was tested, FAST flips were ungated, and only F 40–60 was tried. The mechanism stays in the file behind `SLEEVES`
(default off).

Reproduce (from MAIN; W = the sleeves worktree, E = `$W/experiments/round_3/dataathletechamp/20261108-r3-w9-sleeves-001`):

```bash
env -u VIRTUAL_ENV uv run --locked python experiments/round_3/dataathletechamp/20261108-r3-wave-runner-001/runner.py \
  --strategy $W/strategies/round_3/dataathletechamp/r3_follower_sleeves.py --grid $E/grid.json --tapes r3,r2 --out $E/out --workers 2
env -u VIRTUAL_ENV uv run --locked python -m simulator.main --backtest data/round3/round3_public.csv \
  --strategy $W/strategies/round_3/dataathletechamp/r3_follower_sleeves.py --log-dir $E/cli_r3 --no-logs
env -u VIRTUAL_ENV uv run --locked python -m tools.preflight $W/strategies/round_3/dataathletechamp/r3_follower_sleeves.py
```

The diagnostics used `grid_diag_a.json`→`out_diag_a` and `grid_diag_b.json`→`out_diag_b`, one worker each.
