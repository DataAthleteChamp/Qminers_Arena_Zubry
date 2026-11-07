# Round2: clean workspace and bounded opening plan

## Closed-round handoff

Read [round2-retrospective.md](round2-retrospective.md),
[round2-decision-log.md](round2-decision-log.md),
[round2-workspace-lessons.md](round2-workspace-lessons.md) and
[round2-to-round3.md](round2-to-round3.md).
The actual humanFinal is now frozen under
submissions/round_2/dataathletechamp/final_actual_20261108:
public127559; suppliedserverexport80993, penalty0, **B/CstageUNKNOWN**.
Do not confuse it with earlier47k/121k files.

Worktree:`/Users/jakubpiotrowski/PycharmProjects/Qminers_Arena_Zubry_Round2`.
Branch:`round_2/dataathletechamp`. Use uv only and read `rounds/r2/BRIEF.md`.
Main now has the curated Round1 lessons, actual Final/public-private evidence,
and registered R2A gzip/manifest/hash.
The originalQminers_Arena_Zubry directory remains on the R1 branch unchanged:
raw185-run ledger, archives, logs, failed setup/tests and nested worktrees remain.
No destructive cleanup or history rewriting was performed.

## Seed registry

| File under strategies/round_2/dataathletechamp | Origin / limitation |
|---|---|
|clipped_ridge_seed_from_r1.py|Exact507393 R1 public candidate; privateUNKNOWN; R1-fitted coefficients|
|final_maker_seed_from_r1.py|Exact505225 public /504903 private human Final; R1-fitted coefficients|
|inventory_queue_seed_from_r1.py|Exact449661 R1 no-learned-forecast control; current book/inventory only|

All are carry-forward seeds, NOT selected Round2 strategies. Their actual A
scores are now -146085/-143178/-168655, all penalty0. The Final seed loss was
exactly reproduced; no-order control is0. See the new execution note below.
The learned arrays,
normalisers, inventory cap and5ms assumptions must be reviewed against the NEW
round data/mechanics. Do not overwrite the R1 frozen evidence.

## DataA/B/C protocol

Participant-reported change: uploads provide feedback on a second tapeB; final
private tapeC remains hidden. Exact organisers' implementation isUNKNOWN.
Contract-v1 preserves the pre-release state; contract-v2 registers A separately
from still-UNKNOWN B/C identities and historical mechanics.

Fit/develop onA; preserve actual future-label cutoff and current-only signals.
Freeze up to3 candidates before consultingB. IfB is repeatedly used to rescue
thresholds, it is selection/training feedback, not untouched validation.
Never fit on B result logs as if they were a complete raw tape, or infer C profit
from public bootstrap. A's actual hash is registered; any new organiser mechanics
and B/C details remain prerequisites for stronger official-release claims.

## Current research checkpoint

**Validation overrides the public-only record:** risk/Ridge+18916A failed
onB(-229513). ConservativeB-10781; originalGridB+28827isbestprovidedexport,
supersededbyowner-reportedgap/FIFOB+43782.
The typedGridport reproducesA+91025/R1+149143, but uploadedsourcehash/
coefficientfitprovenance are not authenticated by the three-file exports.
Readcontract-v3 andthevalidationgap beforechoosingFinal.

Latestreproducedpublicchallengers:FIFO+100195 andFIFO+visible-gap-protection
+103998, both penalty0. Files:r2_grid_fifo_public_100195.py and
r2_grid_gap_public_103998.py understrategies/round_2/dataathletechamp.
TheFIFO-onlyBscoreisUNKNOWN; latestownerconfirmsthegap/FIFOfilegotB+43782
andisnowFinal. OriginalGrid+28827remainsapreservedcomparison.
Explorer islive at http://127.0.0.1:8050/ forlocalreferenceA only.

Latestownerupdate:gap/FIFO103998receivedreportedB+43782andisnowFinal;
7sharedslotsremain. Isolatedinside-spreadrepairarms losttotheAcontrol,
so theyareparked ratherthansubmitted. Seespread-repair-results-v1.md.

Latequeue/capacitywave:largerquotesandmorechildrenfailedtoimproveA.
CleanNORMAL-onlyEMAreference104703wasexactlyreproduced(+705only);
newBscoreUNKNOWN,notFinal. Seelate-queue-capacity-results-v1.md.

LatestconfirmedB:clean-reference47150,markedFinalbyowner.
Finalstructuraltrial1x96haspublic121235exactlyreproduced, BUNKNOWN:
r2_trial_grid1x96_public_121235.py. Do notreplace47150unlessactualBimproves.
Ownerreportsactualextendedclose00:15; dashboardauthorityoverridesoldschedule.

| Note | Purpose |
|---|---|
|[market-regimes.md](market-regimes.md)|Same-method R0/R1/R2 statistics, tail attribution, signal stability and null5ms hazards|
|[execution-diagnostics.md](execution-diagnostics.md)|Actual seed losses, exact reproduction, filled-lot markouts, cancellation races and causal fill-state falsification|
|[source-audit-theory-v1.md](source-audit-theory-v1.md)|Six verified primary-source sections, transfer limits and up to3 falsifiable mechanisms|
|[source-audit-empirical-and-references-v1.md](source-audit-empirical-and-references-v1.md)|Newer abstract-only claim limits, pinned HftBacktest/proxy execution and IMCwallmid audit|
|[jump-risk-model.md](jump-risk-model.md)|Independent causal risk-classification screen, calibration caveats and frozen monetary overlay ladder|
|[risk-overlay-results-v1.md](risk-overlay-results-v1.md)|First positive public record+18916, exact reproduction, source hash and failed width comparator|
|[subsecond-size-results-v1.md](subsecond-size-results-v1.md)|Six frozen size/cap probes, five losses, fixed35+8831 and supplied-pack confounding|
|[validation-gap-v1.md](validation-gap-v1.md)|ActualthreeBresults, cash/wealthreconciliation, observedlimits, Gridcode/R1test andlocalexplorer|
|[order-reactions-and-gaps.md](order-reactions-and-gaps.md)|Four verified source scopes, visible/censored gaps, no newsoracle and actual shrinkAPIrace tests|
|[grid-ablation-results-v1.md](grid-ablation-results-v1.md)|Quantity/target/recovery versus FIFO/gap experiments; public103998 is not a Bscore|
|[spread-repair-results-v1.md](spread-repair-results-v1.md)|LatestreportedB43782, inside-spread disproof and limited nextqueue/reference test|
|[late-queue-capacity-results-v1.md](late-queue-capacity-results-v1.md)|Failed larger-size/slot tests, reproduced clean-reference104703 and strict B/Final gate|
|[final-structural-results-v1.md](final-structural-results-v1.md)|Last four structural controls, reproduced1x96public121235 and unknownBtrial|
|[data-provenance.md](data-provenance.md)|Preserved actual A bytes and shared lossless archive|

The supplied root ROUND2_STATISTICAL_ANALYSIS.md and
ROUND2_MARKET_MAKING_RESEARCH.md remain preserved in the old R1 archive.
They are independent reference memos, not authenticated evaluator results or
verified strategy packages. Two source waves and our independent risk screen
are now complete; quantity arms earned+12935/+18916, width lost-70803.
The+18916 standalone public research file is retained understrategies/round_2/
dataathletechamp/r2_public_research_risk_capacity_18916.py, exactly reproduced.
It is not a selected/uploadedFinal. New bounded scalping/regime/IOC probes follow.
AUC, lower drawdown and external proxyPnL are not the raw score.

## First30-minute work block after data release

1. Register actual dataset path/hash/columns, number of instruments, timestamps,
   durations, missing sides, spread/depth/quantity tails and delivery latency.
2. Run the carried507393 seed and no-learned control on SAMEA and unchanged SDK.
   Independently reconcile cash, fills, inventory, pending side limits and markout.
3. Pick at most3 causal hypotheses from NEW observed differences. Price/sizing/
   queue effects must beat the fixed-large-size control; do not start with IOC,
   deep nets, arbitrary anchors or a many-parameter search.

Assign pairA=diagnosis/implementation and pairB=execution/risk/validation.
One human submits, another checks exact file hash/Final flag; name a backup.
Use unique run IDs underexperiments/round_2/dataathletechamp/.

## Official commands after REALA is registered

Use the registered actual A, not an R1/synthetic tape:

```
uv run --locked python -m tools.preflight strategies/round_2/dataathletechamp/clipped_ridge_seed_from_r1.py
uv run --locked exchange-simulator --strategy strategies/round_2/dataathletechamp/clipped_ridge_seed_from_r1.py --backtest data/round2/round2_public.csv --log-dir experiments/round_2/dataathletechamp/your-unique-seed-run/logs --no-logs
```

Before running, record source/data/SDK hashes, hypothesis and rejection rule in
the experiment directory; afterward record actual result, failures and runtime.
Historical tools.run_experiment writes legacyresearch/experiments and is NOT the
new layout. Use the direct official CLI with explicit output here; do not silently
reuse the hard-coded R1 runner. Missing data is an error, not a fake baseline.

Keep raw tapes, all experiments and logs local/ignored; commit curated lessons
and reviewed standalone sources at least every30minutes. Human integration/release.
Local checks do not replace server sandbox confirmation. No upload was performed.
