# Round 4 validation (server tape B) feedback log

Final = the latest successful upload. Cancelling a running or waiting
submission is now possible in the portal, and new submissions show their
filename. Exports are archived locally under
`experiments/round_4/dataathletechamp/20261108-r4-validation-feedback-001/`.

| Upload | File (sha256 prefix) | R4 public A | Validation B | Notes |
|---|---|---:|---:|---|
| U1 | `r4_u1_follower_u7_baseline.py` (d2a0fc9c, = R3 final U7) | 821,692 | **1,326,712** | penalty 0; ordinary seconds +1,198.7k (99.9/s); 34 jump seconds +128.0k (23 positive); 19/20 positive 600 s blocks |

The validation tape is momentum-friendly like R4 public. B over A is 1.61×
for the same file (R3: 1.30×).

## Neighbourhood of U8 on R4 (`20261108-r4-neighbourhood-001`)

U8 makes 821,664 on R4, 415,883 on R3 and 171,568 on R2. One change at a
time (R4 / R3 / R2):

| change | R4 | R3 | R2 |
|---|---:|---:|---:|
| flip margin 0.6 | 792k | 392k | 133k |
| flip margin 0.8 | 821k | 392k | 161k |
| flip margin 1.3 | 782k | 382k | 154k |
| flip margin 1.6 | 729k | 374k | 140k |
| A_SWEEP 2 | 821k | 402k | 158k |
| A_SWEEP 4 | 822k | 419k | 173k |
| flow 400 | 823k | 389k | 159k |
| flow 900 | 822k | 412k | 157k |
| TRIG1 FV 0.35 | 826k | 405k | 178k |
| TRIG1 FV 0.75 | 816k | 383k | 171k |

- HOLD_S 10, 15 and 20 are identical to each other (R4 822,094): the hold
  deadline almost never binds.
- Flip margin 1.0 stays best on R4.
- No single parameter gives a material gain. Improvements must be
  structural.
