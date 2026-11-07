# Round 2 A: the R1 seeds really lose, without penalties

Measured 2026-11-07 with the unchanged official SDK, not the independent C++
maker in the supplied memo. Read [market regimes](market-regimes.md) for data
definitions and [R1 evidence](../../round_1/dataathletechamp/round1-final-evidence.md)
before confusing the actual Final with the 507393 public-only research file.

## Actual frozen seed results

| Run ID | R1 origin | R2 A net PnL | Penalty | Filled orders | Executed lots | Final inventory |
|---|---|---:|---:|---:|---:|---:|
| r2-seed507-A-v1 | 507393 clipped research | -146085 | 0 | 11577 | 1166585 | -43 |
| r2-seed505-A-v1 | 505225 actual Final | -143178 | 0 | 11486 | 1159623 | -43 |
| r2-control-nofit-A-v1 | 449661 no-learned queue control | -168655 | 0 | 13959 | 1365510 | -100 |

The no-order observer earns exactly zero. It is a useful monetary floor:
none of these trading seeds is currently a demonstrated profitable R2 option.
R1 private 504903 and rank 14 say nothing about their new-tape profitability.

The clipping change alone loses 2907 versus Maciej's reference on A, reversing
its R1 improvement. Do not overwrite the R1 evidence or blindly choose the
historical 507k name. The no-learned control also changes inventory skew,
depth-price weighting and slot count, so its loss **does not isolate** the
incremental value of Ridge. A true no-Ridge ablation must hold those constant.

All inputs were unchanged and conservative preflight passed.
Maciej's cash 273492 plus -43 lots at the actual terminal liquidation
mark 9690 equals -143178. Clipped cash 270585 reconciles to -146085.
No-learned cash 800345 plus -100 at 9690 equals -168655.
Cash alone and midpoint alone are not the score.

## Reproduction and actual fill economics

`r2-final-seed-full-logs-A-v1` reproduces the Final seed's entire result exactly,
including PnL, cash, inventory, volume, fills and zero penalty. Result SHA256:
`422cbc2909932c9e6bb86e1ff9dcdf121fd06392dfe234a07c89fdfef43275c7`.
The trade ledger independently reconciles all quantities and cash.

There are 17,987 user-matched trades but 11,486 distinct filled user orders.
1,159,339 lots are maker fills; 284 lots are incidental taker fills from delayed
LIMIT arrival, despite IOC_MODE=0. Do not equate a fill-count field with matches.

Actual market-only BBO is reconstructed from the **run's book deltas**, not a
different null-market tape. Sample after all deltas at or before the outcome
clock; missing sides stay missing. Diagnostic signed markout is
`side_sign * (future_midpoint - fill_price)`, weighted by actually filled lots.

| Horizon after fill | Maker size-weighted mean, ticks/lot |
|---|---:|
| Immediately after the event | +0.48496 |
| 0.1s | +0.21883 |
| 0.5s | -0.10132 |
| 1s | -0.11853 |
| 3s | -0.08609 |

At 1s the **match-weighted** mean is +0.04765 while the **lot-weighted** mean
is -0.11853. Average/median small-fill success masks economically larger toxic
fills. This is a strong reason not to increase size indiscriminately.
Markout is still not independently executable liquidation PnL, additive closed
trade PnL, or proof that a particular size gate would improve total score.

Mean request age at fill is 0.45048s by lots; median match age 0.38917s.
The 5 ms send delay is only part of maker risk.
1,483 matches / 85,502 lots fill after cancellation was sent but before its
effective arrival: about 7.37% of all filled lots. There are 122 failed cancels
because the resting order has already disappeared; no rejected additions
were recorded. A cancel request never immediately frees risk capacity.

Time-weighted mean absolute inventory is 77.19; mean signed inventory +2.56.
The strategy spends 3,169.11s (52.82% of tape time) exactly at either boundary,
but actual absolute inventory never exceeds 100. Thus this is adverse-selection/
inventory timing loss, not a penalty-accounting failure or simply permanent long
exposure. Sampled PnL maximum drawdown is 178225.

Equal chronological quarters contribute +16977, -25141, -110622 and -24392.
These are changes of the continuous official PnL path, not restarted bots or
additive scores from independently reset windows. They are descriptive time
locations, never permissible hardcoded trading triggers.

## Cheap falsification: feature must precede the fill by 5 ms

`execution-conditional-v1` conditions on standing market-only book and actual
external executed flow at **fill time minus 5000us**. Its volatility is the
past 60 valid nonoverlapping 1s returns, sampled on the same 25ms-offset clock.
The high threshold, 1.936758 ticks, is the 67th percentile fitted on the
first 40% of this actual run. It differs slightly from null-market thresholds.
Undefined volatility is its own state, not calm.

Each boundary-crossing match is split into position-reducing and
position-increasing lots: a 200-lot sale from +100 reduces 100 then accumulates
100 short. Table entries are one-second size-weighted markouts of **accumulation
maker lots**, not a fitted strategy or a counterfactual PnL.

| Prior condition | Prefix A | Selection A | Late A |
|---|---:|---:|---:|
| High volatility | -0.4600 | -0.8396 | -0.5408 |
| Lower volatility | +0.0419 | +0.1844 | -0.0685 |
| Undefined volatility | -0.9019 | -1.2369 | -0.8254 |
| QI/flow agree with filled side | -0.0334 | -0.3989 | -0.2692 |
| QI/flow oppose filled side | -0.7320 | -0.7571 | -0.6391 |

The high-volatility premise survives all three consumed-A blocks. Low volatility
is **not universally safe**, and even agreeing QI/flow does not give positive
accumulation fill value. This contradicts a shortcut from arbitrary-observation
return correlation to aggressive profitable fills.

Simple realized match-size bins are not a clean explanation either: >=100-lot
accumulation markouts are -0.214/-0.441/-0.405; <100 lots
-0.099/-0.460/-0.187. FIFO, state and fill selection matter, not just a universal
quantity cutoff. Realized matched quantity is not requested quote quantity.

Models/scales only use the declared prefix. Actual future endpoints remain
inside each 40/30/30 block. Full A has already been observed; these blocks are
diagnostic/selection evidence, not pristine holdouts. Baseline fills are selected
by its orders: removing them changes fills, position, queue opportunities and
future liquidation. **Run a frozen paired policy to claim monetary improvement.**

## What to preserve and what not to deploy blindly

Preserve the exact standalone loader, external MARKET aggregation, per-match
inventory ledger and same-side reservations; keep IOC disabled by default.
Do not net opposing outstanding quantities or release cancel-pending orders.
Keep large quote headroom available when it has demonstrated value; do not
replace q200 with a tiny tutorial maker just to avoid risk.

Stop treating fixed R1 normalization, tiny 0.001 inventory skew and always-full
capacity as calibrated for R2. Do not delete those mechanisms from history:
test isolated volatility capacity, side capacity, and volatility inventory-skew
arms before combination or parameter sweeps.

Park permanent short bias, public crash timestamps, future-tail removal,
unverified persistent-wall anchors, more aggressive IOC alpha and intentional
>100 exposure. A 5ms threshold breach already costs 50 units *if* it can
actually be exited in 5ms; partial fills or disappearing liquidity cost more.
Necessary incremental condition is
`DeltaGross - 10000 * DeltaExpectedOutsideSeconds - explicitRiskReserve > 0`.
This inequality is not calibrated evidence or permission to bypass common risk.

## Reproducible commands and fingerprints

All commands below actually succeeded. Original IDs are immutable; use new IDs
for repetitions. Run from the active R2 worktree using its locked environment.

```bash
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-seed507-A-v1 --strategy strategies/round_2/dataathletechamp/clipped_ridge_seed_from_r1.py --tape data/round2/round2_public.csv --stage public-A-frozen-R1-seed-transfer
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-seed505-A-v1 --strategy strategies/round_2/dataathletechamp/final_maker_seed_from_r1.py --tape data/round2/round2_public.csv --stage public-A-frozen-R1-seed-transfer
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-control-nofit-A-v1 --strategy strategies/round_2/dataathletechamp/inventory_queue_seed_from_r1.py --tape data/round2/round2_public.csv --stage public-A-no-learned-forecast-control
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-final-seed-full-logs-A-v1 --strategy strategies/round_2/dataathletechamp/final_maker_seed_from_r1.py --tape data/round2/round2_public.csv --stage public-A-seed-reproduction-and-fill-attribution --full-logs
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/execution-attribution-v1/analyze.py
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/execution-conditional-v1/analyze.py
```

Seed SHA256s, in table order:
`b21e633b76bd2b74214ab684666b0faa5316b55761b18eece660e26b7f0152ac`,
`c1f194668ec83e94bf522e749ce36d266caeedb9244506ede2adeee68e8e3667`,
`46309d3232983388433f5bfde55da75a1c9011640e1fbc323260f0d1ff9d8165`.
R2 raw hash and SDK digest are recorded in [market-regimes](market-regimes.md).
Attribution source:
`c8e865efdf005060f99f9bbc5cacf5e4f38b34c8149bf489ce5db452bcfe7e62`.
Attribution result:
`4cfe40bb03b04853ba5115a2265598b0c2a49f7c65e6642cdddb348b1bd162a0`.
Conditional script/result:
`845e2d3236aa2ef29c2b6caa75a9eaa3382ee7953927a292264b55cf728d1ba1` /
`dd7b67ecf3230bd515832b850852d27bbfe7b11d657ccc7bc3d2df54092a2918`.
New supplied `ROUND2_MARKET_MAKING_RESEARCH.md` SHA256:
`135070b9248253f9be40afe9f997e69f6f1b6324308204b9e6cade97b66304c9`.
Its quantitative jump classifier and four described prototypes remain separate,
unverified reference claims; they are not these actual engine outputs.

Ruff check/format passed for both new diagnostic versions. Three
clock/missing-book profiler+attribution regression tests and two conditional
volatility/boundary-crossing tests passed. Server static validation, new R2
mechanics confirmation, B feedback and C private performance remain UNKNOWN.
No upload or automatic Final selection was performed.
