# Organiser's post-competition data release

After the final results (8 Nov 2026) the organisers released every round's hidden data:
- the validation and private tapes;
- the hidden fair price;
- the market-regime timings.

We store gzip copies here. The original `market_data.zip` stays local as `data/market_data.zip`; its
sha256 is in [`manifest.json`](manifest.json).

| Round | Tapes (`*.csv.gz`) | Fair price | Regimes |
|---|---|---|---|
| 1 | private (public: `data/round1/round1.csv.gz`) | public, private | none (one regime) |
| 2 | validation, private (public: `data/round2/round2_public.csv.gz`) | public, validation, private | public, validation, private |
| 3 | public, validation, private | public, validation, private | public, validation, private |
| 4 | validation, private (public: `data/round4/round4_public.csv.gz`) | public, validation, private | public, validation, private |

## File formats

- **Tapes:** `Time,Operation,OrderId,Side,Volume,Price,Lifespan`, the simulator's input.
  - Validation and private tapes cover 12,000 s.
  - Public tapes cover 6,000 s, except Round 1's, which covers 12,000 s.
  - The released public tapes are byte-identical to the ones we used during the rounds.
- **Fair price** (`*.fair.csv.gz`): `Time,FairPrice`, the hidden price the generator quotes around,
  as a step function.
- **Regimes** (`*.regime.csv`): `Start,End,Label` windows in seconds.

## Using and checking the files

- **Decompress:** `uv run --locked python -m gzip -d data/market_data/round4/round4_private.csv.gz`.
- **Integrity:** every `.gz` decompresses to the organiser's exact bytes. Check the stored files with
  `shasum -a 256 -c SHA256SUMS` in this folder. `manifest.json` has all raw hashes, row counts and
  time spans.
- **Official scores:** replaying our finals on these tapes reproduces all eight official
  validation and private scores to the dollar.
- **What the data shows:** see
  [data-release-fair-price-regimes.md](../../knowledge/round_4/dataathletechamp/data-release-fair-price-regimes.md).
