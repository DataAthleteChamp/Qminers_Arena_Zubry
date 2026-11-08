# R3 passive follower — passive execution of the D1 informed-flow target (negative result)

Owner dataathletechamp, branch `r3-da-passive-follower`, 2026-11-08. Experiment
`20261108-r3-w3-passive-follower-001` (raw outputs gitignored in the worktree's
`experiments/round_3/dataathletechamp/`). Status: official-engine public-tape research; **no variant accepted**.
Private B/C performance UNKNOWN.

## Question

D1 (informed-flow follower) has gross mid alpha 795,920 on R3 A but nets 270,229 because 2,151
200-lot IOC flips cost ≈ 1.2 ticks/lot. Can the SAME target path be executed with resting orders
(front-of-queue, earning the half-spread from uninformed takers) and keep most of the alpha?

## Definitions (strategy `strategies/round_3/dataathletechamp/r3_passive_follower.py`)

- Signal A per market taker order (trades grouped by `taker_order_id`, sign from `book_side`):
  4th+ consecutive same-sign market taker order and filled ≥ 100, or |last − first fill| ≥ 2 ticks,
  or filled ≥ 500 (strong = span ≥ 2 or filled ≥ 500). D1 state machine unchanged: target ±100,
  same-sign A extends the 5 s hold, opposite A flips, deadline → 0.
- `EXEC_MODE="ioc"` (default) = D1: IOC entries at the touch, IOC flips at touch ∓ 3, deadline exit
  joins the touch 1 s then IOC. Reproduces the prior runs to the unit (R3 270,229; R2 26,384).
- **X1** passive-first: rest |target − pos| at own touch, keep orders at/inside the touch (re-price
  only when the touch moves away), IOC the remainder after `FALLBACK_MS` (100/300/1000).
- **X2** X1 + standing `MAINT_QTY` (50/100) orders at both touches (aging), shrink via modify,
  pull a side when insert FV opposes it by `FV_CANCEL` (0/0.5/1.0; FV = (max new bid insert +
  min new ask insert within 2 ticks of touch, last 50 ms)/2 − mid, new = market id > max seen).
- **X3** IOC entries, X1 for flips/exits. **X4** IOC only for strong signals, X1 otherwise.
- Added after wave 1 (not predeclared): **delay control** `IOC_DELAY_MS` (D1 with entry/flip IOCs
  deferred 20/50/100 ms) and **X5 cross-and-rest** (entry/flip LIMIT at the opposite touch, the
  remainder rests at the front of the new touch, IOC after `FALLBACK_MS`).
- Worst-case inventory check at every send (resting + in-flight, modifies at old size):
  max exposure incl. pending = 100 and penalty = 0 in all 38 runs; 0 blocked sends.
- Cost = sign·(fill − mid at send) ticks/lot. "passive%" = lots filled by LIMIT orders (for X5 this
  includes the immediately marketable part, so it is not a maker share).

## Provenance

| item | sha256 |
|---|---|
| R3 A `data/round3/round3_public.csv` | `1021586b92a3d9dfdb70096e6b0af34d460813b139f1f51f56b73871cb5a2d15` |
| R2 `data/round2/round2_public.csv` | `88ff641e962540c66fa1cc4a3547585d31838d0929340150690cabb4f3cfb9f4` |
| simulator.py / models.py / strategy.py | `c37b2262…` / `d66d6155…` / `464830f4…` (unchanged) |
| strategy wave 1 snapshot (X1–X4) | `e1b2d599ca347bd07413d584afd7eac56c55e55af55b2afabeeb30f55750bf92` |
| strategy wave 2 snapshot = committed file | `dc22fe1ac6a6d60bc3d7a9d91e934e001348a3d4f3fbbd334a0ef6f55942665e` |
| shared runner | `079727719583626a27aca7666128ef8ee8831806bb202fc010f2eba11b3302a9` |

Engine config: 5 ms accept delay, depth 20, ±100, potential 1000, 10,000/s penalty. Windows: fit
t ≤ 2400 s, eval = rest (≈ 3,600 s on each tape). Commands, wave 1 then wave 2 (MAIN = main checkout, E = experiment dir):
`cd $MAIN && env -u VIRTUAL_ENV uv run --locked python $MAIN/experiments/round_3/dataathletechamp/20261108-r3-wave-runner-001/runner.py --strategy $E/r3_passive_follower_v{1,2}.py --grid $E/grid_wave{1,2}.json --tapes r3,r2 --out $E/wave{1,2} --workers 3`.
Wave-2 D1_base reproduced wave 1 exactly.

## Results (PnL/s fit / eval; Δ paired vs D1_base in the same harness)

| variant | R3 fit | R3 eval | Δ eval | R3 PnL | R3 lots | passive% | cost/lot all (passive / IOC) | R2 fit / eval (Δ eval) |
|---|---|---|---|---|---|---|---|---|
| **D1_base** | 39.4 | 48.8 | 0 | 270,229 | 443,550 | 0.8 | 1.19 (−0.56 / 1.20) | 5.3 / 3.8 |
| X1 fb100 | 19.8 | 11.5 | −37.3 | 88,973 | 439,212 | 7.0 | 0.81 (−0.73 / 0.92) | −8.0 / −22.7 (−26.5) |
| X1 fb300 | 0.4 | −8.7 | −57.6 | −30,418 | 434,330 | 26.0 | 0.53 (−0.68 / 0.96) | −26.9 / −36.3 (−40.1) |
| X1 fb1000 | −1.4 | −18.2 | −67.0 | −68,691 | 437,198 | 74.4 | −0.23 (−0.60 / 0.83) | −3.2 / −12.4 (−16.2) |
| X2 m50 | −97.4 | −118.8 | −167.7 | −661,613 | 1,602,780 | 53.5 | −0.02 (mm −0.86) | −80.4 / −125.7 |
| X2 m100 | −167.2 | −197.6 | −246.4 | −1,112,846 | 2,334,326 | 55.6 | −0.03 | −127.9 / −184.2 |
| X2 m50 FV 0.5 | −49.5 | −62.5 | −111.3 | −343,904 | 992,718 | 48.6 | 0.12 | −49.4 / −82.4 |
| X2 m50 FV 1.0 | −73.8 | −89.2 | −138.1 | −498,454 | 1,429,142 | 52.6 | 0.02 | −69.4 / −109.2 |
| X3 fb100 | 19.9 | 11.7 | −37.1 | 89,948 | 439,012 | 6.7 | 0.81 | −7.9 / −23.4 |
| X3 fb300 | 0.3 | −9.0 | −57.9 | −31,855 | 434,150 | 24.3 | 0.56 | −27.6 / −36.7 |
| X4 fb100 | 32.4 | 40.0 | −8.8 | 221,772 | 443,444 | 1.9 | 1.15 | −2.7 / −6.6 (−10.4) |
| X4 fb300 | 26.6 | 32.9 | −15.9 | 182,142 | 440,170 | 7.5 | 1.09 | −3.9 / −10.5 (−14.3) |
| D1 delay 20 ms | 37.4 | 37.3 | −11.5 | 224,081 | 440,302 | 0.7 | 0.87 (flip 0.88) | 2.3 / −2.1 (−5.9) |
| D1 delay 50 ms | 30.3 | 26.1 | −22.7 | 166,932 | 435,502 | 0.8 | 0.85 | 0.6 / −11.2 (−15.0) |
| D1 delay 100 ms | 18.4 | 8.4 | −40.4 | 74,495 | 428,150 | 0.8 | 0.93 | −11.3 / −30.0 (−33.8) |
| X5 fb100 | 36.8 | 45.9 | −3.0 | 253,438 | 453,888 | (91.4) | 1.05 | 10.4 / 3.0 (−0.8) |
| X5 fb300 | 37.6 | 46.0 | −2.9 | 255,662 | 456,288 | (95.8) | 1.04 | 11.7 / 3.5 (−0.3) |
| X5 fb1000 | 38.4 | 47.8 | −1.1 | 264,000 | 457,470 | (99.5) | 1.03 | 13.8 / 5.5 (+1.7) |

Flips ≈ 2,150–2,220 and time at |I| ≥ 90 ≥ 97% for all X1/X3/X4/X5 runs (X2: 60–78%).

## Findings

1. **Passive execution saves cost but loses more alpha.** X1 fb1000 turns execution from a cost of
   +525k ticks (D1) into a rebate of −101k (passive fills −0.60 ticks/lot vs mid at send), a
   ≈ 626k swing, yet PnL falls by 339k on R3: ≈ 965k of gross alpha is lost to waiting and to
   adverse selection of the fills that do happen. Same sign on R2.
2. **The D1 alpha decays on a tens-of-ms scale.** Merely delaying D1's IOCs by 20/50/100 ms costs
   −11.5/−22.7/−40.4 PnL/s on R3 eval (R2 −5.9/−15.0/−33.8), even though the delayed flips are
   cheaper (0.88 vs 1.20 ticks/lot: the book refills after the triggering sweep). X1 fb100 (93% of
   lots still IOC'd, after 100 ms) loses the same as the 100 ms delay: the loss is the wait, not the
   passive fills. Any execution that does not trade within ~5–20 ms of the signal gives up alpha
   worth more than the whole spread.
3. **Standing two-sided orders (X2) are picked off by the same informed flow D1 follows**: mm fills
   look cheap at send (−0.8 ticks) but turnover ×3.5 and −100 to −200 PnL/s. The insert-FV pull
   halves the damage at 0.5 ticks but remains far negative.
4. **X5 cross-and-rest is near-neutral** (R3 −1.0…−3.0 eval, R2 −0.8…+1.7 eval, fit +5…+8.5):
   avoiding the 3-tick walk does not pay because the unfilled remainder misses the alpha. Not
   accepted (rule: R3 eval must improve); recorded as a possible transfer-neutral variant only.

## Verdict

Hypothesis rejected on R3 A and R2: no passive variant (X1–X4, X5) improves R3 eval vs D1 in the
same harness; the best is X5 fb1000 at −1.1 PnL/s. The ~1.5M/12,000 s reported for top teams cannot
come from executing this follower's target passively; the follower's edge is its immediacy. Cost
reduction must come from *which* flips are taken (flip gating, see cost-aware notes) or from
signals with slower alpha, not from resting orders. No R1/CLI/server step was required (no variant
beat D1 by > 10 PnL/s); the committed file defaults to D1, passed the local preflight, and the
official CLI on R3 A (`exchange-simulator ... --no-logs`, 13 s) reproduces PnL 270,229, penalty 0.
Server sandbox validation not done.

## Limitations

- Public A and R2 only, one chronological split each; single paired runs, no SE. Waves 1+2 = 19
  variants (D1_base twice); delay control and X5 were added after seeing wave 1 (selection step).
- Non-reactive tape: our resting orders do not change other participants' behaviour; queue
  position follows the engine's FIFO with our order joining the back at accept time.
- X2 FV uses "id > max id seen within 2 ticks of the touch" (cheap proxy for "id not in previous
  snapshot"); no other FV definitions or windows were tried.
- No tick-improving (inside-spread) or size-dependent passive variants were tested.
