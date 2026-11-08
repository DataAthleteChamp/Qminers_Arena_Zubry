# Round 4: U2 trade anatomy — where it earns, bleeds and misses

Source: `experiments/round_4/dataathletechamp/20261108-r4-burst-predictor-001/`
(`record_trades.py`, `trade_chart.py`, `trade_chart.txt`; interactive chart `u2_r4_trades_chart.html`).
Exact official-engine fills and follower signals of U2 (`r4_u2_trig2_ungated.py`). The recorder reproduces
the engine PnL exactly: R4 886,626, R3 415,404, R2 159,515.

## PnL decomposition

PnL = gross mid PnL (position × mid change) − execution cost (fill vs mid at fill).

| tape | gross mid PnL | execution cost | net | lots | cost per lot |
|---|---:|---:|---:|---:|---:|
| R4 | 1,265,370 | 378,586 (30% of gross) | 886,626 | 381,900 | 0.99 |
| R3 | 811,636 | 396,182 (49%) | 415,404 | 391,500 | 1.01 |
| R2 | 542,100 | 382,535 (71%) | 159,515 | 387,700 | 0.99 |

- **Cost per lot by spread at fill (R4):**

  | spread at fill | cost per lot | share of lots |
  |---:|---:|---:|
  | 1 | 0.68 | 58% |
  | 2 | 1.11 | 26% |
  | 3 | 1.63 | 11% |
  | ≥ 4 | 2.65 | 5% |

  Almost all of this is the spread itself; walking the book adds about 0.18 at spread 1. The execution-cap
  grid showed no lever there (`r4-oracle-gap.md`).
- **Where it comes from:** nearly all volume is 200-lot IOC flips, about 1,900 per tape. Each flip costs
  about 200.

## Holding episodes (R4)

1,910 episodes of one position sign, median 2.2 s, 54% winners.

| trigger | episodes | net | net per episode | win rate |
|---|---:|---:|---:|---:|
| A sweep | 1,298 | 515,830 | 397 | 53% |
| FLOW | 193 | 36,454 | 189 | 46% |
| TRIG1 | 342 | 239,872 | 701 | 60% |
| TRIG2 | 75 | 166,424 | 2,219 | 76% |

- **TRIG2 off R4:** on R3 its episodes net +32,776 (400 per episode), and on R2 they net −7,685.
- **By duration:** episodes under 1 s are whipsaws.

  | tape | episodes < 1 s | net |
  |---|---:|---:|
  | R4 | 403 | −43,610 |
  | R3 | 434 | −55,274 |
  | R2 | 421 | −72,799 |

  Episodes of 2–15 s carry the profit: +924k on R4.
- **Flip timing:** after an executed flip the mid moves +0.97 / +2.10 / +2.68 / +3.33 ticks at
  0.2 / 1 / 2 / 5 s in the flip's direction. In the second before the flip it moved −0.76.
- **Gate-blocked opposite signals** (1,133 on R4) move only +0.92 ticks at 1 s in the blocked direction.
  That is below the cost of a 200-lot flip, so the gate is roughly neutral.

## Jump seconds carry the round

| tape | jump seconds (\|mid change\| ≥ 10 in the second) | PnL in them | share positive | ordinary seconds |
|---|---:|---:|---:|---:|
| R4 | 421 | **+566,718** | 94% | +319,908 (57/s) |
| R3 | 176 | +210,487 | 95% | +204,917 |
| R2 | 110 | +96,779 | 79% | +62,736 |

- **R4's worst seconds** are big latent jumps taken on the wrong side:
  - 2,170 s: −7,483 (mid +75.5);
  - 5,632 s: −5,800 (+59);
  - 814 s: −4,382 (−44);
  - 2,540 s: −3,204 (+33);
  - 2,689 s: −2,187 (+26);
  - 5,801 s: −1,957 (+21.5).
- The onsets at 2,170 s, 2,540 s, 2,689 s and 5,801 s are exactly the events that the clustered
  order-id-gap jump-onset detector called in the right direction (`jump_onset.py`, `jump_episodes.py`).

## Can the whipsaws be filtered at flip time? No (`whipsaw.py`, `whipsaw.txt`)

- **Method.** Skipping a flip into episode E means holding the old side through E and not flipping
  back. The value of skipping is −2 × gross(E) + cost(E) + cost(next flip), computed from exact fills.
- **Every bucket says flipping was right, on every tape.**

  | flips filtered | skip value R4 / R3 / R2 |
  |---|---|
  | < 600 ms after the previous flip | −213k / −97k / −70k |
  | ≥ 6 flips in the last 10 s | −284k / −188k / −110k |
  | spread ≥ 3 at the signal | −848k / −386k / −120k |
  | FLOW trigger within 2 s of the previous flip | −25k / −43k / −21k |
  | every flip | −1.92M / −0.98M / −0.44M |

  The only positive cells have n ≤ 60 and occur on R2 alone.
- **Why it fails.** Whipsaws are the unavoidable cost of reacting fast. Wide-spread flips are the most
  valuable ones, because they happen inside jumps.
- **The rejected alternatives:** partial flips (to flat), stricter gates and cheaper execution.
  - The gate-blocked signals move only about 1 tick in the blocked direction.
  - The execution caps had no effect.
  - None of these has a positive offline case.

## Reading

- **No hidden bleed in the logic.** U2 earns where it should: it is on the right side of 81% of R4's jump
  seconds.
- **The two systematic drains:**
  - the spread paid on about 1,900 flips (30–70% of gross);
  - whipsaw episodes under 1 s (−44k to −73k per tape).
- **The missed money** sits in big latent jumps. U2 is wrong-footed in a few of them, and it never holds
  more than ±100 in any of them. That is the jump-onset work (`r4-jump-onset.md`, on branch
  `r4-da-jump`).
