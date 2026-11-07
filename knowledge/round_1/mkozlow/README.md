# Round1 research by mkozlow

Start with [team handoff](team-handoff.md): best retained maker, exact benchmark, major research findings, failed taker/penalty policies and reproduction commands.

Retained standalone baseline: [midpoint maker64](../../../strategies/round_1/mkozlow/midpoint_maker_64.py), exact tested source with206364 local full-tape PnL, zero penalty and no active fitted directional model. Server/private confirmation remains pending.

Detailed notes:

- [Signal execution](signal-execution.md) and [inventory capacity](inventory-capacity.md).
- [Adaptive makers and hybrids](adaptive-makers-and-takers.md) and [taker horizons](taker-horizon.md).
- [Price and size distributions](price-size-distributions.md).
- [Round0 supplied evidence](round0-user-supplied-evidence.md) and [report review](round0-report-review.md).
- [Maker penalty economics](maker-penalty.md).

Experimental code, frozen trial variants, logs and plots stay under`experiments/round_1/mkozlow/`. Use`uv run --locked`, preserve completed runs, work on a branch and stage only explicit reviewed knowledge/strategy paths. Preparing this handoff does not authorize a commit or upload.
