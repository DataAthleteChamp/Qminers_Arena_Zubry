# Round2: clean workspace and bounded opening plan

Worktree:`/Users/jakubpiotrowski/PycharmProjects/Qminers_Arena_Zubry_Round2`.
Branch:`round_2/dataathletechamp`. Use uv only and read `rounds/r2/BRIEF.md`.
Main now has the curated Round1 lessons and actual Final/public-private evidence.
The originalQminers_Arena_Zubry directory remains on the R1 branch unchanged:
raw185-run ledger, archives, logs, failed setup/tests and nested worktrees remain.
No destructive cleanup or history rewriting was performed.

## Seed registry

| File under strategies/round_2/dataathletechamp | Origin / limitation |
|---|---|
|clipped_ridge_seed_from_r1.py|Exact507393 R1 public candidate; privateUNKNOWN; R1-fitted coefficients|
|final_maker_seed_from_r1.py|Exact505225 public /504903 private human Final; R1-fitted coefficients|
|inventory_queue_seed_from_r1.py|Exact449661 R1 no-learned-forecast control; current book/inventory only|

All are carry-forward seeds, NOT Round2-validated strategies. The learned arrays,
normalisers, inventory cap and5ms assumptions must be reviewed against the NEW
round data/mechanics. Do not overwrite the R1 frozen evidence.

## DataA/B/C protocol

Participant-reported change: uploads provide feedback on a second tapeB; final
private tapeC remains hidden. Exact organisers' implementation isUNKNOWN.
Contract-v1 records this separately from historical Round1 public-only uploads.

Fit/develop onA; preserve actual future-label cutoff and current-only signals.
Freeze up to3 candidates before consultingB. IfB is repeatedly used to rescue
thresholds, it is selection/training feedback, not untouched validation.
Never fit on B result logs as if they were a complete raw tape, or infer C profit
from public bootstrap. The next organiser brief and realA hash are prerequisites.

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

ReplaceROUND2_PUBLIC.csv by the actual downloaded filename, not an R1/synthetic tape:

```
uv run --locked python -m tools.preflight strategies/round_2/dataathletechamp/clipped_ridge_seed_from_r1.py
uv run --locked exchange-simulator --strategy strategies/round_2/dataathletechamp/clipped_ridge_seed_from_r1.py --backtest data/round2/ROUND2_PUBLIC.csv --log-dir experiments/round_2/dataathletechamp/your-unique-seed-run/logs --no-logs
```

Before running, record source/data/SDK hashes, hypothesis and rejection rule in
the experiment directory; afterward record actual result, failures and runtime.
Historical tools.run_experiment writes legacyresearch/experiments and is NOT the
new layout. Use the direct official CLI with explicit output here; do not silently
reuse the hard-coded R1 runner. Missing data is an error, not a fake baseline.

Keep raw tapes, all experiments and logs local/ignored; commit curated lessons
and reviewed standalone sources at least every30minutes. Human integration/release.
Local checks do not replace server sandbox confirmation. No upload was performed.
