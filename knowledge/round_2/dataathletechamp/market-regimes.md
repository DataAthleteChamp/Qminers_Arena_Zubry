# Round 2 A: observed market regimes, not a known generator

Investigated 2026-11-07 in `Qminers_Arena_Zubry_Round2`, on
`round_2/dataathletechamp`. Read alongside [data provenance](data-provenance.md)
and [actual execution diagnostics](execution-diagnostics.md).

**Decision:** do not transfer unconditional R1 q200/100 inventory exposure.
The main change is rare, clustered price risk and weaker directional forecasting,
not a wholesale change in event intensity or median requested order sizes.
Past-state risk controls are plausible; their monetary benefit still needs an
actual paired strategy replay. No public statistic guarantees private profit.

## Data, units and common methodology

R2 A contains 2,193,064 rows over 0.000067--5999.996013 seconds.
Raw SHA256:
`88ff641e962540c66fa1cc4a3547585d31838d0929340150690cabb4f3cfb9f4`.
Preserve raw bytes; the registered lossless gzip is shared on main.
One anonymous instrument, integer price units/ticks and integer lots.
Do not attach a currency or asset identity to these observations.

All four profiles use the same unchanged official SDK and a strategy sending
**no orders**. Aggregate MARKET orders at the same price. Observe the standing
book on an exact 50 ms clock, offset 25 ms, before the following market event:
no event-bucket aliasing, future interpolation or zero substitute for a missing
side. Time-weighted spread and calendar-sampled returns have separate definitions.

The table uses nonoverlapping one-second midpoint differences, population SD,
not annualized realized volatility. Missing return endpoints are excluded and
counted. A genuine valid-price tail is not removed for being extreme.

| Dataset | Rows | Duration s | Time-weighted mean spread | 1s return SD |
|---|---:|---:|---:|---:|
| R0 original warmup | 53,758 | 3,599.000 | 2.000000 | 2.566819 |
| R0 public v2 | 2,000,000 | 5,749.869 | 1.587765 | 0.496113 |
| R1 public | 4,411,336 | 11,999.990 | 1.070640 | 0.920288 |
| R2 public A | 2,193,064 | 5,999.996 | 1.230016 | 3.649809 |

R0 warmup is a distinct sparse tutorial distribution, not interchangeable with
R0 v2. R2 SD is 3.97 times R1; corresponding variance is about 15.73 times,
not merely four times.

## What changed

R2 nonoverlapping one-second returns: mean -0.05860 ticks, SD 3.64981,
minimum -94.5, maximum +112, p1/p99 -10/+9, excess kurtosis 259.76.
R1 minimum/maximum -4/+4, p1/p99 -2/+2, excess kurtosis 0.536.
Normal-diffusion assumptions are a poor account of the R2 extremes.

One-tick spread occupies 83.93% of valid book time versus 93.02% in R1.
Mean spread rises only about 14.9%, far less than return variance.
R2 has 4.118884 seconds without a two-sided book; 81 missing 50 ms samples
and eight invalid nonoverlapping one-second return pairs. These are explicit
missing states, not invented midpoint zero or a claim that every tail is a gap.

Event rates are 365.51/s versus R1 367.61/s. Resting inserts are about
178.31/s versus 179.80/s; IOC requests 8.90/s versus 8.01/s.
Resting requested quantity medians remain 14; IOC request medians remain 61.
R2 best-level median bid/ask depth is 686/716 lots versus 902/900 in R1.
Requested sizes are not executed sizes; canceled-request ages are not live
lifetimes. Similar medians do not identify the hidden market generator.

## Rare outcomes dominate variance

`jump-study-v1` uses one-second endpoints anchored every 50 ms, so these windows
overlap. Its SD 3.76536 and range -95.5/+118.5 differ from the nonoverlapping
table above. These definitions must not be mixed with the supplied independent
100 ms study's SD 3.86.

| Absolute next-1s change | Overlapping windows | Share of centered square variation |
|---|---:|---:|
| At least 5 ticks | 6.64% | 88.90% |
| At least 10 ticks | 1.97% | 73.38% |
| At least 20 ticks | 0.28% | 53.98% |

For the 335 windows at least 20 ticks, 124 contain an intermediate missing
book sample; 211 do not. Thus tails are not merely a zero-midpoint artifact.
These are overlapping windows, **not 335 independent jump episodes**.
Tail frequency and variance attribution are hindsight descriptions, not online
gates or calibrated probabilities on a new tape.

Excluding future tails makes QI correlation look better, but cannot be deployed:
we do not know the future exclusion label when placing an order.

## Signals and chronological stability

Top-level QI correlation with next return:

| Horizon | R1 | R2 |
|---|---:|---:|
| 0.1s | 0.2995 | 0.0890 |
| 0.5s | 0.3389 | 0.0494 |
| 1s | 0.2456 | 0.0329 |

R2 executed-flow EMA1 correlation is 0.0941 at 0.5s and 0.0640 at 1s.
An eight-feature past-fit linear screen, fitted before 40% of A, improves
selection-window MSE over zero by 2.842%/2.914%/1.737%/0.908% at
0.1/0.2/0.5/1s. R1's same 0.5s screen improves 19.737%.
This is a new diagnostic model, **not Maciej's exact callback Ridge predictor
or a strategy PnL ablation**.

Every actual fitted future-target timestamp is before 2399.9984052s; maximum
included target is 2399.975s. Selection ends at 4199.9972091s.
Full-A descriptive screens have already consumed the last 30%: do not relabel
it as untouched merely because coefficients were fitted earlier.

Past 60s volatility thresholds fitted on the first 40% are
1.13224/1.92095 ticks at the 33rd/67th percentiles; minimum-depth thresholds
24/319 lots at the 10th/50th percentiles. Counts on the one-second clock:
calm/deep 1,182; high volatility 2,094; middle 2,264; thin/wide 154;
undefined 304. The state is observable from the past; its next return is not.

A prior three-second move of at least two ticks does **not** produce stable
one-second continuation: signed means are +0.059/+0.179/-0.096 ticks across
fit/selection/late A. Book/flow confluence appears steadier for arbitrary
observation times (+0.358/+0.290/+0.349), but
[actual accumulation fills do not inherit that edge](execution-diagnostics.md).
Do not turn these unconditional cells into a permanently aggressive safe-side
policy.

## Latency and FIFO implications

At 119,919 hypothetical null-market decision clocks, the BBO changes before
5 ms delivery 2.275% of the time versus R1 1.213%.
An old ask-capped buy would miss the newer ask in 0.568% of decisions;
an old bid-capped sell would miss the newer bid in 0.615%.
R1 counterparts are 0.308%/0.321%.
These are no-order book hazards, **not actual IOC fill probabilities or PnL**.

Five milliseconds is the action delay, not the whole maker exposure:
actual orders often wait much longer in FIFO, and cancellation can lose a race.
Never credit a pending cancellation or shrink before confirmation.
At q=-100, a buy of 200 can still be legal within the 100 envelope; quoted
quantity is not the same as increasing the position limit.

## Source audit and reproduction

Official upstream commit: `3f5bea730d5f341c6988b1fe2722998b66270ea0`.
Installed SDK digest:
`6dba6395cd6104e47132c53a251f2f0781b4d66d910c34e0025cc7843fbeadb5`.
Profiler SHA256:
`9beb8a019ff2f26d83980f4f15cb84768916563f33d91d8bc0ac8f855e213d69`.
Regime script/result:
`cfd033d50857c9938f68289996d7ea1bd3f7f58f97c99a355b589a1808db24fd` /
`5a5c2e89ff69a66b0c8a3432e1917f08991d3a104f14bc0badd5490794432223`.
Jump script/result:
`30e3bb2e87ff4b708961ade594bdd6a32d82b365028ddb5ee1d688959d633170` /
`9009eb079a20ada0900a94694fcd521eaef9963ccab7eb50605ba2d10d5aba95`.

Successful original profile commands, from the active worktree:

```bash
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/market-profile-v3/profile.py --id round0-warmup --data ../Qminers_Arena_Zubry/data/round0/sample.csv --label round0-original-warmup
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/market-profile-v3/profile.py --id round0-v2 --data ../Qminers_Arena_Zubry/data/round0/sample_v2.csv --label round0-public-v2
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/market-profile-v3/profile.py --id round1 --data ../Qminers_Arena_Zubry/data/round1/round1.csv --label round1-public
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/market-profile-v3/profile.py --id round2 --data data/round2/round2_public.csv --label round2-public-A
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/regime-study-v1/analyze.py
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/jump-study-v1/analyze.py
```

All completed successfully. These IDs/outputs are immutable; reproduction needs
new IDs/output versions. Raw scripts/results remain in ignored experiments per
the contributor layout. Two profiler regression tests passed. Earlier v1
event-bucket aliasing and v2 NaN-serialization failure remain preserved and
qualified; neither silently replaced the successful evidence.

Supplied `ROUND2_STATISTICAL_ANALYSIS.md` SHA256
`7d4048217e3cb725152f63a3cc54600e64d4b54952a95834114a695ff4f09578`
is an untrusted independent reconstruction. Its proxy maker -179596 is not an
official seed result. Newly supplied jump-classification AUC values and prototype
claims likewise require their own reproducible verification.

UNKNOWN: new official mechanics, generator/asset identity, B raw availability
and reuse, C path/distribution, team field statistics and private ranking.
