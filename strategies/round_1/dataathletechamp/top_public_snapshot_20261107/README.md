# Published top-three snapshot before the next experiment wave

These are exact previously evaluated bytes on the ORIGINAL Round1 public tape.
Names encode public PnL, not private PnL, expected return or the competition z-score.
The snapshot is immutable; future improvements get a new file/snapshot, not a rename.

| File | Whole original-public PnL | Later validation | Reserved check |
|---|---:|---:|---:|
| `pnl_344438_ridge_queue_hybrid.py` | 344438 | 106580 | 104829 |
| `pnl_343269_inventory_queue_maker.py` | 343269 | 106617 | 106725 |
| `pnl_333188_depth_inventory_maker.py` | 333188 | 105381 | 102832 |

All three: penalty0, actual and joint reserved exposure <=100, local preflight,
strict typing and exact cash/inventory/PnL reconciliation passed.
The ridge training-label cutoff was corrected before this snapshot.
The simpler queue file remains the earlier validation-selected preference.

See `knowledge/round_1/dataathletechamp/top-three.md` for hashes and limits.
Server sandbox acceptance and manual Final selection are NOT performed here.
Do not use mirrored stress-data scores or independent C++ estimates as these scores.
