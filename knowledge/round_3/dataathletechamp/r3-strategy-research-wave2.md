# Round 3 strategy research, wave 2: calibration, fair value and passive gating

Question: why are we far below the field, and which passive and directional
mechanisms could close the gap on B/C-like tapes? Data and engine as in
`r3-market-diagnosis.md`; fit t < 2400 s, evaluation t >= 2400 s; R2 A and R1
used as regime stress. Screens are numpy/order-level replays that reproduce
the official engine's null trades; rows marked "official" ran a research
strategy inside the unmodified official simulator with exact accounting.
Raw scripts/results stay in uncommitted `experiments/round_3/dataathletechamp/`.

## 1. Calibration: the field earns mostly passively

Owner-pasted R2 private leaderboard (12,000 s): 1st delfini 1,875,116;
2nd 1,302,831; 5th 1,195,019; 10th 1,017,551; 20th 817,304; 30th 440,618;
Zubry 0.00 at rank 55 (cause of the zero not yet established: our R2 Final's
only supplied server export, 80,993, is timestamped 23:11 before close).
R1: leader 792,696, Zubry 504,903 (rank 14).

Perfect-foresight **taker** ceiling (+/-100, L1 prices 5 ms after decision,
10 ms steps; `oracle_ceiling.py`): R3 A 206/s (2.48M per 12,000 s), R2 A
153/s (1.84M), R1 43/s (0.52M). The R2 leader matched the R2 A taker
ceiling and the R1 leader beat the R1 ceiling by 1.54x, so top scores come
mainly from **passive spread capture with selective fills**, not taking.
Our best taker engines reach ~45/s on R3 A and ~5/s on R2 A.

## 2. Insert-implied fair value (new, strongest cross-round predictor)

FV = (max price of new bid G-inserts + min price of new ask G-inserts in the
last 50 ms)/2 - standing mid. New inserts are visible live as new order ids.
Correlation with the future mid change (fit / eval):

| Tape | 0.1 s | 0.5 s | 1 s |
|---|---:|---:|---:|
| R3 A | +0.331 / +0.265 | +0.314 / +0.275 | +0.286 / +0.234 |
| R2 A | +0.320 / +0.191 | +0.253 / +0.146 | +0.164 / +0.090 (20 ms window) |

Ridge on FV windows (20/50/200 ms), bid/ask placement aggressiveness, taker
flow EMAs, sweep EMAs and queue imbalance (`fair_value_ridge.py`), eval R2:
R3 6.1% / 8.5% / 5.8% at 0.1 / 0.5 / 1 s (eval top/bottom 5%: +2.11/-2.22
ticks at 0.5 s); R2 6.4% / 3.4% / 1.3%; R1 14.8% / 24.5% / 14.7%.
The old past-fit ridge without FV reached 3.5% (R3) and 0.9% (R2) at
0.2/1 s.

Placement is anchored to the **current** book, not to a hidden future price:
the dispersion of at-or-inside-touch insert prices around mid(t+tau) is
smallest at tau = 0 (R3 0.28/0.35 ticks bid/ask; R2 0.30/0.31) and grows for
tau > 0 (`insert_anchor_lag.py`). The information is directional: the mean
bid offset drifts from -0.59 at insert to -1.13 one second later (the mid
rises after aggressive bid inserts), and inside-spread inserts are followed
by +1.29 (bid) / +0.98 (ask) ticks in their direction within 1 s on R3
(R2 +0.37 / +0.79). So the generator's placement aggressiveness, not a
recoverable fair price, carries the lead.

**Passive fills split cleanly by FV known 5 ms before the fill** (all
external touch fills, lot-weighted ticks/lot at 1 s, fit / eval;
`fair_value_maker_screen.py`):

| FV relative to maker side | R3 share | R3 1 s | R3 0.1 s | R2 1 s |
|---|---:|---:|---:|---:|
| opposes (price heading through us) | 21% | -1.67 / -1.75 | -0.21 / -0.31 | -0.95 / -1.02 |
| opposes by >= 1 tick | 5% | -3.53 / -3.44 | | -2.81 / -2.24 |
| neutral | 53% | -0.38 / -0.41 | +0.24 / +0.21 | -0.20 / -0.27 |
| agrees | 26% | -0.13 / -0.20 | +0.30 / +0.32 | +0.03 / -0.12 |

## 3. Queue-behind decides passive fill quality (all rounds)

Simulated 10-lot touch orders (5 ms latency, FIFO, order-level replay;
`20261108-r3-big-queue-walls-001`): fills with >= 300 lots queued behind us
5 ms before the fill earn +0.16..+0.25 (R3), +0.22..+0.29 (R2) and
+0.24..+0.44 (R1) ticks/lot at 1 s; fills with nothing behind lose -2.0,
-1.2 and -0.4. Tape limit orders have scheduled lifetimes (median ~0.3 s,
~99% cancelled), so a long-lived resting order migrates to the front while
new orders join behind it. A pull rule (ahead <= 50 and behind < 300) cut a
plain R3 touch maker from -28.7/-33.2 to -10.3/-12.9 PnL/s without FV gating.

"Big queues every couple of seconds" are real (2,000+ lots every ~1.8 s) but
random ordinary orders with the same ~0.3 s scheduled life; leaning on walls,
wall-pull following and price improvement in front of walls all lose.

## 4. Official-engine taker results (R3 A, 100 lots, penalty 0)

| Configuration | PnL | fit / eval PnL/s | R2 A |
|---|---:|---:|---:|
| E1 informed follow, 5 s hold, touch exit at deadline | ~270k | 39.3 / 48.8 | +5.3 / +3.7 PnL/s |
| E1 2 s hold | 242k | 30.0-33.3 / 42.2-45.1 | -4.9 / -10.3 PnL/s |
| E2 stale-side snipe k=2, 2 s hold, alone | 180k | 30.9 / 33.1 | -24.1 / -15.3 PnL/s |
| E1 (2 s) + E2 + E3 shared +/-100 | 278k | 36.8 / 52.7 | +7.5k total |
| E1 (5 s) + E2 + E3 shared +/-100 | 289k | 43.4 / 51.3 | not run |

E1 sits at +/-100 82-98% of the time, so the inventory cap binds; a round
trip costs ~2.4 ticks/lot against ~1.2 net. Take-profits (-16 to -38 PnL/s),
scale-outs, queue-imbalance exits, passive follow entries, entry price caps
and signal-strength sizing did not help; holding longer did. E2 on R2 A is
unresolved: +57k in the combined-capacity implementation but -24.1/-15.3
PnL/s in the exit-optimisation one (2 s hold), and negative in the
aggressive-taker screen on R2/R1, so treat it as R3-specific. A noisier
signal definition (2+ distinct fill prices) loses -51/-44 PnL/s:
definitions must be exact.

## 5. Literature consensus used for design (sources in experiment notes)

Takers earn the seconds-horizon alpha; passive income needs either short
inventory flips, front-of-queue position or state gating (Baron et al. 2019;
Brogaard et al. 2014; Menkveld 2013; Moallemi-Yuan; Cartea-Donnelly-
Jaimungal 2018; Albers et al. 2025 live BTC experiment: front-of-queue fills
with a large near queue are profitable, back-of-queue fills lose). Prosperity
winners used a robust fair value and take-then-make quoting. Sizing:
fractional Kelly with shrinkage; one change per validation upload; act only
on paired deltas consistent across tape halves.

## 6. Validation-upload protocol (Bailey et al. PBO/DSR, Blum-Hardt ladder)

Log every tried configuration (N). Score configs on 12 x 500 s blocks of the
official 1 s wealth curve; estimate public-to-validation shrinkage
B = 2r/(1+r) from split-half rank correlation r; expected validation PnL
~ (12,000/6,000) x rho x [mean + B (P_i - mean)]. R2's validation/2x-public
ratio of 0.3-0.6 is what selection noise alone predicts. Upload an unchanged
baseline first, then at most five pre-registered finalists; promote a
challenger only if it beats the incumbent by more than one paired SE; never
hill-climb thresholds on validation feedback. Re-upload the exact chosen
bytes last: the final is the latest successful upload, and our R2 private
0.00 must not repeat (verify the dashboard's evaluated final before close).

## 7. Next predeclared experiments (official simulator)

1. Gated maker ladder (running): touch maker -> + FV cancel gate -> +
   queue-behind gate -> + informed-sweep guard -> + passive unwind. Reject a
   step if its paired delta is <= 0 in fit or eval, or any penalty occurs.
2. FV-skewed quoting plus E1 taking on one ledger; E1 only when maker
   inventory agrees.
3. Robustness: no exceptions on empty/one-sided books, all tapes R0-R3, CPU
   per 12,000 s well under 900 s; the R2 zero must not repeat.
