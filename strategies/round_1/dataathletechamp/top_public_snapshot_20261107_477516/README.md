# Current verified top-three ORIGINAL-public snapshot

| File | Full public PnL |4800-8400 trading|8400-12000 trading|
|---|---:|---:|---:|
|pnl_477516_ridge_price_maker.py|477516|148043|145786|
|pnl_473373_ridge_price3_maker.py|473373|147860|142600|
|pnl_460752_nonblocking_flow_maker.py|460752|141050|143411|

All exact bytes reproduced with independent cash/inventory accounting,
every-callback actual+reserved extrema±100, penalty0 and zero rejections.
Later runs replay original prefixes with prior book warmup and flat trading
activation. Their PnLs do not sum into a whole score. All blocks are now consumed.
The two ridge-price files use the corrected frozen0.5s past-fit predictor.
IOC is disabled; the sparse taker tests did not improve passive continuation.

See `knowledge/round_1/dataathletechamp/top-three-capacity-forecast.md`.
Upload only ONE Python file manually; not the folder, ZIP, research or tools.
Local validation is not server sandbox certification or private-profit proof.
This snapshot is immutable. Future records receive NEW files/snapshots.
