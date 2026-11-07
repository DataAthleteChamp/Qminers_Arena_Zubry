# Registered Round2 public development tapeA

Participant source:
`/Users/jakubpiotrowski/PycharmProjects/Qminers_Arena_Zubry/data/round2/round2_public.csv`.
Canonical local working file:`data/round2/round2_public.csv`, unchanged bytes.

- Raw78512311bytes, SHA256
  `88ff641e962540c66fa1cc4a3547585d31838d0929340150690cabb4f3cfb9f4`.
- Sharedlossless`data/round2/round2_public.csv.gz`,18092928bytes, SHA256
  `d4c97820dd188e9365c658a19a08908c132d605084736116811341bac195c495`.
-2193064 event rows,0.000067 through5999.996013 seconds.
-1123282 inserts:534901 resting buys,534958 resting sells,26643 IOC buys,
  26780 IOC sells.1069782 cancellations.
- Every row audited: exact7-column schema, ordered unique timestamps,
  unique insert IDs, valid sides/lifespans, positive integer inserted prices/volumes.
- Time is seconds on CSV, integer microseconds in SDK. Price/lots are anonymous
  integer units, not authenticated currency/ticker/contract multipliers.

Lossless archive decompression reproduces the RAW SHA exactly. The original source
and working CSV were rehashed after registration and remain unchanged.
Manifest:`data/round2/round2_public_manifest.json`; hashes:`round2_public.sha256`.
No feedbackB or final-privateC raw tape is present.

## Restore working bytes from a fresh clone

```
uv run --locked python - <<'PY'
import gzip, hashlib, shutil
from pathlib import Path
p = Path("data/round2/round2_public.csv")
with gzip.open("data/round2/round2_public.csv.gz", "rb") as source, p.open("xb") as target:
    shutil.copyfileobj(source, target)
if hashlib.sha256(p.read_bytes()).hexdigest() != "88ff641e962540c66fa1cc4a3547585d31838d0929340150690cabb4f3cfb9f4":
    raise RuntimeError("Decompressed dataset hash mismatch")
PY
```

The archive is retained; exclusive output creation refuses to overwrite an existing
CSV. Compare an existing file to the manifest instead. Never edit either raw copy.

Registration actually run:

```
uv run --locked python experiments/round_2/dataathletechamp/intake-v1/register.py
```

That raw registration script remains in the local contributor experiment folder.
Full descriptiveA analysis consumes distribution information; future strategy
validation does not become a pristine holdout merely by slicing this tape later.
