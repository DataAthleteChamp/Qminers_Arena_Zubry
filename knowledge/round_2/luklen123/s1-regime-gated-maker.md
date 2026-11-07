# S1: a regime-gated maker (Round 2)

Question: does gating the zubry_v2 maker by market regime fix its Round 2 loss? The gates tested
are spread = 1, trailing 1 s mid volatility, and pulling the quoted side after a big taker.
The hypotheses come from `round2-public-tape-profile.md`.

- Strategy: `strategies/s1.py`. The final defaults are `REQUIRE_SPREAD=1`, `VOL_WINDOW_S=60`,
  `VOL_MAX=3.0`, `BIG_TAKER=0` (pull disabled), `KEEP_REDUCING_QUOTE=True`,
  `FLATTEN_IN_STRESS=False`, and the same 2-lot / ±20 cap as zubry_v2.
- Experiment: `experiments/round_2/luklen123/20261107-s1-regime-maker-001/`. `run_variants.py`
  overrides constants, runs the official simulator and writes `results_*.csv` and `out_*.log`.
  It is not committed.
- Tapes: R2 public, SHA-256 `88ff641e…cfb9f4`, 6000 s; R1, SHA-256 `362e8208…1735940`, 12000 s.
  The official simulator is unchanged.
- Halves: H1 is PnL(t = end/2) and H2 = final − H1, both from the full run's 1 s `pnl.csv`.
  The book state and inventory carry over, so the tape is not row-sliced.
- Rejection rule, declared before the runs: a variant fails if its R2 PnL does not beat zubry_v2's
  −4032, or if it has any penalty. No run had a penalty.

## Results (PnL)

| Variant | R2 | R2 H1 / H2 | R2 fills | R2 maxDD | R1 |
|---|---|---|---|---|---|
| zubry_v2 (baseline) | −4032 | −749 / −3283 | 15359 | 4563 | 11206 |
| s1 as first specified (pull ≥200 lots for 2 s) | +1 | −53 / +54 | 1559 | 379 | 1243 |
| spread gate only (no vol gate, no pull) | −998 | +407 / −1405 | 12918 | 2047 | — |
| vol gate only (no spread gate, no pull) | +1647 | +672 / +975 | 9567 | 872 | 11206 |
| **spread + vol 3.0, no pull (final default)** | **+1816** | +1116 / +700 | 9111 | 286 | 10339 |
| spread + vol 2.0, no pull | +2173 | +1283 / +890 | 8460 | 172 | 10339 |
| spread + vol 5.0, no pull | +1569 | +1077 / +492 | 10612 | 484 | — |
| spread + vol 3.0, 30 s window, no pull | +2590 | +1495 / +1095 | 10056 | 188 | 10339 |
| spread + vol 3.0, 120 s window, no pull | +1431 | +884 / +547 | 8116 | 274 | — |
| pull ≥200 lots for 0.5 s | +1723 | +1075 / +648 | 5946 | 179 | 6870 |
| pull ≥500 lots for 2 s | +730 | | 4575 | 283 | — |
| pull ≥1000 lots for 2 s | +1561 | | 7573 | 316 | — |
| IOC flatten while stressed | −2359 | | 3481 | 2361 | — |
| no reducing quote while stressed | +943 | | 1240 | 424 | — |

## Findings

- **The vol gate is the main lever.** It turns R2 from −998 (spread gate only) into +1816. On R1
  it never fires (R1 vol60 stays at or below ~1.25), so it costs nothing there. Every
  no-pull setting with vol 2–5 and window 30–120 s scores +1431 to +2590 on R2, with both halves
  positive. That is a flat plateau, not a single spike.
- **The big-taker pull is harmful at 200 lots / 2 s.** Takers of 200 lots or more arrive about
  once per second, so the pull keeps the maker out of the market most of the time: R1 drops
  from 10339 to 1243, and R2 to +1. A shorter or rarer pull hurts less but never beats the
  no-pull default on either tape. The pull stays in the code behind `BIG_TAKER`.
- **The spread gate is roughly neutral.** It costs about 870 on R1. On R2, spread + vol scores
  +1816 against +1647 for vol only, but with a lower `pnl_se` (332 vs 1151) and a lower maxDD
  (286 vs 872). It is kept for risk control.
- **IOC flattening in stress loses.** It crosses the spread exactly when the spread is widest.
- The final default is the centre of the plateau, not the best R2 run (vol 3.0 / 60 s rather
  than the 30 s window's +2590). This limits selection on a single path: 22 variants were run
  on one R2 tape.

## Limitations

- All of this is public-tape, in-sample evidence. The R2 numbers come from one 100-minute path
  with one crash. The ~22 variants make the best row optimistic.
- `pnl_se` is a one-arm figure, not a paired-delta SE. The per-strategy SEs on R2 are 270–1190
  against differences of a few hundred, so the ranking inside the plateau is not significant.
  The big gaps are robust: v2 against the gated maker, and pull against no pull on R1.
- The server sandbox validation and an upload have not been done.
