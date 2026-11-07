# Top three retained Round 1 candidates

**Recommended:** `inventory_queue_maker.py` (selected before final checks).
**Highest observed original-public PnL:** `ridge_queue_hybrid.py` (cutoff-corrected).
They differ by only1169 whole-public PnL, about0.34%. Queue maker is simpler and won both later checks; the private ranking remains unknown.

| File | Whole public PnL | Selection validation | Reserved check | Runtime | Bytes |
|---|---:|---:|---:|---:|---:|
| [ridge_queue_hybrid.py](../../../strategies/round_1/dataathletechamp/ridge_queue_hybrid.py) | 344438 | 106580 | 104829 | 56.2s | 6402 |
| [inventory_queue_maker.py](../../../strategies/round_1/dataathletechamp/inventory_queue_maker.py) | 343269 | 106617 | 106725 | 38.8s | 4936 |
| [depth_inventory_maker.py](../../../strategies/round_1/dataathletechamp/depth_inventory_maker.py) | 333188 | 105381 | 102832 | 35.7s | 4610 |

All three: penalty0; maximum actual and joint reserved inventory100; no time outside100. 90,000 adverse state transitions across the three original finalists plus the corrected hybrid tests passed. Every final source passed local preflight, Ruff and strict typing. Transparent executions independently reconciled cash/position and exact PnL.

Measured CLI child peak RSS was about56-60MB on this machine. This is not certification of the remote1CPU/2GB/15minute sandbox.

## Exact hashes

- `strategies/round_1/dataathletechamp/ridge_queue_hybrid.py`: `617125719135fdf27f7f2535299550c551173575b8e5fcc02065db6660744622`
- `strategies/round_1/dataathletechamp/inventory_queue_maker.py`: `1102cf8b355014afc7ff47553f60d4cecb6298d0f3b38d7c177843519481e08f`
- `strategies/round_1/dataathletechamp/depth_inventory_maker.py`: `b70527ed8f37520010fd32432c48a633f8c1e08e68ce19b2dd07bacdca940468`

Data SHA-256: `362e8208be1eeec32ad190d097774e26448f0d5149575a8e1b1efd1db1735940`.
Official source SHA-256: `6dba6395cd6104e47132c53a251f2f0781b4d66d910c34e0025cc7843fbeadb5`.

## Reproduce

Use a NEW output directory; do not overwrite earlier logs:

```bash
uv run --locked python -m tools.preflight strategies/round_1/dataathletechamp/inventory_queue_maker.py
uv run --locked exchange-simulator --strategy strategies/round_1/dataathletechamp/inventory_queue_maker.py \
  --backtest data/round1/round1.csv \
  --log-dir experiments/round_1/dataathletechamp/new-reproduction/logs --no-logs
```

## Upload discipline

These are validated local candidates, not authenticated human approval or server acceptance. Upload only one reviewed standalone .py. Check the website error/static/runtime result and confirm the intended **Final** selection. Do not upload experimental wrappers or mistake the mirrored stress PnL for the original score. No auto-upload was performed.

Raw experiments remain local/uncommitted per AGENTS.md; retained code and curated research are checkpointed on `round_1/dataathletechamp`, not automatically merged/pushed.
