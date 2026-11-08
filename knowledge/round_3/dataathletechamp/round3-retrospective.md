# Round 3 retrospective

## Outcome

| | Value |
|---|---|
| Final submission (marked in the portal) | Paweł's upload `db1805cd` (05:23); validation B 597,854 |
| **Private C (12,000 s, final leaderboard)** | **+589,202, rank 34 of 53** (the score of `db1805cd`) |
| Our best own upload | U7, `strategies/round_3/dataathletechamp/r3_follower_u7_flow_deepfv.py` (sha256 d2a0fc9c…f897) |
| U7 on public R3 A (6,000 s, local official engine) | 413,588, penalty 0 |
| U7 on validation B (12,000 s, server) | 538,844 |

**Correction (2026-11-08, from the portal dashboard):** earlier versions of this note named U7 as the
final. The team's marked Final was Paweł's upload, and its R3 bytes are not archived here. It is most
likely the `r3_final.py` he re-uploaded in Round 4: U7 plus the JumpBurst flip trigger, which scores
419,806 on R3 A.

The final leaderboard was each team's last submission, evaluated on the private tape:

| Rank | PnL |
|---:|---:|
| 1 | 1,458,005 |
| 2 | 1,240,532 |
| 3 | 1,198,048 |
| 10 | 929,224 |
| 20 | 816,404 |
| 27 (median) | 724,745 |
| **34 (Zubry)** | **589,202** |
| 53 | −2,192 |

## Timeline of uploads (validation tape B)

| Upload | File | R3 A | R2 A | B | Change |
|---|---|---:|---:|---:|---|
| U1 | `r3_informed_follower.py` | 270,035 | 26,175 | 272,176 | informed-flow follower (D1) |
| U2 | R1 Final maker (probe) | −422,816 | – | −659,826 | B is toxic for passive quoting |
| U3 | `r3_combined_regime.py` | 269,288 | 63,328 | 258,688 | regime gate + maker; the gate switched off profitable stretches |
| U4 | `r3_alpha_follower_p1_sw3.py` | 330,208 | 109,317 | 411,302 | ridge flip gate (P1) + 3-tick sweep trigger |
| U6 | `r3_alpha_follower_p1_sw3_rlin0.py` | 357,488 | 107,856 | 415,828 | gate refit on full R3 + R2, intercept 0 |
| **U7** | `r3_follower_u7_flow_deepfv.py` | **413,588** | **167,166** | **538,844** | + taker-flow trigger + deep-insert fair-value trigger |
| U8 (not final) | `r3_follower_u8.py` | 415,883 | 171,568 | – | TRIG1 flow 200, hold 6 s, flow hold 8 s (+1.2% over 7 tapes) |

Teammates' uploads on B were Maciej's 154,162 (04:06) and Paweł's 597,854 (05:23, **marked Final**)
and 596,419 (05:46).

Most of the progress came late, between 03:00 and 04:20 (U4 → U7), after the oracle-gap and IOC-structure research. From 01:00 to 03:00 the effort went into broad literature and research waves and into maker and regime experiments that did not survive B.

## What made money

All of it is taker execution of informed order flow, about ±100 lots almost all the time:

1. **Signal A per market taker.** Fill span >= 3 ticks, or filled >= 500 lots, or a same-side run >= 4 with filled >= 100. It sets the target to ±100 through an IOC; same-sign signals extend a 5–6 s hold.
2. **Flip gate.** A 2 s-horizon ridge forecast on 25 O(1) features blocks flips the forecast does not support by more than 1 tick. Refitting it on pooled R3 + R2 with intercept 0 (no drift bias) improved B.
3. **Earlier entry.** Two extra A-like triggers:
   - |signed taker volume over 200 ms| >= 600;
   - TRIG1: taker flow >= 300 (later 200) **and** the 200 ms mean of (new resting insert price − prior mid) over all visible depth >= 0.5 tick.

   These lifted B by 30% (ordinary-second rate 42.4 → 50.9 per s) and beat the previous version on all 5 synthetic tapes.

## What the market looked like

From `r3-market-diagnosis.md`, `r3-ioc-limit-structure.md`, `r3-oracle-gap.md`
and the teammate profile (`experiments/round_3/dataathletechamp/20261108-r3-teammate-inputs/round3-public-tape-analysis.md`, luklen123):

**Order generator**
- The generator family is the same as R1/R2. Resting (G) inserts never cross and have scheduled lifetimes (median about 0.3 s).
- All taking is by IOCs, about 9 per second. Their limit carries the forecast; non-marketable IOCs are invisible to a live strategy.
- The informative new resting orders sit **deep** in the book. Within ±2.5 ticks of mid the correlation with the next 0.5 s move is about 0; across all visible depth it is 0.23.

**Price process**
- Momentum at 1–5 s, reversion at 10 s – 5 min (VR 0.86 at 60 s). R2 was the opposite.
- Jumps are heavy-tailed: kurtosis about 210 on A and much larger on B.

**Maker economics**
- Touch makers lose: −0.62 ticks/lot at 1 s, −1.1 at 2 s.
- Only fills against small aggressors are safe.

**Gap to perfect foresight** (±100, 10 ms, touch crossing: 206/s on A)
- 57% is late entry: we switch about 0.3 s after the oracle.
- 36% is counter-swings during holds.
- Our execution costs about 0.98 ticks/lot versus the oracle's 0.60.

## What failed

Every mechanism is kept behind an off-by-default flag; details are in the linked notes.

| Mechanism | Result | Note |
|---|---|---|
| FV-gated, aged and regime makers; heavy R1 maker | small on A, toxic on B | `r3-aged-maker.md`, `r3-combined-candidate.md` |
| Positions above ±100 (bursts, 300–1,000 lots) | penalty plus crossing costs; any gain came from a few outliers | `r3-strategy-research-wave2.md`, `r3-naive-families.md` |
| Stale-side snipe | overlaps the follower; R2 −33k | `r3-follower-snipe.md` |
| Passive execution of the follower target | the edge decays within about 20 ms; standing orders lose | `r3-passive-follower.md` |
| Hidden-IOC probes inside wide spreads | probes cost 24k; signal sign did not hold live | `r3-hidden-ioc-probe.md` |
| Wall-mid deep-book fair value | noise | `r3-follower-wallmid.md` |
| Jump guard (thin exit depth) | hedge only, −1.3k / −1.4k | `r3-follower-jump-guard.md` |
| Exits: blocked-flat, giveback, stops, opposite-flow flat | one tape up, the other down | `r3-follower-exits.md` |
| Reversion overlay / reversion sleeve | each lot moved costs about 5× its reversion edge | `r3-u7-trigger-stack.md`, `r3-follower-revsleeve.md` |
| Two-horizon sleeves, evidence-weighted sizing | −33% to −97% | `r3-follower-sleeves.md`, `r3-follower-evidence.md` |
| Alpha forecast as a trigger; alpha v2 with trigger features; consensus gate bypass | worse | `r3-alpha-model.md`, `r3-u7-trigger-stack.md` |
| Colleague JumpBurst (flat, 1 s bursts) | 78k A / 154k B alone; adds +2k as a trigger | `r3-u7-trigger-stack.md` |

## Mistakes and lessons

1. **We assumed the field was inflated.** We guessed that validation scores above 1M came from fitting B's per-second wealth curve. The private board disproved it: 33 teams beat us on an unseen tape, the top one at 1.46M. Treat competitors' scores as real evidence of an edge we lack.
2. **Mechanism discovery came too late.** The oracle-gap study (where perfect foresight beats us) and the IOC-limit structure were the most productive analyses, and both ran after 03:30. Run them in the first hour.
3. **Live features didn't match the research definition.** The live fair value used `FV_DEPTH = 2` (near-touch inserts only), while the screen used all visible depth. That hid the strongest live signal for hours. Every live feature needs a parity test against its research definition.
4. **Check agent explanations against data.** An agent explained the weak live fair value by "marketable inserts". The tape shows 0 of 1,178,322 G inserts cross. Check every mechanistic claim against the tape before acting on it.
5. **B is the only same-generator out-of-sample test, so use it early and often.** Uploads that don't beat the best don't lower it. Each B result was decomposed:
   - ordinary seconds vs |ΔPnL| >= 3,000 jump seconds;
   - 600 s blocks against the previous upload;
   - `validation_pnl_stats.py` and `validation_jump_seconds.py` in `20261108-r3-ioc-limit-structure-001/`.

   This variance-reduced view correctly ranked U4 < U6 < U7 when the totals were close.
6. **Parallel worktrees plus one shared runner scaled well.** Predeclared acceptance rules kept selection honest, and negative results were recorded. But many agent-hours went to parameter neighbourhoods worth about 1%. Spend agents on new information sources and execution timing instead.
7. **Use synthetic tapes for paired checks.** The calibrated generator (`20261108-r3-generator-monte-carlo-001`) gives paired comparisons across realizations. Its absolute PnL levels are not credible.

## Where the remaining edge probably is

Teams at 0.8–1.46M on the private tape earned 1.4–2.5× our private rate. From our own gap analysis, the candidates are:

- earlier entry: we act about 0.3 s after perfect foresight;
- better flip timing during counter-swings;
- lower crossing cost on flips, which are made right after sweeps when the spread averages 1.58 ticks.

All three are untested ideas, not results.
