# R3 follower + wall-mid latent estimate (`20261108-r3-w7-wallmid-001`): negative, flag off

**Verdict: reject.** `WALL = "off"` stays the default. With the flag off, the file
behaves exactly like U4 (`r3_alpha_follower_p1_sw3.py`, R3 330,208). No wall-mid variant meets the predeclared
acceptance rule. All numbers come from local public-tape runs. Public PnL is not private PnL.

## Question and mechanism

The "Wall Mid" idea comes from the IMC Prosperity 3 runner-up. Stale orders and sweeps distort the touch. Resting
orders deeper in the book were placed recently around the hidden latent price, so a deep-book fair value might
estimate the latent price better than the mid. The oracle-gap study (`20261108-r3-w6-oracle-gap-001`) found that
inserts within ±20 ticks carry information: IC at 0.5 s is 0.227 in R3 and 0.145 in R2. Inserts within ±2.5 ticks
carry none. It also found that 57% of the gap to perfect foresight comes from entering about 0.3 s late.

Implementation (`strategies/round_3/dataathletechamp/r3_follower_wallmid.py`): this is U4 plus the `WALL` flag.

- `L_hat = (W_bid + W_ask) / 2`.
- `W_side` is the quantity-weighted mean price of MARKET resting orders at price levels 2..`WALL_K` (the best market
  level is excluded).
- Optional `WALL_AGE_MS`: keep only orders younger than this age. Age comes from the monotone market order id: the
  strategy keeps a deque of (first time a new maximum id was seen, id), and ids at or below the id seen at t − age
  count as old. This is O(1) amortised.
- Cost is one pass over at most `WALL_K` market price levels per side on each book event. Runtime is about 55–70 s
  on R3, against 33 s for U4.
- `trigger` mode: `ask < L_hat − θ` is treated as a long A event and `bid > L_hat + θ` as a short A event. It only
  applies when no taker A fired in the same event, and it uses the existing D1 enter/extend/flip logic, so flips
  still pass the P1 gate.
- `veto` mode: a flip to sign s is blocked when `(L_hat − mid)·s < −θ`.

## Setup

Data and code:
- R3 tape `data/round3/round3_public.csv` (sha256 `1021586b…`).
- R2 tape `round2_public.csv` (`88ff641e…`).
- R1 tape `round1.csv` (`362e8208…`).
- Simulator `simulator/simulator.py` `c37b2262…`.
- Strategy sha256 `976884ba…`.

Engine and windows:
- The official engine runs in process through `20261108-r3-wave-runner-001/runner.py`.
- Engine settings: ±100, potential 1,000, 5 ms accept delay, depth 20, penalty 10,000/s.
- Fit window: t < 2,400 s. Eval window: t ≥ 2,400 s.
- No parameters were fitted. θ, K and the age limit come from a predeclared grid.

Command (from MAIN):

`env -u VIRTUAL_ENV uv run --locked python experiments/round_3/dataathletechamp/20261108-r3-wave-runner-001/runner.py --strategy <wt>/strategies/round_3/dataathletechamp/r3_follower_wallmid.py --grid <exp>/grid1.json --tapes r3 --out <exp>/wave1-r3 --workers 2`

The grids and the `results.jsonl` files are in the worktree experiment folder (not committed).

Predeclared acceptance rule:
- R3 total > 330,208;
- R3 eval ≥ 56.3/s;
- R2 ≥ 87,000;
- the neighbouring θ keeps ≥ 0.5 of the gain.

## Results (R3 public; Δ against U4 330,208)

In variant names, `t` = trigger and `v` = veto, `k` = WALL_K, `a` = age limit in ms (0 = none), `th` = θ.

| variant | R3 PnL | Δ | fit/s | eval/s | wall signals (events) | entries/flips/ignored |
|---|---:|---:|---:|---:|---:|---|
| U4 (WALL off) | 330,208 | 0 | 51.6 | 57.3 | 0 | 140/1380/707 |
| t k10 a0 θ1.5 | 321,148 | −9,060 | 52.1 | 54.5 | 23,972 | 134/1399/21341 |
| t k10 a0 θ2.5 | 329,918 | −290 | 51.8 | 57.1 | 5,339 | 136/1383/5621 |
| t k10 a0 θ4 | 331,871 | +1,663 | 51.5 | 57.8 | 854 | 138/1380/1465 |
| t k10 a300 θ1.5 | 292,001 | −38,207 | 50.9 | 47.2 | 53,970 | 91/1473/17356 |
| t k10 a300 θ2.5 | 330,971 | +763 | 51.1 | 57.8 | 1,573 | 138/1380/1710 |
| **t k10 a300 θ4** (best) | **331,999** | **+1,791** | 51.6 | 57.8 | 192 | 139/1379/856 |
| t k5 a0 θ1.5 / θ2.5 / θ4 | 326,570 / 330,971 / 330,871 | −3,638 / +763 / +663 | | 56.7 / 57.8 / 57.8 | 3,845 / 796 / 243 | |
| t k5 a300 θ1.5 / θ2.5 / θ4 | 326,670 / 330,971 / 331,999 | −3,538 / +763 / +1,791 | | 56.7 / 57.8 / 57.8 | 2,707 / 482 / 91 | |
| v k10 a0 θ1.5 | 326,589 | −3,619 | 52.9 | 55.5 | 29 vetoes | 143/1359/705 |
| v k10 a0 θ2.5 / θ4 | 330,208 / 330,208 | 0 / 0 | | 57.3 | 0 vetoes | identical to U4 |

R2 public (U4 109,317):
- t k10 a300 θ4: 103,988 (−5,329);
- t k10 a0 θ4: 103,867 (−5,450);
- t k10 a300 θ2.5: 103,459 (−5,858).

R1 (information only): t k10 a300 θ4 scores −112,045, the same as U4 with WALL off (−112,045, paired run). The
flag has no effect on R1.

Official CLI on R3 with the default (`WALL = "off"`): pnl **330,208**, penalty 0, fills 1,666, 301,670 lots.
`tools.preflight` passes.

## Reading

- Against the rule: the best variant (k10 a300 θ4) passes R3 total and eval/s and has R2 ≥ 87k. It fails the
  neighbour test: θ2.5 keeps 763/1,791 = 0.43 of the gain, and θ1.5 loses 38k. It is also −5.3k on R2. The R3
  "gain" comes from about 1–2 episodes (192 event-level signals, one fewer entry and one fewer flip). That is noise,
  not a mechanism.
- Levels 2..K rarely place `L_hat` more than 2.5 ticks from the touch, and when they do, the sign mostly opposes the
  position the follower already holds. The P1 gate blocks most of these signals: "ignored" rises from 707 to
  1.5k–21k. The ones that pass the gate (θ1.5: +19…+93 flips) lose money. In veto mode, θ ≥ 2.5 never fires; θ1.5 vetoes 29 flips, and blocking them costs 3.6k.
- A static depth-weighted book centre is not the insert-flow FV the oracle study measured. The study's signal was
  the mean price of new inserts in the last 200 ms (`grel200`) combined with taker flow (`sv200`). The resting-depth
  centre is dominated by old queue mass and depth asymmetry, which behaves like the imbalance features the study
  already found negative. The 300 ms age filter does not change this.

## Limitations and retention

- One public tape per round. No paired-delta SE. θ was not tuned beyond the predeclared grid.
- Server validation is still needed for any file that is uploaded. This one should not be uploaded instead of U4.
- The mechanism stays in the file behind `WALL` (default off) for reuse. Do not adopt it.
