# Round1 Final evidence: public505225, private504903

Exact Final source SHA256:
`c1f194668ec83e94bf522e749ce36d266caeedb9244506ede2adeee68e8e3667`,8419bytes.
The missing original EOF newline is preserved; never format frozen submitted bytes.
No IOC enabled, same-side pending reserve100, requested target200,8slots,
skew0.001, corrected frozen0.5s predictor. Source binding is HUMAN confirmation;
the archives name classMaker but do not embed code/data fingerprints.

| Field | Official public archive | Official private archive |
|---|---:|---:|
|PnL|505225|504903|
|Filled orders|19581|19267|
|Executed lots|2020098|2008486|
|Cash|-497675|-31804|
|Ending inventory|100|54|
|Depth liquidation mark|10029|9939.018518518518|
|Penalty|0|0|
|User fill matches|32314|31921|
|Incidental user-as-taker lots|175|98|

Both downloaded trade ledgers independently reconcile cash, signed inventory,
filled-order counts, executed volume and official PnL. Max abs inventory after
each user match is100. LIMIT activation can consume market liquidity after5ms;
those tiny user-taker quantities are not self-trading or a deliberate IOC policy.

Public:`-497675+100*10029=505225`.
Private:`-31804+54*9939.018518518518=504903`.
Do not round the private weighted liquidation mark to an integer or use midpoint
valuation. Negative cash is not a loss without the inventory liquidation value.

## Preserved inputs

`results_final_round1.zip` is the PUBLIC Final sandbox/replay archive:
74246594bytes, SHA256
`12e7c1166206c0ba6febf8bf626cf94053ef0b363d9c1220920881087893e498`.

`results.zip` is the supplied PRIVATE Final archive:
73983043bytes, SHA256
`f75b5a70a7dbcd7c09f113ee7383500b8413fe12756414a974bfa62a2fbba779`.

Each contains7 members:book_deltas,events,trades,metadata,result,run,pnl.
Streaming reads validated ZIP CRC and recorded every member's exact SHA/size.
Original ZIP bytes remain unchanged in the R1 checkout; raw logs are not committed.
The curated bundle contains byte-identicalpublic/private result andmetadataJSON,
source, member catalogue/provenance and a dashboard rank observation.

Public input tape SHA256:
`362e8208be1eeec32ad190d097774e26448f0d5149575a8e1b1efd1db1735940`.
The raw PRIVATE input CSV isNOT present. These are strategy-influenced result
logs, not an interchangeable private replay tape. Never replay507393 on those
logs and call the output its private performance.

## Actual audit command

```
uv run --locked python experiments/round_1/dataathletechamp/postround-archive-audit-v1/audit.py
```

Passed for BOTH archives. Raw audit code/output history stays in the retained
R1 workspace. The bundle'sprovenanceJSON names all hashes and binding limitations.
Leaderboard rank14 and504903 agree with the participant's supplied dashboard;
the run timestamp has no declared timezone, so no wall-clock inference is made.
