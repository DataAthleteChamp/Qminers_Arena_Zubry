# R3: aged-queue maker overlay on the U4 follower (negative, MAKER_MODE stays "off")

Experiment `20261108-r3-w5-aged-overlay-001` (raw outputs uncommitted in the experiment folder).
Strategy `strategies/round_3/dataathletechamp/r3_follower_p1_aged.py`
(sha256 5a5ceffade03c56b10c113959730d97a88115581cd96f180f57dc1fc6c09a2a4), copy of U4
`r3_alpha_follower_p1_sw3.py` (sha256 e4dfd2ce…574f) plus a flag `MAKER_MODE` (default `"off"`).

## Question and mechanism

Can the aged-queue maker of `r3_aged_maker.py` / `r3_combined_regime_aged.py` (KEEP_AGED, MAX_DIST 2,
FV_STRONG 1.5, cooldown 100 ms, age 150 ms, FV gate 0.5 on the 50 ms new-insert FV, MAKER_CAP 80)
add PnL on top of U4 when both engines share ONE inventory ledger (all pending orders of both
count; hard cap +-100; follower sends are clipped to the room while maker cancels are in flight)?
The follower is "active" from the event its target becomes non-zero until flat with no orders;
it owns (and flattens) the whole inventory. Predeclared modes: `flat` (maker only while the
follower is idle; activation cancels all maker orders), `regime` (flat + only when the A-rate EMA,
tau 120 s, >= 2-tick A definition, is < RATE_HIGH 0.867; follower unchanged), `partial` (flat while
idle; while active the maker keeps/places only the side moving inventory toward the follower target,
capped at the target). MAKER_Q in {10, 20}.

## Data, windows, commands

R3 public (sha256 1021586b92a3d9df…), R2 public (88ff641e962540c6…), official
`simulator.simulator.ExchangeSimulator` (simulator.py c37b2262186f977d…), 5 ms latency, depth 20,
+-100, 10,000/s penalty. fit/s = PnL to t = 2400 s / 2400; eval/s = remainder per second (no fitting
was done here; the maker constants are the donor's). Command (from MAIN):
`env -u VIRTUAL_ENV uv run --locked python experiments/round_3/dataathletechamp/20261108-r3-wave-runner-001/runner.py --strategy <exp>/strategy_snapshot_v1.py --grid <exp>/grid.json --tapes r3,r2 --out <exp>/out_v1 --workers 7`.
Acceptance (predeclared in plan.md): R3 > 330,208 AND R3 eval/s >= 56.3 AND R2 >= 87,000 AND the
Q neighbour keeps >= 0.9 of the R3 gain.

## Results (actual)

| variant | R3 PnL | dR3 | R3 fit/s | R3 eval/s | R2 PnL | dR2 | maker lots R3/R2 | verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| off (= U4) | 330,208 | 0 | 51.6 | 57.3 | 109,317 | 0 | 0/0 | base |
| flat Q20 | 330,019 | -189 | 51.7 | 57.2 | 111,098 | +1,781 | 3,350/3,696 | fail R3 |
| flat Q10 | 331,067 | +859 | 51.7 | 57.5 | 110,332 | +1,015 | 1,713/1,906 | fail neighbour (Q20 -189) |
| regime Q20 | 328,065 | -2,143 | 51.6 | 56.7 | 109,370 | +53 | 1,246/2,144 | fail R3 |
| regime Q10 | 329,125 | -1,083 | 51.6 | 57.0 | 109,345 | +28 | 626/1,097 | fail R3 |
| partial Q20 | 328,970 | -1,238 | 51.4 | 57.1 | 110,729 | +1,412 | 3,792/4,283 | fail R3 |
| partial Q10 | 330,573 | +365 | 51.5 | 57.5 | 110,153 | +836 | 1,942/2,196 | fail neighbour (Q20 -1,238) |

All penalties 0, max exposure incl. pending 100. `off` reproduces U4 exactly (R3 330,208, R2 109,317).
Official CLI (`env -u VIRTUAL_ENV uv run --locked python -m simulator.main --backtest
data/round3/round3_public.csv --strategy strategies/round_3/dataathletechamp/r3_follower_p1_aged.py
--log-dir <exp>/cli_r3_off --no-logs`) with the committed default: pnl 330,208.00, breach_penalty 0,
fills 1,666, traded_volume 301,670 (identical to U4). `tools.preflight`: local conservative preflight
passed (server sandbox validation still required).

## Why it does not help

U4 is almost never idle: on R3 the follower activates only 74 times (R2 70) and |inventory| q50 = q95
= 100, i.e. same-sign A signals keep extending the 5 s hold, so the maker gets a few percent of the
session and trades 0.6k-4k lots against ~300k follower lots. Effects are +-0.6 % of PnL with signs
that flip between Q10 and Q20; nothing passes the predeclared rule. The donor's gain came from the
regime switch that disables the follower in the low state; with the follower unchanged (as U4 needs)
there is no room left for the maker. Validation B already showed heavy passive quoting is toxic.

## Verdict

NEGATIVE. Keep `MAKER_MODE = "off"` (file is behaviour-identical to U4). The overlay code is kept
behind the flag for reuse (e.g. if a future follower is idle much more often).
Limitations: public tapes only, one seed each; no server run; not a private-round guarantee.
