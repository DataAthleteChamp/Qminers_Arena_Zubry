# Round 4 retrospective (dataathletechamp)

Round 4 ran 07:00–12:00 CET on 8 Nov 2026 and is weighted ×1.2 on normalized private PnL.

- **Data:** public R4 tape (6,000 s; sha256 61c0b6d1…) plus the validation tape B (12,000 s, server
  only). Both come from the R4 generator.
- **Final (marked in the portal, submission `71380109`):** Paweł's `r3_final.py`. Validation 1,420,312;
  **private 1,250,605** (11.9% below validation). The rank has not been announced yet.
- **Uploads:** the team used 11 of the 15 allowed. Besides the rows below, they were:
  - Maciej's `continuous_book_adaptive.py` (1,250,479) and `..._direct_flip_edge_1_5.py` (1,170,758);
  - Łukasz's `toxflow_v5.py` (1,196,226) and `toxflow_v6.py` (1,268,596);
  - one canceled U6 re-upload.

## Upload log (validation B)

| Upload | File | R4 A | B | Paired vs previous |
|---|---|---:|---:|---|
| U1 | our R3 U7 (`r4_u1_follower_u7_baseline.py`) | 821,692 | 1,326,712 | baseline |
| U2 | + TRIG2 ungated (`r4_u2_trig2_ungated.py`) | 886,626 | 1,343,784 | +17,072 (15/20 blocks) |
| U6 | + jump-onset flip + burst (`r4_u6_jump_k4.py`) | 920,538 | 1,343,238 | −546 |
| U8 | + CUSUM + 500-lot burst (`r4_u8_allin.py`) | 948,126 | 1,318,169 | −25,069 |
| U9 | U6 + burst flip trigger (`r4_u9_u6_burst.py`) | 937,371 | 1,400,890 | +57,652 vs U6 |
| Paweł | U7 + burst flip trigger (`r3_final.py`) | 860,599 | **1,420,312** | +93,600 vs U1 |

The owner reported a validation median of about 3M late in the round. We could not explain it (below).

## What worked

1. **The informed-flow follower:** always ±100, flipping with 200-lot IOCs on sweeps and taker flow,
   with the ridge flip gate. Its earnings concentrate in jump seconds (64% of R4 A PnL) and 2–15 s holds
   (`r4-u2-trade-anatomy.md`).
2. **The JumpBurst flip trigger** (Paweł's file): mid move ≥ 2 ticks within 100 ms at a 1-tick spread
   gives an immediate ungated flip, with a 500 ms cooldown. This was the biggest validated gain of the
   round: +93.6k on U7.
   - We had seen it in R3 ("adds +2k as a trigger" on R3 A) and shelved it.
3. **TRIG2 placement classes:** +17k on B. It is real but small, and it overlaps the burst trigger.

## What failed (details in the linked notes)

- **Burst sizes above 100 lots.**
  - Liquidity-bound: a perfect-timing sniper finds 0.1–0.3M of stale quotes per 6,000 s at big latent
    jumps, gone within about 50 ms.
  - Live detectors misfire, and the penalty accrues on the misfires (`r4-burst-study.md`,
    `r4-jump-burst-probe.md`, `r4-different-families.md` §5).
- **Hidden-IOC and DEEP8 triggers:** real signals, already captured by the follower
  (`r4-hidden-*.md`, `r4-deep8-trigger.md`).
- **Every non-follower family:**
  - oracle imitation ties the follower;
  - skewed market makers lose on every tape;
  - the literature and competition review found nothing better (`r4-different-families.md`).
- **Whipsaw and cost fixes:** minimum hold, spread-wait, post-jump freeze and execution caps all lose
  on R4 (`r4-u2-trade-anatomy.md`, `r4-oracle-gap.md`).
- **Model work:**
  - gate refits including R4 (`r4-alpha-refit.md`);
  - an R4-native TRIG2 table;
  - CUSUM (+11k on A, not validated);
  - the TWAP-bot follow.

## Lessons

1. **Single-public-tape selection deflates about 6× on validation.** TRIG2 +65k became +17k, jump onset
   +34k became 0, and the all-in +27.6k became −25k. Screen on A, then decide on B. Upload probes early;
   the portal's MARK FINAL lets any completed upload become the final.
2. **Triggers that see the same moves do not add up.** The burst trigger added +93.6k to U7 but +57.7k
   to U6, because TRIG2 and the jump flip overlap it. Combining our best pieces lost to a simpler file.
3. **Re-test simple rejected mechanisms on every new configuration.** The best R4 gain was an R3 reject.
   Teammates' files are candidates too: run them through the same paired engine checks early.
4. **The ±100 follower sits near the visible-information ceiling here.** That is why ~3M is puzzling.
   - On R4 A the 107-feature oracle-imitation model converges to the follower's PnL.
   - Perfect-foresight ±100 is ~270/s on A, while the reported B median is ~250/s.
   - After the private board: compare it with validation, and ask the organisers to clarify the
     metric if the gap persists.
   - Never use non-live information (file or introspection access is forbidden).
5. **Process.**
   - Parallel builders with pre-declared acceptance rules and engine parity checks were efficient.
   - Three agents failed on network timeouts at 10:40; relaunch immediately.
   - Keep the last 30 minutes for paired validation decisions, not new mechanisms.

## Next round checklist

- [ ] Upload last round's final and the teammates' best files in the first hour to get B baselines.
- [ ] Screen new mechanisms on A with flags off = base. Promote only with a paired B check.
- [ ] Re-run the trigger-family screen (burst threshold, window, spread) on the new configuration.
- [ ] Compare per-second B curves pairwise. Single totals hide jump-second luck.
