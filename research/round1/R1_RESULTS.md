# Round 1 public-tape results (data/round1.csv, 12 000 s)

Public-tape PnL from the official simulator, one run each. This is NOT private PnL.
All runs: breach_penalty = 0. Each run is under `research/experiments/<id>/`.

## Best result

**`strategies/r0_v2_maker.py` (experiment `r1-maker-baseline`): PnL +27 011.**
It is a passive inventory-limited maker: one LIMIT quote per side near the touch,
quote size 5, position cap 80, inventory skew 0.025 ticks/lot, no imbalance weight.
It was written earlier for `sample_v2.csv`, not fitted to round1.

## All runs

| Experiment | Strategy | Tape | PnL | Verdict |
|---|---|---|---:|---|
| r1-maker-baseline | r0_v2_maker | full | +27 011 | best |
| r1-noguard-full | maker_obi_noguard | full | +21 751 | worse than baseline |
| r1-obi-full | maker_obi (OBI guard 0.65) | full | +18 236 | guard hurts |
| r1-noguard-first3000 | maker_obi_noguard | first 3000 s | +5 170 | |
| r1-obi-first3000 | maker_obi | first 3000 s | +4 244 | |
| r1-real-zubry | zubry (1-lot flow) | full | -23 851 | rejected |
| r1-real-flowv1 | zubry_flow | full | -173 493 | rejected |
| r1-real-flowv2 | zubry_flow_v2 | full | -173 599 | rejected |

Earlier tutorial-tape runs (`r1-flow-taker-001/002`, with `-v2` on sample_v2) are kept:
the flow taker made +22.7k on sample.csv and lost about 137k on sample_v2.csv.

## Findings

- Flow takers pay the spread and lose about 0.39 tick/lot on round1. The F-flow drift of
  sample.csv does not exist here (96 088 F events in 12 000 s, one per ~125 ms).
- Passive making earns on the same tape.
- The OBI_3 side-withdrawal guard reduced PnL on both windows (-3 515 full, -926 first 3000 s).
  The ablation hypothesis "guard adds PnL" is rejected at the tested threshold 0.65.
- maker_obi trails the baseline; which of size, cap and skew explains it is NOT tested.
- first-3000 s prefix is a causal prefix of the tape (book state preserved). Rate about
  1.4 PnL/s early vs about 1.55 later for maker_obi: one split, not six windows.

## Next

Start from r0_v2_maker and change one parameter at a time (size, cap, skew) over
six 2000 s windows.
