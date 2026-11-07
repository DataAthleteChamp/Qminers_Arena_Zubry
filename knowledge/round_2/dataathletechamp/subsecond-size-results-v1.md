# Smaller tickets do not beat the first risk-capacity record

Six predeclared, trusted c1-derived configurations were run on the same
registered Round2A/unchanged official SDK. **No new public record.**
The+18916 risk-capacity file remains retained; none of these replaces Final.

| Run ID | Quote target / fixed cap | Net PnL | Penalty | Interpretation |
|---|---|---:|---:|---|
| r2-fixed-q10-cap25-A-v1 | 10 /25 | -3211 | 0 | Joint size/exposure probe |
| r2-fixed-q25-cap40-A-v1 | 25 /40 | -11020 | 0 | Joint size/exposure probe |
| r2-fixed-q50-cap60-A-v1 | 50 /60 | -36475 | 0 | Joint size/exposure probe |
| r2-fixed-q100-cap100-A-v1 | 100 /100 | -99628 | 0 | Quote-only change versus q200/cap100 |
| r2-fixed-q200-cap35-A-v1 | 200 /35 | **+8831** | 0 | Cap-only change; simpler positive comparator |
| r2-fixed-q50-cap100-A-v1 | 50 /100 | -64284 | 0 | Quote-only change at common100 cap |

All completed successfully, input bytes unchanged,31--32s approximate measured
runtime. More filled orders do not imply more profit: q50/cap100 fills14955
orders but loses64284; the+18916 record fills10494.
These are target aggregate same-side remaining quantities, not a guarantee
that each request has exactly that many lots.

The fixed35 control explains152009 of improvement versus the R1 Final's
-143178. The adaptive full-risk policy still beats it by10085 on A.
Thus the entire162094 improvement cannot honestly be attributed to the
classifier. Capacity reduction is the dominant demonstrated mechanism;
incremental state-aware value is smaller and needs further transfer checks.
This is measured on consumedA, not a private gain forecast.

All probes keep R1 forecast, SKEW0.001, eight slots, queue controller and
IOC_MODE0. Only declared quote/cap settings and a runtime fixed-envelope
assertion differ. Same-side pending/cancel reservations remain counted.
No timed100ms exit or new learned fit was introduced.

## Do not confuse these with the supplied six-file pack

The read-only reviewer inspected all files in
`Zubry_Round2_Subsecond_Scalping_Research`, without executing/importing them.
Verdict **needs-evidence**; no blocking reservation defect found, but origin/
licence and source hashes were not authenticated by that reviewer.

Its s01/s02/s03 also change SKEW to0.015/0.010/0.005 and slots to4/5/6;
s04 changes SKEW to0.002. The supplied s00 and s05 display identical reference
parameters. Its "parameter isolation" claim is therefore not correct.
Our scores above are **not scores of those supplied bytes**:
we generated owned-source probes with original skew/slots deliberately held
constant. No supplied research helper or external strategy was executed.

The inherited10-lot minimum top-up means a q10 residual cannot be replenished
while active unless its deficit reaches10. Its nominal slot ceiling is not the
binding mechanism. Unused HYSTERESIS/MIN_REST/DEPTH_WEIGHT/FLOW_WEIGHT knobs
do not deactivate the still-used R1 Ridge.
One million lots is plausible turnover; one million independently profitable
fills is a different and unproved claim.

## Reproducibility and next rejection gate

Original successful commands:

```bash
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-fixed-q10-cap25-A-v1 --strategy experiments/round_2/dataathletechamp/subsecond-size-probes-v1/artifacts/q10_cap25.py --tape data/round2/round2_public.csv --stage user-small-quote-joint-config
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-fixed-q25-cap40-A-v1 --strategy experiments/round_2/dataathletechamp/subsecond-size-probes-v1/artifacts/q25_cap40.py --tape data/round2/round2_public.csv --stage user-small-quote-joint-config
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-fixed-q50-cap60-A-v1 --strategy experiments/round_2/dataathletechamp/subsecond-size-probes-v1/artifacts/q50_cap60.py --tape data/round2/round2_public.csv --stage user-medium-quote-joint-config
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-fixed-q100-cap100-A-v1 --strategy experiments/round_2/dataathletechamp/subsecond-size-probes-v1/artifacts/q100_cap100.py --tape data/round2/round2_public.csv --stage isolated-quote100-at-common-cap100
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-fixed-q200-cap35-A-v1 --strategy experiments/round_2/dataathletechamp/subsecond-size-probes-v1/artifacts/q200_cap35.py --tape data/round2/round2_public.csv --stage fixed35-exposure-vs-learned-risk-attribution
env -u VIRTUAL_ENV uv run --locked python experiments/round_2/dataathletechamp/evaluation-v1/run.py --id r2-fixed-q50-cap100-A-v1 --strategy experiments/round_2/dataathletechamp/subsecond-size-probes-v1/artifacts/q50_cap100.py --tape data/round2/round2_public.csv --stage isolated-quote50-at-common-cap100
```

`subsecond-size-probes-v1/manifest.json` holds every exact source hash.
Preflight/Ruff/strict mypy passed for all six files; six focused cancellation
and opposite-fill headroom tests passed. No raw logs/results/experiments were
committed. Repetition needs new immutable IDs.

Next test one-change inventory/forecast improvements against the fixed+18916
leader, not an endlessly retuned small-ticket menu. Inspect actual own FIFO
lot recycling and both IOC legs before treating outside-flow pair proxies as
executable trades. AUC, more orders or shorter holding is not the monetary
rejection gate; B/C remain UNKNOWN and no upload was performed.
