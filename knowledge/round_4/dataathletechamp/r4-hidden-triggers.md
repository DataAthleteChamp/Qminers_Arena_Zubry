# Round 4: hidden-IOC triggers on the U2 follower (negative)

Experiment `20261108-r4-w6-hidden-001`. Question: does the live order-ID-gap detector
(`r4-hidden-ioc-precursor.md`) add PnL to U2 (`r4_u2_trig2_ungated.py`, R4 886,626 / R3 415,404 /
R2 159,515, penalty 0)? Answer: no. All 30 variants failed the acceptance rule. The default keeps every
flag off, which reproduces U2 exactly.

## Implementation

`strategies/round_4/dataathletechamp/r4_follower_hidden.py` (sha256 `a94f9585…bbc1`) is U2 plus `HID_*`
flags, all `False` by default. The detector reuses the TRIG2 full-book scan of new market ids and adds
market trades' `taker_order_id`. A detection fires when the smallest new id > max id + 1.

- Inside the trading strategy it finds 2,141 detections and 2,248 missing ids on R4. The lots-0 parity
  recorder finds 2,158 and 2,262.
- With the detector on but no action (`detect_only`), the PnL is identical to U2 on all three tapes.
- Burst mode overlays target ±N for H ms, then unwinds with IOCs at touch ±3 back to the follower's
  ±100. It pays the 10,000/s breach penalty.

Rules come from the brief and the coordinator's direction and strength study. No fitting was done here.
The rules were motivated by descriptive statistics on these same tapes, so the tapes are not
independent evidence.

## Setup

- Engine: official `ExchangeSimulator` in-process (runner `20261108-r4-runner-001`). 5 ms latency,
  depth 20, ±100 limit, 10,000/s penalty, full tapes.
- Data sha256: R4 `61c0b6d1…`, R3 `1021586b…`, R2 `88ff641e…`. `simulator.py` `c37b2262…`.
- Accept a flag only if R4 > 895,492 (+1%) and R3+R2 >= 557,671 (−3% of 574,919).

## Results (PnL; penalty is 0 unless shown)

| variant | R4 | R3 | R2 | R3+R2 Δ |
|---|---:|---:|---:|---:|
| U2 / all off / detect_only | 886,626 | 415,404 | 159,515 | 0 |
| ARM 200 ms gated | 873,294 | 409,502 | 150,214 | −2.6% |
| ARM 200 ms ungated | 852,965 | 373,913 | 72,830 | −22.3% |
| ARM 500 ms gated | 871,198 | 394,793 | 130,466 | −8.6% |
| ARM 500 ms ungated | 788,730 | 285,189 | −7,763 | −51.8% |
| FLOW F200 gated | 887,717 | 412,654 | 160,268 | −0.3% |
| FLOW F200 ungated | 868,981 | 403,886 | 172,935 | +0.3% |
| FLOW F400 gated | 886,705 | 418,295 | 160,529 | +0.7% |
| FLOW F400 ungated | 865,398 | 406,148 | 176,871 | +1.4% |
| FLOW chain (last A 1 s → flow → mid), all, gated | 868,457 | 395,587 | 123,765 | −9.7% |
| FLOW chain, all, ungated | 772,146 | 323,023 | 79,485 | −30.0% |
| FLOW chain, strong only, gated | 864,517 | 395,212 | 130,705 | −8.5% |
| FLOW chain, strong only, ungated | 865,866 | 357,394 | 123,236 | −16.4% |

Burst rows show PnL / breach penalty, with the change before penalty vs U2 in brackets.

| variant | R4 | R3 | R2 |
|---|---:|---:|---:|
| ≥3 det/300 ms + flow F200, N300 H200 | 745,047 / 139,476 (−2k) | 22,766 / 358,059 (−35k) | −42,862 / 178,438 (−24k) |
| F200, N300 H500 | 606,855 / 309,186 (+29k) | −340,761 / 778,065 (+22k) | −239,593 / 398,152 (−1k) |
| F200, N600 H200 | 711,298 / 145,849 (−29k) | −147,704 / 368,167 (−195k) | −155,676 / 187,286 (−128k) |
| F200, N600 H500 | 618,622 / 310,675 (+43k) | −380,220 / 777,323 (−18k) | −305,594 / 405,609 (−60k) |
| F400, N300 H200 | 776,843 / 102,136 (−8k) | 125,841 / 263,894 (−26k) | 14,260 / 140,529 (−5k) |
| F400, N300 H500 | 666,121 / 231,468 (+11k) | −165,228 / 595,142 (+15k) | −156,590 / 316,838 (+1k) |
| F400, N600 H200 | 740,629 / 101,025 (−45k) | −5,711 / 270,784 (−150k) | −60,455 / 141,963 (−78k) |
| F400, N600 H500 | 657,987 / 231,935 (+3k) | −207,822 / 598,137 (−25k) | −203,562 / 327,527 (−36k) |
| strong (gap ≥ 2 or ≥3/300 ms), dir last A → mid, N300 H150 | 321,848 / 408,267 (−157k) | −671,585 / 786,990 (−300k) | −424,331 / 443,283 (−141k) |
| strong, N300 H300 | 196,186 / 585,835 (−105k) | −987,947 / 1,227,716 (−176k) | −598,922 / 652,011 (−106k) |
| strong, N900 H150 | −132,574 / 483,252 (−536k) | −2,121,882 / 934,221 (−1.6M) | −927,124 / 583,505 (−503k) |
| strong, N900 H300 | −297,728 / 698,304 (−486k) | −1,916,708 / 1,353,354 (−979k) | −1,046,613 / 770,088 (−436k) |

## Why it fails

- **ARM.** Smaller sweeps (span >= 1 or fill >= 200) after a detection add flips that lose. Longer
  arms and ungated flips lose more.
- **FLOW.** About 90% of the signals extend a position the follower already holds in that direction:
  A events and `FLOW_TRIG` already capture the prior-flow information. The gated versions are therefore
  neutral (+0.1% / +0.0% on R4), and ungated flips cost about 2% on R4.
- **Direction chain.** Firing on every detection, or on strong events (about 400 on R4), adds bad flips
  even with the alpha gate. The study's 0.82–0.86 accuracy is conditional on a nonzero 1 s move; the
  marginal flip edge after U2's own triggers is negative.
- **Bursts.** The gross edge is at best +43k on R4 over 61 bursts (about 700 per burst). Each burst
  costs about 10,000 × H in penalty, about 5,000 at 500 ms. Strong-event bursts lose even before the
  penalty, because of IOC slippage at touch ±3 and wrong-way bursts. Within ±100 the edge is far too
  small to pay for a breach.

## Reproduction

From MAIN, with `E=experiments/round_4/dataathletechamp/20261108-r4-w6-hidden-001`:

```bash
env -u VIRTUAL_ENV uv run --locked python \
  experiments/round_4/dataathletechamp/20261108-r4-runner-001/runner.py \
  --strategy $PWD/$E/snap_v1_r4_follower_hidden.py --grid $PWD/$E/grid_main.json \
  --tapes r4,r3,r2 --out $PWD/$E/out_main --workers 4
```

- Rows 1–9 and the first eight burst rows: `snap_v1` (`f1ef1a5c…`) with `grid_main.json`.
- Direction-chain rows and strong bursts: `snap_v2` (identical to the committed file) with `grid_v2.json`.
- Official CLI, default file on R4 (`simulator.main --no-logs`): PnL 886,626, penalty 0, 48 s.
- `tools.preflight` passed.

## Limitations

There is one public tape per round, and these tapes also motivated the rules. A passing or failing
local run is not a private-round result. The penalty settings and burst sizes are taken from the brief,
and only the brief's grid was tested.
