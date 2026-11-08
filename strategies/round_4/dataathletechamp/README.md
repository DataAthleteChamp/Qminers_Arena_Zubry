# Round 4 strategies (dataathletechamp)

**Recommended final (11:53): Paweł Andrzejewski's `r3_final.py`.** Submission 71380109; the owner marks
it FINAL in the portal. A byte copy of the code is in `r4_final_pawel_r3_final.py` (sha256 of the copy
3c9eebf2). It is U7 plus the JumpBurst flip trigger.
- Validation 1,420,312; public R4 860,599.
- Private result pending.
- Why this one: `round4-retrospective.md` and `r4-validation-feedback.md` in `knowledge/round_4/dataathletechamp/`.

Every research file keeps its new mechanism behind flags that are off by default, so with defaults it
behaves like its base.

## Uploads and candidates

Official engine, penalty included. A = public tapes (6,000 s); B = validation (12,000 s).

| File | sha256 | R4 A | R3 A | R2 A | Validation B | Role |
|---|---|---:|---:|---:|---:|---|
| `r4_u1_follower_u7_baseline.py` | d2a0fc9c | 821,692 | 413,588 | 167,166 | 1,326,712 | U1: byte copy of the R3 final U7 |
| `r4_u2_trig2_ungated.py` | b239d85a | 886,626 | 415,404 | 159,515 | 1,343,784 | U2: + TRIG2 placement-class trigger (ungated, THR 0.95) |
| `r4_u3_trig2_gated.py` | c128a6e3 | 840,594 | 421,747 | 172,626 | – | gated TRIG2; not uploaded |
| `r4_u5_jump.py` | a3e72689 | 912,274 | 407,508 | 152,088 | – | U2 + jump-onset flip + 300-lot burst (K 3, spread ≤ 1); superseded |
| `r4_u6_jump_k4.py` | ca3e1b7c | 920,538 | 416,104 | 158,693 | 1,343,238 | U6: jump onset K 4, spread ≤ 2 |
| `r4_u7_cusum.py` | 72844dc5 | 932,031 | 419,798 | 159,710 | – | U6 + gated CUSUM trigger; not uploaded |
| `r4_u8_allin.py` | 058c74c9 | 948,126 | 421,985 | 158,885 | 1,318,169 | U8: U7 + 500-lot, 100 ms jump burst |
| `r4_u9_u6_burst.py` | c8c57f3b | 937,371 | 422,188 | 188,384 | 1,400,890 | U9: U6 + the colleague burst flip trigger |
| **`r4_final_pawel_r3_final.py`** | **3c9eebf2** | **860,599** | **419,806** | **180,827** | **1,420,312** | **U7 + JumpBurst flip trigger (Paweł); final** |

Public-tape gains shrank on validation. The R4 A selections (TRIG2, jump onset, all-in) gained about a sixth
as much on B. The simple burst trigger transferred.

## Research variants (flags off reproduce the base)

| File | sha256 | Flags / note |
|---|---|---|
| `r4_follower_hidden.py` | a94f9585 | `HID_*` hidden-IOC triggers; off = U2 (`r4-hidden-triggers.md`) |
| `r4_follower_deep8.py` | b62fad7b | `DEEP8_*`, `TRIG2_K8`; off = U2 (`r4-deep8-trigger.md`) |
| `r4_follower_jump.py` | 0a5b4144 | `JMP_*` jump-onset flip and burst; off = U2 (`r4-jump-onset.md`) |
| `r4_follower_alpha_r234.py` | a2509609 | gate refits `r234*`; defaults = U7 (`r4-alpha-refit.md`) |
| `r4_follower_trend.py` | 11c41a8c | trend rules; defaults reproduce the base (`r4-trend-rules.md`) |
| `r4_follower_reversal.py` | 3a0c9c5d | reversal triggers; defaults reproduce the base (`r4-reversal-triggers.md`) |

The following were tested only in uncommitted experiment copies; all were rejected and recorded in the
notes:
- anti-chop (`MINHOLD_MS`, `SPREAD_WAIT`, post-jump freeze);
- `TWAP_*`;
- the R4-native TRIG2 table;
- the skewed market maker;
- oracle imitation.

## Checks

```bash
env -u VIRTUAL_ENV uv run --locked python -m tools.preflight $(pwd)/strategies/round_4/dataathletechamp/r4_final_pawel_r3_final.py
env -u VIRTUAL_ENV uv run --locked exchange-simulator --strategy strategies/round_4/dataathletechamp/r4_final_pawel_r3_final.py --backtest data/round4/round4_public.csv --log-dir <dir> --no-logs
```
