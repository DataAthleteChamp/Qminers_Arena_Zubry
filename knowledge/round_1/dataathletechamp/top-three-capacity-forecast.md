# 477516 current record: exact files for manual checking

Current highest observed ORIGINAL Round1 public PnL: **477516, penalty0**.
File: `strategies/round_1/dataathletechamp/pnl_477516_ridge_price_maker.py`.
Compared with earlier344438, this is+133078 (+38.6%) on this public tape,
NOT an expected private gain. The575k anecdote remains unverified/unbeaten here.

Immutable three-file folder:
`strategies/round_1/dataathletechamp/top_public_snapshot_20261107_477516/`.

| Exact source | Full PnL | Later4800 | Later8400 | Source SHA256 |
|---|---:|---:|---:|---|
|ridge-price scale2|477516|148043|145786|023378dc1df709ef266134b8faa272cc19c089aa58b190c7d838fcc821d60d5a|
|ridge-price scale3|473373|147860|142600|32ee0fac39acb5f6d3a75d405e479dae02a51e4bba43d7b20f3916642279fe0c|
|nonblocking flow0.25|460752|141050|143411|75cead8a0471f3a2fe74db2ddbb5f480aeb706b2a62f6ace672adbaaf7a1c5ce|

Original tape SHA:
`362e8208be1eeec32ad190d097774e26448f0d5149575a8e1b1efd1db1735940`.
First4800s ridge fitting uses actual label timestamps strictly before4800s.
Chronological trading blocks were repeatedly used and are development/robustness
checks, not new untouched validation. No private score orP(win) is inferred.

## What changed and why

Target200 uses full SAFE directional capacity, not200 inventory. Bids/asks may
reverse position from-100 to+100 or vice versa but cannot breach either extreme.
Up to3 FIFO-preserving orders/side refill capacity; all pending/cancel lots count.
Inventory price skew0.005 outperformed0.01/0.001/zero in the selected ladder.

The richer corrected0.5s forecast was useful for PRICE control rather than its
earlier small size tilt, which often clipped at headroom. Scale2 is a tick-rounded
control parameter, NOT a claim of twice predictive accuracy. Scale3 had fewer
fills and more boundary time; scales4/6 lost strongly in first-stage checks.

Nonblocking admissions propose new quotes while old requests/cancels are pending
ONLY if their full remaining quantities leave real capacity. No cancel credit,
netting opposite reserves, self-match or evaluator modification.

## Independent exact accounting

Transparent official-engine observers reproduced every top-three total and checked
actual inventory plus same-side remaining at every private/public callback.
Every source had maximum actual and reserved exposure100, time above100=0,
penalty0, zero rejected messages and unchanged hashes.

For477516: cash-525384, inventory100, mark10029, giving
`-525384+100*10029=477516`.This record has**21236** filled orders,
34554 matches and2232620 lots.
Capture1166006.5-carry688440.5-terminal50=477516 against an approximate50ms
reference: an accounting identity, not independent alpha.

Boundary occupation is42.5% for scale2 and47.4% for scale3. Larger size raises
holding exposure despite the unchanged cap. Sampled one-second drawdown is not
the all-event drawdown; server CPU/memory/static validation is still required.

## Completed checks / exact commands

`make check`: passed lint/format, strict types,25 tests, preflight and unchanged
official SDK/material fingerprints. New source families separately passed strict
source typing, Ruff/preflight;13 focused capacity cases and5 mixed IOC/SDK cases passed.

Actual record command:

```
uv run --locked python experiments/round_1/dataathletechamp/evaluation/run.py --id rp5-ridge20-full --strategy experiments/round_1/dataathletechamp/ridge-price-v5/variants/ridge20.py --tape data/round1/round1.csv --stage consumed-original-full-ridge-price-recheck
```

Actual reproduction:

```
uv run --locked python experiments/round_1/dataathletechamp/evaluation/trace_final.py --file experiments/round_1/dataathletechamp/ridge-price-v5/variants/ridge20.py --expected-pnl 477516 --id trace-ridge20-v1
```

Both passed at477516. Corresponding IDs:rp7-ridge3-full/trace-ridge3-v1,
qa6-reserved-nonblocking-full/trace-nonblocking-v1.
Later IDs:rp5-ridge20-later4800/later8400,rp7-ridge3-later4800/later8400,
qa6-nonblocking-later4800/later8400. All later runs penalty0.

For a fresh clone, reproduce with the retained file and actual organiser CLI:

```
uv run --locked python -m tools.preflight strategies/round_1/dataathletechamp/pnl_477516_ridge_price_maker.py
uv run --locked exchange-simulator --strategy strategies/round_1/dataathletechamp/pnl_477516_ridge_price_maker.py --backtest data/round1/round1.csv --log-dir experiments/round_1/dataathletechamp/your-fresh477516-check/logs --no-logs
```

Human upload/Final selection only. Earlier snapshot/files are preserved.
New supplied playbooks are generating an ownership-consistent external-flow
ablation; until it is executed/reconciled it is NOT a new record.
