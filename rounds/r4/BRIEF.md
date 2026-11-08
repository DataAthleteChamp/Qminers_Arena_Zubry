# Round 4

- Schedule: 07:00–12:00 Sunday; confirm the dashboard deadline and quota
  (10 uploads, one in flight).
- Public data: `data/round4/round4_public.csv`, registered in
  `data/round4/round4_public_manifest.json`. The raw CSV stays local; the
  gzip archive is committed. sha256 61c0b6d1…8a56, 2,398,520 rows, 6,000 s.
- Validation B and private C tapes are not provided.
- No leaderboard before closing. Freeze on validated evidence and known risk.
- Weight 1.2 applies to PRIVATE normalized PnL, not public raw profit.
- Portal features added in Round 4 (organizer announcement, 07:10):
  - A running or waiting submission can be cancelled voluntarily, for
    example a wrong file or a slow result near the deadline. A cancelled
    run is presumably not a successful upload, so the final should stay the
    latest successful upload (`competition.json`); verify on the dashboard.
  - The submissions table shows the uploaded filename for new submissions.
    Use descriptive, versioned filenames (e.g. `r4_u3_<mechanism>.py`) so
    the final can be identified without a hash.
- Rules carried over from Round 3:
  `knowledge/round_3/dataathletechamp/round3-to-round4.md`.
