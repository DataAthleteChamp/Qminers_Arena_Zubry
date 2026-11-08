# R3 follower jump guard (exit-side fragility) — screen and official-engine tests

Experiment `20261108-r3-w5-jumprisk-001` (branch `r3-da-jumprisk`, base commit cec5525).
Strategy: `strategies/round_3/dataathletechamp/r3_follower_jumpguard.py` = U4
(`r3_alpha_follower_p1_sw3.py`, sha256 e4dfd2ce…574f) + flag `JUMP_GUARD` and `JG_*` knobs.
Data: R3 public `round3_public.csv` sha256 1021586b92a3…, R2 public `round2_public.csv`
88ff641e9625…; official simulator unchanged (`simulator.py` c37b2262186f…). Time unit: 1 s PnL
samples of the official engine (`pnl.csv`); fit window t < 2400 s, eval t >= 2400 s.

## Question

Server validation tape B lost −134k on 29 seconds with |ΔPnL_1s| >= 3,000 (D1 follower). Is there
an observable, causal precursor of large adverse 1 s moves against the ±100 position, and does
cutting exposure while it holds pay on R3/R2 public?

Predeclared accept: R3 total >= 327,208 AND R3 eval/s >= 56.3 AND jump-second loss reduced on
both R3 and R2 AND R2 total >= 98,385.

## Precursor screen (U4, official engine, recorder flag `JG_RECORD`)

Features are taken from the last book seen before each 1 s sample boundary and related to the
ΔPnL of the following second, in-position seconds (|pos| >= 50) only: R3 5,899 s, R2 5,883 s.
U4 jump seconds are net POSITIVE on both public tapes (R3 10 s, 7 up, +25.2k, adverse 3 s −17.4k;
R2 9 s, 5 up, +9.9k, adverse 4 s −24.8k).

| condition at start of second | R3 n / ΣΔ / jumps (ΣJ) | R2 n / ΣΔ / jumps (ΣJ) |
|---|---|---|
| (a) exit-side market qty within 3 ticks < 50 | 15 / −15.8k / 3 (−17.4k, all adverse) | 32 / −0.6k / 3 (−10.7k) |
| (a) … < 100 | 28 / −1.5k / 5 (−4.4k) | 64 / +9.2k / 4 (−5.2k) |
| (b) exit-side L1→L2 gap >= 3 ticks | 32 / +18.4k | 40 / +6.5k |
| (b) spread >= 4 | 66 / +19.0k | 86 / +22.3k |
| (c) opposite sweep >= 2 ticks in last 1 s | 166 / +31.4k / 0 jumps | 135 / +20.1k / 0 jumps |
| (d) Σ|Δmid| over last 5 s >= 10 ticks | 1,791 / +287.6k | 987 / +122.7k |

Only (a) thin exit depth precedes adverse jumps; (b)–(d) flag seconds that are on average
favourable (marks rebound after wide/gapped books; sweeps are the follower's edge).

## Official-engine policy tests (`run_variant.py`, same config as `simulator.main`)

Guard = cut via IOC (limit exit touch ∓ 3) to `JG_KEEP` while the condition holds; restore by IOC.

| variant | R3 total | R3 eval/s | R2 total | triggers R3/R2 |
|---|---|---|---|---|
| U4 base (flag off) | 330,208 | 57.2 | 109,317 | 0 |
| a1 depth<100, flat, no persistence | 69,735 | 8.5 | −102,103 | 347/368 |
| a1 gap>=3 / spread>=4 | −24,702 / −105,597 | — | −126,221 / −166,783 | 506/818 |
| a1 opposite sweep >= 4 ticks | 320,121 | 55.7 | 104,022 | 14/12 |
| a2 depth<30/50 flat or keep 50, restore only on next A | 127,689–240,111 | ≤ 40.8 | −9,946–63,147 | ~250–310 |
| a2 depth<50 persist 0.5 s | = base (never triggers) | | | 0 |
| a2 depth<50 persist 0.2 s, grace 0.5 s, flat, min 1 s | 325,826 | 57.3 | 107,343 | 9/12 |
| a3 same, persist 0.1 s / 0.3 s | 319,385 / 326,028 | 54.6 / 56.1 | 100,493 / 103,921 | |
| a3 same, depth<30 / depth<100 | 323,798 / 310,746 | 56.1 / 52.8 | 114,767 / 100,847 | |
| a3 same, no grace, min 0.5 s | 329,596 | 58.3 | 89,859 | 10/14 |
| **a3 depth<50, persist 0.2 s, grace 0.5 s, keep 50, min 1 s** | **328,886** | **57.2** | **107,871** | 9/13 |

Instant triggers churn: the exit side is briefly thin right after the entry sweep, and every
cut/restore pays ~2 spreads on 100 lots. Requiring 0.2 s persistence plus 0.5 s grace after a
new entry/flip removes the churn.

Paired on U4's own jump seconds (same timestamps), best variant (keep 50):

| | R3 adverse / favourable / net | R2 adverse / favourable / net |
|---|---|---|
| U4 | −17,377 / +42,616 / +25,239 | −24,849 / +34,778 / +9,929 |
| guard keep 50 | −11,809 / +37,766 / +25,957 | −17,287 / +29,278 / +11,991 |

Neighbourhood of the keep-50 centre (Δ total vs U4, R3 / R2; paired adverse-jump PnL R3 / R2):

| change | ΔR3 | ΔR2 | adverse R3 / R2 |
|---|---|---|---|
| centre (depth<50, persist 0.2, grace 0.5, min 1, keep 50) | −1,322 | −1,446 | −11.8k / −17.3k |
| persist 0.15 / 0.25 | −4,073 / +49 | −2,836 / −599 | −11.9k / −11.8k ; −15.2k / −19.5k |
| depth<40 / depth<60 | −2,139 / −1,322 | −4,072 / −1,908 | −14.1k / −11.8k ; −19.5k / −17.3k |
| min 0.5 s | +590 | −9,279 | −11.8k / −25.7k |
| grace 0.3 s | −1,322 | −1,446 | = centre |

11 of 14 neighbour deltas are negative (mean ≈ −2.1k); adverse-jump losses shrink in 13 of 14.

### Hidden-IOC precursor (coordinator suggestion; guard use only)

Detector: callback with no trades and unchanged visible book (lengths of both sides plus the
top 3 orders per side by id/price/qty); guard immediately to `JG_KEEP` while >= `JG_HIDDEN_N`
such events in `JG_HIDDEN_W_S`, unless the last trade signal agreed with the position within
0.5 s. The live count is 164,602 on R3 (~27/s) vs 0.55/s true hidden IOCs on the tape: deep
inserts/cancels beyond the 20-tick public depth dominate, so the guard fires ~1,500 times.

| variant (on top of the depth guard unless noted) | R3 total | R2 total |
|---|---|---|
| n>=1 in 0.2 s, keep 50 | 177,684 | 28,416 |
| n>=1 in 0.2 s, keep 0 | 12,308 | −54,353 |
| n>=2 in 0.5 s, keep 50 | 176,070 | 29,227 |
| n>=1 in 0.2 s, keep 50, hidden only | 177,352 | 27,143 |

Negative as implemented (detector fidelity, not necessarily the precursor). The aggression use
(hidden-elevated -> trade the next visible sweep) was not tested within the time budget.

## Verdict

Depth guard, keep-50 centre: nominal PASS of the predeclared rule — R3 328,886 >= 327,208,
eval 57.2/s >= 56.3, adverse-jump losses on U4's jump seconds shrink on both tapes (R3 −17.4k ->
−11.8k, R2 −24.8k -> −17.3k; paired net jump PnL +0.7k / +2.1k), R2 107,871 >= 98,385, penalty 0.
Set as the file default (`JUMP_GUARD = True`). It is a hedge, not alpha: it costs −1.3k / −1.4k
on the public tapes, was picked in-sample from ~23 variants, and rests on 3–4 adverse seconds
per tape; U4 stays the higher public-PnL file. Ship it only if heavier private jumps (tape B) are
believed; tape B itself could not be replayed. Official CLI on the final file
(sha256 b34b944e6e46…389b): R3 328,886, R2 107,871, breach penalty 0; `tools.preflight` passed.
`JUMP_GUARD = False` reproduces U4 (330,208 / 109,317) exactly. All guard modes stay as flags.

## Reproduce

```
cd <main checkout>; E=<worktree>/experiments/round_3/dataathletechamp/20261108-r3-w5-jumprisk-001
env -u VIRTUAL_ENV uv run --locked python $E/run_variant.py <strategy.py> data/round3/round3_public.csv \
  $E/runs/<name>_r3 '{"JUMP_GUARD": true, "JG_DEPTH_MIN": 50, "JG_PERSIST_S": 0.2, "JG_GRACE_S": 0.5, "JG_MIN_S": 1.0, "JG_KEEP": 50}'
env -u VIRTUAL_ENV uv run --locked python $E/analyze.py $E; env -u VIRTUAL_ENV uv run --locked python $E/paired.py $E <names>
```

Limitations: public-tape PnL only (tape B itself not available locally); 17+ guard variants tested
on the same two tapes, so the best one is selected in-sample; the jump-second improvement rests on
3–4 adverse seconds per tape; mark-to-market liquidation walks the whole book, so part of a "jump"
is a thin-book mark that can revert.
