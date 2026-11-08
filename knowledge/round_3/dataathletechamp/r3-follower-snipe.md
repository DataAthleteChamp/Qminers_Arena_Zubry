# R3 follower + E2 stale-side snipe (single ledger) — negative, flag kept off

Experiment `20261108-r3-w5-snipe-001` (branch `r3-da-snipe`, base commit cec5525). Strategy
`strategies/round_3/dataathletechamp/r3_follower_snipe.py` = U4 `r3_alpha_follower_p1_sw3.py`
(sha256 e4dfd2ce…574f) + off-by-default `SNIPE_*` flags (final file sha256 b43aa1df0ee7…a751a9b665).
`SNIPE_ON = False` reproduces U4 exactly
(R3 330,208 / R2 109,317, verified in the runner).

## Question

E2 (research wave 1: one side jumps >= k ticks in one update, IOC the unchanged opposite side;
k=2 +1.07/+0.81 ticks/lot, k=3 +1.77/+1.66, ~0.47 events/s) made ~180k alone but overlapped E1.
Does it add PnL when routed through the incumbent follower's single ±100 ledger?

## Mechanism (as implemented)

- Event: market-only best bid rises >= `SNIPE_K` with the market best ask unchanged (or mirror), and no
  A trade trigger in the same update (A takes precedence).
- `SNIPE_MODE "a"` (as-A-event): same side extends the deadline to >= `SNIPE_HOLD_S`; flat enters
  ±100; opposite flips only through the P1 alpha gate (alpha·side > FLIP_MARGIN 1.0).
- `SNIPE_MODE "alpha"`: same side ignored; flat/opposite act only if alpha·side > `SNIPE_ALPHA_MARGIN` (0).
- Entry IOC at the stale touch (D1 `ioc_in`, ENTRY_CAP 0) or D1 flip IOC (touch ±3). `SNIPE_CHASE False`:
  after the snipe IOC completes the target is clamped to the filled position (no chase past the stale level).
  Exit = D1 exit (join touch 1 s, then IOC ±3). Any A signal takes the position over (same-side A tops up
  to ±100 with the 5 s hold). Exposure incl. pending never exceeds 100; penalty 0 in every run.
- `SNIPE_UNGATED` (post-hoc, see below): while the position is snipe-owned an opposite A flips without the gate.

## Setup

Official `ExchangeSimulator` in-process via `20261108-r3-wave-runner-001/runner.py` (5 ms, depth 20, ±100,
10,000/s), 2 workers. Tapes: R3 public (sha256 1021586b92a3d9df…, 6000 s, fit t < 2400 s / eval t >= 2400 s),
R2 public (88ff641e962540c6…). Simulator `simulator/simulator.py` c37b2262186f977d…. Main commit 9ed70a4.
Predeclared accept rule: R3 > 330,208 AND R3 eval/s >= 56.3 AND R2 >= 87,454 (0.8 × base) AND the
neighbouring setting keeps >= 0.9 of the R3 gain.

## Results (all penalty 0)

| variant | R3 PnL | ΔR3 | R3 fit/s | R3 eval/s | R2 PnL | R2/base | snipes acted R3 (same-side / gated) | rule |
|---|---:|---:|---:|---:|---:|---:|---|---|
| base (off) | 330,208 | 0 | 51.6 | 57.3 | 109,317 | 1.00 | – | – |
| k2 a h1 | 345,649 | +15,441 | 52.4 | 61.1 | 73,035 | 0.67 | 251 of 2,826 (2,168 / 407) | fail R2 |
| k3 a h1 | 332,137 | +1,929 | 50.8 | 58.4 | 76,125 | 0.70 | 46 of 810 (697 / 67) | fail R2 |
| k2 alpha h1 | 335,970 | +5,762 | 45.2 | 63.2 | 93,145 | 0.85 | 423 of 2,835 (2,191 / 221) | fail neighbour (k3 −784) |
| k3 alpha h1 | 329,424 | −784 | 49.7 | 58.4 | 99,238 | 0.91 | 62 of 813 (697 / 54) | fail R3 |
| k2 alpha h2 | 341,362 | +11,154 | 46.4 | 63.9 | 92,616 | 0.85 | 403 of 2,843 (2,211 / 229) | fail neighbour (h1 0.52, k3 <0) |
| k2 a h2 | 349,703 | +19,495 | 53.4 | 61.6 | 73,271 | 0.67 | 228 of 2,827 (2,177 / 422) | fail R2 |
| *post-hoc* k2 a h1 ungated | 353,352 | +23,144 | 54.9 | 61.6 | 90,111 | 0.82 | – | not predeclared; neighbour k3 collapses |
| *post-hoc* k3 a h1 ungated | 330,420 | +212 | 51.2 | 57.6 | 91,517 | 0.84 | – | keeps 0.01 of the k2 gain |

## Verdict

REJECT under the predeclared rule; `SNIPE_ON` stays False (the committed default equals U4 behaviour).

- ~75% of snipe events arrive while the follower already holds the jump side, so the follower already owns
  most of the E2 direction (same overlap as the E1+E2 harness: +6k..+19k).
- "a" mode: R3 +2k..+19k but R2 −33k..−36k for both k=2 and k=3. The R2 loss sits in two 600 s blocks
  (block 7 46.8k → 22–34k, block 10 32.7k → 10–15k): path effects, not the snipe trades themselves.
  Likely cause: a snipe position turns the next opposite A from an ungated entry into a P1-gated flip, so
  the follower misses the move.
- "alpha" mode passes R2 (0.85) and eval/s, but the gain moves only into the eval window (fit/s drops
  51.6 → 45–46), k=3 collapses to −784 and hold 1 s keeps only half of the hold-2 s gain: not stable.
- Post-hoc check of the gate hypothesis (`SNIPE_UNGATED`, after seeing grid 1): k=2 R2 recovers
  73,035 → 90,111 and R3 rises to 353,352 (fit/s 54.9), so the gate interaction explains part of the
  "a"-mode R2 loss. It is still below base on R2 (−19k), k=3 keeps none of the gain, and it was chosen after
  the data, so it is only a lead for a fresh predeclared test (e.g. R1 tape / private-like holdout).
- Official CLI, default file (snipe off): R3 public pnl 330,208, penalty 0 (= U4); R0 `sample_v2.csv`
  runs without exceptions (pnl −197,401, penalty 0). `tools.preflight` passed (server sandbox check still needed).
- Public PnL is one path per tape; these deltas are not paired-SE estimates and not a private-round forecast.
- Grid 2/3 runs recorded strategy sha b43aa1df0ee7…: the file gained the off-by-default `SNIPE_UNGATED`
  flag while grid 2 was running; with the flag False behaviour is identical.

## Reproduce

```
cd <MAIN> && env -u VIRTUAL_ENV uv run --locked python \
  experiments/round_3/dataathletechamp/20261108-r3-wave-runner-001/runner.py \
  --strategy <worktree>/strategies/round_3/dataathletechamp/r3_follower_snipe.py \
  --grid <exp>/grid1.json --tapes r3,r2 --out <exp>/grid1 --workers 2
```
Grids `grid1.json` (base + 2×2 at hold 1 s), `grid2.json` (hold 2 s for k=2), `grid3_posthoc.json`
(ungated) and raw `results.jsonl` stay in the experiment folder (uncommitted).
