# Zubry / Qminers FIFO adaptive-quoting research package

**This is research for your team's private repository. The included figures are from an independent FIFO replay, not official Qminers simulator scores.**

- `research/FIFO_ADAPTIVE_QUOTING_RESEARCH.md` — comprehensive results, queue mechanics, 5ms latency, academic papers and action plan.
- `research/quote_size_sweep.csv`, `research/window_validation.csv` — all measured experimental outputs.
- `research/size_sweep.png`, `research/window_validation.png` — plots for comparison and your project report.
- `strategies/zubry_original_v2.py` — original uploaded baseline, unchanged.
- `strategies/zubry_safe_q{32,64,96,160,200}.py` — original strategy with only size/inventory-cap parameters changed.
- `strategies/zubry_adaptive_fifo.py` — experimental imbalance-adaptive quote sizing (not validated on official simulator).
- `strategies/zubry_addon_fifo.py` — experimental same-price FIFO top-up (not validated on official simulator).
- `tools/independent_fifo_replay.cpp` — research-only independent replay; does **not** implement the official engine verbatim.

Run official `uv run exchange-simulator` before submitting any strategy. **Preferred first official test: `zubry_safe_q200.py`; fallback `zubry_safe_q160.py`.** Keep failed experiments committed in the team's private repository.
- `tests/test_fifo.py` and `tests/fifo_queue_example.csv` — small self-contained FIFO test for the independent replay; requires local `c++` compiler.
