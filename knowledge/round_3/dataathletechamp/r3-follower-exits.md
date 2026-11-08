# R3 follower exit-side flags on U7 — negative

Experiment `20261108-r3-w8-exits-001` (branch `r3-da-exits`, base a9ec97c). Strategy:
`strategies/round_3/dataathletechamp/r3_follower_u7_exits.py` (sha256 2902ae83…4a15d) = U7
(`r3_follower_u7_flow_deepfv.py`, sha256 d2a0fc9c…) + exit flags, ALL DEFAULT OFF (= U7 exactly).
Data: R3 public sha256 1021586b92a3…, R2 public 88ff641e9625…; official simulator `simulator.py`
c37b2262186f… run in-process by `20261108-r3-wave-runner-001/runner.py` (5 ms, depth 20, ±100).
Tapes are in-sample (U7's alpha gate was fitted on full R3 + R2 public).

## Question and mechanism

The oracle-gap study found that 36% of U7's gap comes from 0.75–0.9 s counter-swings during holds.
Can exits that go flat (target 0 via the normal exit; the next signal re-enters) beat holding?
- `BLOCKED_FLAT`: an opposite signal blocked by the P1 gate makes the strategy go flat.
- `GIVEBACK g`: peak favourable mid move since entry or last extension >= g and retrace >= g → flat.
- `ADVERSE a`: mid moves >= a ticks against the entry mid → flat.
- `OPP_FLOW q`: 200 ms signed taker flow opposes the position by >= q lots with no entry/flip → flat.
- `EXIT_IOC`: these exits use an immediate IOC instead of the 1 s join-touch phase.

Accept rule (predeclared): R3 > 413,588 AND R2 > 167,166, and a neighbour keeps >= 0.5 of the gain.

## Results (official engine, total PnL, penalty 0 everywhere)

| variant | R3 (Δ) | R2 (Δ) | flats R3/R2 |
|---|---|---|---|
| off (= U7) | 413,588 | 167,166 | – |
| BLOCKED_FLAT | 323,047 (−90,541) | 168,076 (+910) | 1128/990 |
| GIVEBACK 2 | 404,033 (−9,555) | 145,532 (−21,634) | 279/270 |
| GIVEBACK 3 | 412,769 (−819) | 170,615 (+3,449) | 74/88 |
| GIVEBACK 4 | 412,922 (−666) | 166,758 (−408) | 20/39 |
| ADVERSE 3 | 418,200 (+4,612) | 149,743 (−17,423) | 55/61 |
| ADVERSE 5 | 416,740 (+3,152) | 154,938 (−12,228) | 27/31 |
| OPP_FLOW 300 | 315,425 (−98,163) | 176,555 (+9,389) | 1734/1639 |
| OPP_FLOW 400 | 333,763 (−79,825) | 167,844 (+678) | 1055/989 |
| OPP_FLOW 500 | 392,251 (−21,337) | 168,319 (+1,153) | – |
| GIVEBACK 3 + EXIT_IOC | 404,033 (−9,555) | 177,565 (+10,399) | – |
| GIVEBACK 3, no extension reset | 394,927 (−18,661) | 152,052 (−15,114) | – |
| ADVERSE 5 + EXIT_IOC | 402,537 (−11,051) | 158,385 (−8,781) | – |

## Verdict

Negative: no flag is strictly better on both tapes, so none is accepted and no combination was run.
What helps one tape hurts the other. Going flat on blocked signals or opposite flow helps R2
slightly but costs R3 21–98k; the gate-blocked signals are mostly noise worth holding through.
The adverse stop helps R3 by 3–5k but costs R2 12–17k. Giveback is neutral to negative on R3.
The committed default keeps all flags off (= U7). Limitations: public tapes only and in-sample;
the official CLI run and the server validation of this file were not done.

Command (from MAIN): `env -u VIRTUAL_ENV uv run --locked python
experiments/round_3/dataathletechamp/20261108-r3-wave-runner-001/runner.py --strategy <snapshot>
--grid grid1.json|grid2.json --tapes r3,r2 --out out1|out2 --workers 3`. Raw results are kept in the
worktree's gitignored experiment folder.
