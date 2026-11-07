# Maciej505225: reproduced, reviewed and ready for manual checking

Current observed original-public record: **505225, penalty0**.
Easy file: `strategies/round_1/dataathletechamp/pnl_505225_maciej_ridge_maker.py`.
This is Maciej's supplied source, not an improvement invented by this session.
The earlier496k file actually reproduced496928.

Both use our corrected frozen0.5s predictor,100 side-wise joint risk,200 target,
8 FIFO slots, no IOC. The505225 source differs by inventory skew0.001.
Public tape SHA256:
`362e8208be1eeec32ad190d097774e26448f0d5149575a8e1b1efd1db1735940`.
505225 source SHA256:
`c1f194668ec83e94bf522e749ce36d266caeedb9244506ede2adeee68e8e3667`.

Actual command:

```
uv run --locked python experiments/round_1/dataathletechamp/evaluation/run.py --id maciej505-full-v1 --strategy macieiej_505kpln.py --tape data/round1/round1.csv --stage original-full-teammate-urgent-reproduction
```

Reproduced505225,19581 filled orders,2020098 lots,60.9s locally.
Independent observer:

```
uv run --locked python experiments/round_1/dataathletechamp/evaluation/trace_final.py --file macieiej_505kpln.py --expected-pnl 505225 --id trace-maciej505-v1
```

Reproduced505225 again. Cash-497675, inventory100, liquidation mark10029:
`-497675+100*10029=505225`. Actual and all-pending extrema±100 at every
callback; zero time above100, zero rejected messages. Boundary time50.8%.
Ruff, strict types and conservative preflight passed for the exact retained copy.
Server sandbox/Final selection remain manual; private PnL is unknown.

## Quick neighbours: no550k record found yet

All twelve actual full runs penalty0. More slots plateau:

| Change from505225 | Actual full PnL |
|---|---:|
|skew0,8/16 slots|493447|
|skew0.0005,8/16/32 slots|499060|
|skew0.0015,8 slots|500105|
|same skew0.001,16/32 slots|505225|
|16/32 slots, minimum top-up1|505011|
|16 slots, price scale2.25|499308|
|16 slots, price scale2.5|488504|

The prior urgent reversal wave also failed to add>5000:
control477516; reversal40/80:448029/469117; continuation40/80:470840/475206;
flow agreement40/80:473028/478957; reversal price0.15/0.30:478880/478328.
Every outcome is retained. No phantom550k/650k claim.

Last registered8-arm cheap test changes only width, forecast clipping or a small
QI blend against exact505225. They are not records before actual results.
All public data/windows are consumed optimisation evidence. No future path lookup,
private feedback tuning, evaluator edits, raw data mutation or risk bypass.
