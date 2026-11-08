# Round 3 starting seeds, not selected submissions

The two Python files are byte-identical copies of retained R2 sources. Do not
replace frozen seed bytes; create a new named version for R3 changes.
seed-manifest-v1.json records both source paths and hashes.

Actual Final: one price/side, up to8same-price children,32-lot top-ups,
100shared risk envelope, skew0.05,10/60trend sign. R2A127559 and
providedexport80993, B/CroleUNKNOWN. Raw submitted code is intentionally untyped.

Clean reference: three32-lot price levels, FIFO deficit replenishment, finite
gap warned-side cap, clean-book-only EMAs. R2A104703, suppliedB47150.
This alternative still carries inventory and is not a guaranteed safe strategy.

Both passed local conservative preflight with the unchanged prior SDK.
Reconfirm the R3 contract, then run and freeze an actual baseline on new data.
Never relabel R2 scores as R3 evidence or use a prior tape as new validation.

```bash
env -u VIRTUAL_ENV uv run --locked python -m tools.preflight strategies/round_3/dataathletechamp/r3_seed_actual_final_from_r2.py
env -u VIRTUAL_ENV uv run --locked python -m tools.preflight strategies/round_3/dataathletechamp/r3_seed_clean_reference_from_r2.py
```
