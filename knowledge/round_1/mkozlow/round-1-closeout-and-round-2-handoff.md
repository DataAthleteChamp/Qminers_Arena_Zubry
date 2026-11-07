# Round 1 closeout and round 2 handoff

Prepared 2026-11-07 from retained research and completed local official-simulator runs. This is the current round1 knowledge summary. It supersedes older “current best” claims in team-handoff.md and README.md, which describe earlier checkpoints.

## Final decision and evidence boundary

Best verified local public result: **505,225 PnL, zero inventory penalty**. The 700,000 target was not reached. Retained candidate: [505225_ridge_queue_maker.py](../../../strategies/round_1/mkozlow/505225_ridge_queue_maker.py).

- SHA256: c1f194668ec83e94bf522e749ce36d266caeedb9244506ede2adeee68e8e3667.
- Size: 8,419bytes; conservative local preflight passed.
- Source: experiments/round_1/mkozlow/side-skew-refinement-035/a2_s0010/strategy.py, copied exactly.
- Official result: cash−497675, inventory+100, liquidation mark10029, penalty0; −497675+100×10029=505225.
- Traded volume2,020,098lots:2,019,923user-maker lots and175user-taker lots from LIMIT activation. IOC is disabled.
- PnL attribution:249132 before6000s;130236 in6000–9000s;125857 afterward. Inventory is continuous across these boundaries.
- Maximum reserved exposure100; inventory median absolute100. This policy often holds the boundary, despite never paying a penalty.

These are selected results on one repeatedly inspected public tape. No final private-round result, final dashboard selection or server sandbox confirmation was established in this work. “Prepared for submission” is not proof it was uploaded. No commit, push, pull or automatic upload was performed.

The final sprint verified30 candidate/control runs plus one successful baseline data-collection replay. An initial collector failed on a one-sided book and was retained as a failure, then corrected in a fresh experiment. This is not a count of all research conducted during the round.

## Data, mechanics and reproducibility

Raw input: data/round1/round1.csv,4,411,336events, approximately12000seconds.

- Data SHA256: 362e8208be1eeec32ad190d097774e26448f0d5149575a8e1b1efd1db1735940.
- Official simulator-source digest: 6dba6395cd6104e47132c53a251f2f0781b4d66d910c34e0025cc7843fbeadb5.
- Research branch: r1/mkozlow/research. Official sources and raw input remained unchanged.
- Tape timestamps are seconds; strategy callbacks use microseconds. Five milliseconds is5000microseconds, not a CPU deadline.

The authoritative engine is the installed official simulator. It uses price-time priority,5ms request latency, no fees, penalty-free inventory±100 and hard potential-position limit±1000. Limits and scoring must be rechecked for round2.

Due requests activate in ready-time order before the next applicable tape event; the engine advances its clock to ready_at_us. Older notes saying every action simply receives the next event's timestamp are imprecise. Strategies still need public callbacks to make new decisions.

Self-matching is excluded. A LIMIT intended to be passive can cross market liquidity after5ms; “no IOC” does not mean zero taker executions. There is no native post-only or good-until expiry type. Size reduction preserves FIFO but incurs latency; increasing size requires a new order.

Final PnL values inventory against executable opposite market-book liquidity, with fallback rules beyond available depth. It is not midpoint valuation and not an actual strategy closing trade. Negative cash alone is not a loss.

Recheck the candidate using a fresh output directory:

    uv run --locked python -m tools.preflight strategies/round_1/mkozlow/505225_ridge_queue_maker.py
    uv run --locked exchange-simulator --strategy strategies/round_1/mkozlow/505225_ridge_queue_maker.py --backtest data/round1/round1.csv --log-dir experiments/round_1/mkozlow/round-1-closeout-recheck/logs --no-logs

These are reproduction instructions, not a claim of an additional closeout replay. Do not rerun into completed artifact directories. Local CLI/preflight does not implement the website's entire static checker.

## Market distribution: what we actually observed

This was a tight-spread, heavily canceled, heavy-tailed-size market:

- Mean time-weighted spread1.07064ticks; about93.1% of quarter-second samples have a1tick spread,6.8% have2ticks.
- Median market touch depth about898bid/897ask lots; time-weighted means1326/1306. Depth tails and thin states matter more than these averages suggest.
- Median event gap1.795ms. Multiple events commonly occur within one action delay.
- Inserted quantity median15, p90154, p99973. IOC median request61lots, p90360. Submitted quantity is not executed quantity.
- Orders≥100lots represent about15% of inserts but77% of submitted quantity. Large original IOC size is not necessarily visible in the public executed-trade feed.
- Cancellation-request age median.337s and mean.467s, little different across size buckets. These are request ages, not live-order survival times.
- About13.24% of cancel requests target already-absent orders. Withdraw remaining live quantity, not original submitted quantity, when measuring cancellation pressure.
- Both book sides are not always present:677event callbacks had a missing side. Guard every midpoint, imbalance and depth calculation.

Plain1s price-return autocorrelation was close to zero in the initial profile. This does not exclude conditional prediction from book and flow. The instrument is anonymized; no asset identity, fixed10000anchor or known generator was established.

Sources: [market profile](../market-research.md), [price/size distributions](price-size-distributions.md), [cancellations](../cancellations.md).

## Transfer hypothesis and distribution-focused fitting

The team expects related public/private generator distributions. Supplied round0 public/private diagnostics support similar spread, quantity, cancellation and volatility mechanics with very different price paths, but that supplied comparison was not independently reproduced here.

Round1 provides a useful internal distinction:

- Exact size histograms differ only about1.4–1.5% total variation across chronological thirds.
- Absolute midpoint occupancy differs roughly25–79%. A shared generator does not imply the same realized drift or occupied price levels.
- Exact price lookup tables improved training error but worsened later30s error about5–6%, even though almost every later price was already seen.
- Absolute-price, modulo5/10 and simple rounding features did not establish forward-time improvements.

Favor conditional size, flow, queue, spread and arrival mechanics over memorizing this path. Parameter specialization is reasonable; future leakage, absolute-price anchors and tape-time schedules are not evidence of a transferable distribution.

The closing parameter sweep explicitly treated the public tape as tuning data. Chronological segment comparisons remain useful stability diagnostics but are not untouched validation after repeated inspection. One-arm pnl_se is not a paired-delta SE or probability of beating another strategy.

## Signals worth retaining

**Imbalance plus executed flow:** current touch imbalance and recent aggressive flow contain complementary short-lived information. Early fixed models reduced250ms MSE about21–22% relative to zero-change prediction; a nonlinear model reached roughly24%. Price history alone did not help those early models, and5s prediction was weak.

Strong imbalance with agreeing flow was more informative than the same imbalance with opposing flow. Such conditional midpoint responses are not fill-conditioned earnings, and stronger selected states must not be presented as unconditional accuracy.

**Same-price replenishment:** publicly reconstructed fresh arrivals at an unchanged touch improved250ms MSE about6.3% relative to a book/flow nonlinear baseline in both later checks. New-best arrivals added under1%. Paired60s-block uncertainty supported the same-price increment under that model and dependence assumption; this was prediction evidence, not maker PnL.

Public snapshots and maker IDs reconstructed all measured70,286,924lots of live touch cancellations and about99.987% of touch additions in the reference replay. Exclude visibility-boundary ambiguity. Do not use engine-only raw event causes as online predictors.

**Broad cancellation counts:** little incremental directional information beyond the resulting depth, imbalance and flow. Their execution importance remains large. Fresh arrivals deserve more research than treating every withdrawal request as a separate alpha.

**Flow ownership:** filtering both taker_owner=market and maker_owner=market excludes aggression hitting our own quotes. This changes observed features as our market share increases. Including all market-taker executions is a sensible definition to investigate, but coefficients and training observations must match it. Adding our liquidity can itself change executed quantity. On477k.py, the one-line ownership-complete change without refitting reduced PnL477516→474767; do not call it an assured profit fix.

Sources: [signals](../signals.md), [public replenishment](../replenishment.md), [execution/forecast report review](side-execution-forecast-report-review.md).

## Continuation, reversal and multiple price levels

Closing research added causal20ms samples of imbalance, flow, depth changes, recent20/100/250ms moves, time since the last move and EMA departure.

After a recent short move, the next250ms outcome was approximately22–23% continuation,20–21% reversal and57% unchanged. Do not assume every move continues, or that no further move means passive making is unattractive.

Six fixed boosted classifiers estimated reaching up/down1/2/3ticks within3s; another classified the next250ms midpoint-change direction. Both upward and downward barriers can be reached within the horizon, so their probabilities are not mutually exclusive. Prediction improvements were largest at1tick and much smaller at3ticks, where no-hit prevalence makes raw accuracy misleading.

Additional nonlinear endpoint forecasts achieved later correlation about.52 at250ms and.38–.40 at1s. Exported standalone trees matched sklearn predictions within1e-10. These results did not produce a superior quoting policy:

- Path-probability inventory target479306 versus477516 control: small total gain, inconsistent later segments.
- Replace quote-center forecast with path score466942.
- Joint execution-value sizing469643; combine with path inventory target473899.
- Nonlinear1s replacement471839 versus496928 control; blend489830;250ms/1s blend489418.

All new learned policies activated only after6000s, with complete training labels before that boundary and unchanged earlier strategy state. These are reused checks. The evaluation gates are not instructions to idle for half of round2.

Sources: [closing sprint](side-distribution-and-path-sprint.md); experiments side-path-execution-model-031, side-path-quoting-033 and side-nonlinear-return-036.

## Best strategy: exact mechanism

The best is a passive ridge-centered FIFO maker, not the old zero-forecast64lot strategy and not the new path classifier.

Its frozen ridge uses five standardized inputs: touch imbalance, aggregate visible market-depth imbalance, and exponentially decayed signed market-to-market flow at.2/1/3seconds. The supplied477k.py contains the exact coefficients and normalization constants; training provenance was not supplied.

    center = market_midpoint + 2 * ridge_prediction - 0.001 * inventory
    bid = max(1, min(market_best_bid, floor(center)))
    ask = max(market_best_ask, ceil(center), bid + 1)

These are passive at decision time; latency still permits incidental taking. Inventory skew shifts the center one-tenth of a tick at100lots. It influences whether a quote remains at touch or moves back; it cannot improve inside a1tick spread without crossing.

Quantity is adaptive through capacity even though nominal target is200:

- Total buys B and sells S include all pending, live and cancel-pending remaining quantities.
- New BUY capacity100−I−B; new SELL capacity100+I−S.
- At flat inventory, only100lots per side fit. At+100, selling200 can reverse to−100 without exceeding the band.
- Keep existing same-price FIFO orders and add new orders at the back, up to eight per side. Additions use available headroom, with minimum10lot top-ups.
- Full replenishment replaces the earlier remainder≤60 rule; it does not imply submitting200every callback.
- Any pending submission or cancel on a side blocks additional submissions there until resolved.
- Cancel when target changes or the side is disabled, retaining reservation. Replace after terminal confirmation and a public callback, with another5ms acceptance delay.
- No native expiry, age-based cancel policy, signal block, emergency overflow or active IOC. Some legacy constants/disabled branches remain; preserve exact tested behavior.

The retained file was copied byte-for-byte and hash checked. Do not clean or retune it and retain its PnL prefix without rerunning.

## What produced actual PnL gains

Benchmark lineage, all full public tape unless explicitly noted:

- Old64lot zero-forecast midpoint maker206364.
- Teammate95lot inventory/queue maker343269, independently reproduced.
- Nominal200 and same-price top-ups416852.
- Full headroom replenishment with two orders429954; eight orders435759.
- Half inventory skew with eight orders451276.
- Supplied477k.py477516; eight slots478290.
- Forecast scale2/skew.0025/eight slots496928.
- Forecast scale2/skew.001/eight slots505225.

Zero skew was not automatically best: without the supplied forecast it made423550; with that forecast493447. Raising forecast scale or inventory skew often reduced profit. The closeout sweep found a useful local setting, not a universal optimum.

Queue throughput and a suitable inventory/forecast balance delivered the main improvements. Better prediction scores alone repeatedly failed to improve execution profit.

## Execution lessons and negative results

**Cancellation latency and queue value:** while an order ages, it remains live and trades. A cancel request leaves it fillable for5ms; its capacity remains reserved. Replacement has an additional acceptance delay and loses FIFO priority. No order can be made unfillable merely by “blocking” new submissions.

**Fixed lifetimes:**100ms expiry changed416852 to−150019;500ms expiry to58228. Inventory/imbalance-conditioned100ms expiry made391270. Reject these rules. Age alone discards useful queue positions; native expiry is unsupported.

**Predictive cancellation:** a first-fill-conditioned model identified later adverse-markout subsets, but two cancellation policies made416564/416715 versus416852. A short adverse markout does not price the lost future value of a quote.

**Blocking without cancellation:** inventory-aware and either-side adverse replenishment blocks made416444/416484. Adaptive size411311; follow1s forecast404033; fade397462; reversal383816; strict rearming355459; immediate observed shift detector412095. None beat416852. Preserving live FIFO avoids one cost, but withholding queue entry still loses useful fills.

**Maker accounting audit:** continuous private inventory parity, remaining-quantity checks and trade-derived cash matched the official engine. No catastrophic cash/ledger bug was found in the old baseline. Its20ms minimum repricing could leave adverse quotes exposed; removing that restriction selectively improved only1051 on the full tape.

**Shrinking:** a modify preserves FIFO but old quantity must remain reserved until acknowledgment. Partial fills can invalidate a pending shrink. REJECTED can mean a failed modification of a still-live order; do not delete that live order from the ledger. A bounded adaptive8–128lot policy made201322 versus206364; it was a risk/turnover tradeoff, not a PnL win.

Sources: [lifetimes](side-order-lifetimes.md), [predictive cancellation](side-predictive-cancellation.md), [passive policies](side-passive-signal-policies.md), [critical audit](side-critical-audit.md), [adaptive size/recovery](adaptive-size-passive-reversal.md).

## Takers and penalties

There is no theorem that takers cannot help. They compete with same-side maker reservations, pay spread/depth costs and must earn enough after5ms. Most simple round1 taker rules failed even before penalty.

On the old206364 maker, a throttled directional64lot IOC overlay made220673 with375437IOC lots. Its14309gain was mostly in the fitting half; later-half gain was2022 and one later segment weakened. Unconditional inventory IOC reduction made142979; adverse-conditioned reduction150725. Neither establishes an overlay improvement for the final505225 maker.

Penalty is10000×exact seconds with actual absolute inventory>100, independent of excess size. It is not10000per lot or rounded to whole seconds. A slight breach pays the same clock as a large breach; pending exposure is separately constrained.

Broad passive overflow failed decisively. Cap300 natural recovery produced around78–79million penalty. Large900lot policies with10/50ms grace and forced excess reduction also lost millions and often lost before penalty. Grace is not total breach duration: callbacks, cancel races, latency and incomplete exits extend it. Passive reversal does not guarantee fast recovery.

Use separate extrema I+B and I−S; never net opposing orders to claim headroom. Cancel/modify acknowledgment, not request time, releases exposure. Recompute emergency reduction after race fills. Penalty durations were independently reconstructed from fills in those studies.

Sources: [maker penalty](maker-penalty.md), [taker overlays](working-maker-taker-overlays.md), [timing](../timing-and-penalty.md). The timing proxy's older next-event activation wording is superseded by the exact engine description above.

## Round 2 startup plan

1. Read the new brief, competition settings and applicable agent procedures. Confirm instrument count, tick units, order types, latency, inventory/penalty rules and terminal scoring. Do not assume round1 parameters transfer unchanged.
2. Work on the assigned round2 branch. Keep new experiments in experiments/round_2/mkozlow/, curated Markdown in knowledge/round_2/mkozlow/ and reviewed standalone strategies in strategies/round_2/mkozlow/. Preserve frozen round1 sources/artifacts.
3. Hash the new raw data and simulator. Profile quality, event rate, missing-book states, spread, touch/deep depth, sizes, live cancellations, executions and volatility. Compare distributions and conditional relationships, not merely net price drift or mean price.
4. Replay the frozen505225 and simple zero-forecast control on the new tape using the official engine, after checking compatibility. Record actual execution roles, volume, inventory, queue use, cancel races, runtime and liquidation PnL. An R1 filename is historical evidence, not a promised R2 score.
5. Refit normalization and predictors on an early R2 window; purge crossing labels and reserve later periods before tuning. Match public feature definitions between fitting and deployment. Measure baseline-induced censoring and ownership effects.
6. Prioritize deeper-book imbalance, ownership-consistent executed flow, same-price arrivals and conditional continuation/reversal. Test volume-weighted fill profit, not only raw midpoint MSE. New nonlinear path models omitted deeper-book imbalance used by the successful supplied ridge; test that omission before adding more complexity.
7. Tune quantity/replenishment and inventory/forecast interaction with controlled ablations. Use several seeds/tapes if supplied. After repeated inspection, label the whole tape as tuning; do not rename reused periods “held out.”
8. Require a specific execution mechanism before retesting IOC, expiry or penalty. Preserve useful disabled mechanics and failed findings. Do not spend another round rediscovering that more cancellations, higher prediction accuracy or more inventory need not mean higher PnL.
9. Promote only an exact verified source, with hash, settings, data/window, command, actual results and limitations. Run local preflight and obtain server validation through the team's submission process. Keep a known successful final available.

Use uv run --locked and uv sync --locked for project execution. No global Python/pip, old demo simulator, raw tape slicing, silent upstream updates or automatic Git history changes. Curate valuable notes and retained strategies; raw experiments/logs remain experiments.

## Source map

- [Closing sprint and all30 candidate/control outcomes](side-distribution-and-path-sprint.md).
- [Earlier handoff](team-handoff.md): baseline206364 lineage, initial maker/taker/penalty experiments; historical best claims are superseded here.
- [Market profile](../market-research.md), [signals](../signals.md), [cancellations](../cancellations.md), [public replenishment](../replenishment.md).
- [Distribution-specific fitting](price-size-distributions.md), [round0 supplied evidence](round0-user-supplied-evidence.md).
- [Review of supplied execution/forecast research](side-execution-forecast-report-review.md); independent replay/paper claims were not all independently verified.
- Experiment plans, frozen sources, provenance, results, plots and datasets remain under experiments/. New layout did not move or delete older pre-layout directories.
