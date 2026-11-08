# Round 3 strategies (dataathletechamp)

**Final submission: `r3_follower_u7_flow_deepfv.py` (U7).** Private +589,202
(rank 34 of 53), validation 538,844, public R3 413,588. The lineage is
U1 → U4 → U6 → U7. Every other file is a research variant whose new mechanism
is off by default, so with defaults it behaves like its base. Details and
reproduction are in `knowledge/round_3/dataathletechamp/`; start with
`round3-retrospective.md`.

## Submission lineage

| File | sha256 | R3 A | R2 A | Validation B | Role |
|---|---|---:|---:|---:|---|
| `r3_informed_follower.py` | 1d3f2506 | 270,035 | 26,175 | 272,176 | U1: D1 informed follower |
| `r3_combined_regime.py` | 111fc83e | 269,288 | 63,328 | 258,688 | U3: regime gate + maker |
| `r3_alpha_follower_p1_sw3.py` | e4dfd2ce | 330,208 | 109,317 | 411,302 | U4: P1 ridge flip gate + A_SWEEP 3 |
| `r3_alpha_follower_p1_sw3_rlin0.py` | e3102973 | 357,488 | 107,856 | 415,828 | U6: gate refit on full R3 + R2, intercept 0 |
| **`r3_follower_u7_flow_deepfv.py`** | **d2a0fc9c** | **413,588** | **167,166** | **538,844** | **U7, final; private +589,202** |
| `r3_follower_u8.py` | 0075a2bf | 415,883 | 171,568 | – | U8: +1.2% over seven tapes, not uploaded |
| `r3_aged_maker_best.py` | 24fc7515 | 35,027 | – | – | U5 probe (aged maker alone); B result not reported |

## Research variants

| File | sha256 | Flag / note |
|---|---|---|
| `r3_alpha_follower.py` / `r3_alpha_follower_p1.py` | a01404e4 / 51ee7c75 | Alpha model, D1 / P1 defaults (`r3-alpha-model.md`) |
| `r3_alpha_follower_p1_sw3_refit.py` | 18a04575 | Pooled refits rlin / rlin0 / rsym (`r3-alpha-model.md`) |
| `r3_informed_follower_gate0867.py` | d4cd5fd0 | Follower with the 0.867/s regime gate |
| `r3_combined_tuned.py` / `r3_combined_regime_aged.py` / `r3_combined_maker_probe.py` | c8ef8b26 / 3fe5e25a / 627769c9 | Tuning, aged maker in the combined file, maker-only probe |
| `r3_aged_maker.py` | 3be6adc6 | Aged-queue maker research file (`r3-aged-maker.md`) |
| `r3_follower_deepfv.py` | 7b03aff4 | TRIG1 on the U4 base (`r3-follower-deepfv.md`) |
| `r3_follower_snipe.py` | b43aa1df | `SNIPE_ON` (`r3-follower-snipe.md`) |
| `r3_follower_probe.py` | 7deee03e | `PROBE_ON` (`r3-hidden-ioc-probe.md`) |
| `r3_follower_p1_aged.py` | 5a5ceffa | `MAKER_MODE` (`r3-follower-aged-overlay.md`) |
| `r3_follower_jumpguard.py` | b34b944e | `JUMP_GUARD`, on by default; a hedge (`r3-follower-jump-guard.md`) |
| `r3_follower_wallmid.py` | 976884ba | `WALL` (`r3-follower-wallmid.md`) |
| `r3_follower_u7_trig2.py` | 7c31aa76 | `TRIG2_ON` (`r3-follower-trig2.md`) |
| `r3_follower_u7_exits.py` | 2902ae83 | Exit flags (`r3-follower-exits.md`) |
| `r3_follower_revsleeve.py` | 1fd03a0e | `REVSLEEVE` (`r3-follower-revsleeve.md`) |
| `r3_follower_sleeves.py` | cc9e35d2 | `SLEEVES` (`r3-follower-sleeves.md`) |
| `r3_follower_evidence.py` | 963a1383 | `EVIDENCE` (`r3-follower-evidence.md`) |
| `r3_naive_flow_follower.py` | 330d8ee5 | `FAMILY` switch over eight simple families (`r3-naive-families.md`) |

## Round 2 starting seeds (frozen)

`r3_seed_actual_final_from_r2.py` (1d2c63ea) and
`r3_seed_clean_reference_from_r2.py` (10886b7d) are byte-identical copies of
R2 sources (`seed-manifest-v1.json`). On R3 A they lost 33–73k, so do not
reuse their trend skew. Do not replace frozen seed bytes.

## Checks

```bash
env -u VIRTUAL_ENV uv run --locked python -m tools.preflight $(pwd)/strategies/round_3/dataathletechamp/r3_follower_u7_flow_deepfv.py
env -u VIRTUAL_ENV uv run --locked exchange-simulator --strategy strategies/round_3/dataathletechamp/r3_follower_u7_flow_deepfv.py --backtest data/round3/round3_public.csv --log-dir <dir> --no-logs
```
