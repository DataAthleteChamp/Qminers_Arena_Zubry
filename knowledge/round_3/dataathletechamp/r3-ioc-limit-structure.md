# Round 3: market IOC limits carry the information, not their side

Question: where does the large unfilled taker demand on the R3 tapes sit,
and can a resting order of ours be on the profitable side of it?

Data: R3 public A (`data/round3/round3_public.csv`, sha256 1021586b…2d15,
6,000 s) and R2 public A (`data/round2/round2_public.csv`), official-engine
null replays (`20261108-r3-deep-diagnostics-001/<round>/replay.npz`).
Scripts: `experiments/round_3/dataathletechamp/20261108-r3-ioc-limit-structure-001/`
(`marketable_inserts.py`, `ioc_remainder_premium.py`, `ioc_limit_buckets.py`,
`safe_side_maker_bound.py`), each run with
`env -u VIRTUAL_ENV uv run --locked python <script>` from the repository root.
Descriptive tape statistics, not executed strategy PnL; whole-tape, no
fit/eval split.

## Facts

- Tape `Lifespan` G = resting limit insert, F = IOC. On R3 A, 0 of 1,178,322
  G inserts traded on arrival: G inserts never cross, so every G limit price
  is visible in the live snapshot. All taking is by 56,274 IOCs (9.4/s,
  8.97M lots).
- 6,107 IOCs ended with unfilled size: 1.81M lots on R3 (301/s), 1.65M on R2
  (275/s). Selling to buy-IOC remainders (and buying from sell-IOC remainders)
  at the IOC limit would have earned, against the mid 1 s later,
  +0.52 ticks/lot on R3 and +0.53 on R2 (volume-weighted).
- Split by limit relative to the opposite touch (`rel`, ticks; 1 s signed mid
  move, from the mid before the IOC):

| rel (spread) | R3 n | R3 move | R3 premium at limit | R2 n | R2 move |
|---|---:|---:|---:|---:|---:|
| < −1 (1 tick) | 567 | −7.12 | +4.75 | 118 | −4.59 |
| [−1, 0) (1 tick) | 1,653 | −2.66 | +2.19 | 997 | −1.83 |
| [−1, 0) (>= 2) | 814 | −1.49 | +1.20 | 751 | −1.70 |
| [0, 1) (1 tick) | 15,855 | −0.12 | +0.45 | 17,831 | −0.04 |
| [1, 2) (1 tick) | 16,627 | +0.52 | +0.20 | 18,549 | +0.49 |
| [2, 4) (1 tick) | 5,129 | +1.66 | −1.18 | 3,300 | +1.44 |
| >= 4 (1 tick) | 3,873 | +3.72 | +1.31 | 1,857 | +1.93 |

## Interpretation

- The IOC side looks random and the limit carries the forecast. IOCs that
  can't reach the opposite touch never trade or rest, so a live strategy
  can't see them. Yet they predict a move against their own side: 1.5 to
  7 ticks at 1 s, on both tapes.
- IOCs priced exactly at the touch are a third of IOC volume and roughly
  uninformed: no move, and makers earn +0.45 (R3) or +0.23 (R2) ticks per
  lot.
- Sweeps 1–4 ticks deep are the informed, toxic flow. Sweeps 4 or more ticks
  deep overpay: their limits sit above the mid 1 s later.
- Upper bound for a maker at the front of the touch queue that keeps only the
  side the follower's signal (A_SWEEP 3) says is safe: the per-lot means flip
  sign between 0.5, 1 and 5 s on both tapes, because jumps dominate. The
  follower's state does not separate the harmless touch IOCs from the toxic
  sweeps, which is consistent with the earlier small maker results.
- Correction to the fair-value screen: it used only G inserts, so it has no
  IOC leak. Its FV >= 2 events occur mostly at wide spreads just after
  sweeps. The +3.44-tick mid moves are therefore mostly the spread closing;
  executable taker value was about +1.1 ticks/lot.

## Use

- With a spread of 2 ticks or more, a 1-lot probe inside the spread is crossed
  by the hidden IOCs with limits inside the spread. A probe fill whose taker
  then stops should reveal the hidden, opposite-side forecast. The official-engine
  test (`r3-hidden-ioc-probe.md`) rejected this. Live, probe-only fills moved
  with the taker on R3 (+0.5 ticks at 0.5 s) and were flat on R2, and the
  probes cost 24k on R3 by themselves.
- Hidden IOCs are still visible live as callbacks: the engine emits a
  snapshot after every market event, so a non-trading IOC appears as a
  callback with no trades and an unchanged visible book. They warn of
  volatility but not direction (`hidden_event_precursor.py`). With at least
  one hidden IOC in the last 200 ms, P(|Δmid over 1 s| >= 10 ticks) is 10.2%
  vs 2.2% without one (R3), and 9.4% vs 1.6% (R2). E|Δmid over 1 s| is
  4.3–5.4 vs 1.8 ticks.
- Don't add deep or touch passive size on the strength of this table alone:
  the maker bound above is not robust.

## Leaderboard context

A ±100 position that knows the mid path at 1 s steps, trading at the touch,
earns 1.96M on R3 A (326/s, so 3.9M per 12,000 s) and 667k on R2 A
(`one_second_foresight.py`). Every validation upload returns a 1 s wealth
curve; a constant-position upload would reveal the validation tape's 1 s
price path. Validation scores above 1M are therefore attainable without any
edge that transfers to the private tape. This is a possible reading of the
field's validation numbers, not evidence about any team.
