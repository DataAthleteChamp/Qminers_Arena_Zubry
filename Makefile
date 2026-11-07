.PHONY: setup test lint typecheck check playground-original playground-team compare

setup:
	uv sync --locked

test:
	uv run --locked python -m pytest

lint:
	uv run --locked ruff check tools tests strategies/zubry.py strategies/zubry_v2.py
	uv run --locked ruff format --check tools tests strategies/zubry.py strategies/zubry_v2.py

typecheck:
	uv run --locked mypy

check: lint typecheck test
	uv run --locked python -m tools.preflight strategies/zubry.py
	uv run --locked python -m tools.preflight strategies/zubry_v2.py
	uv run --locked python -m tools.validate_setup

playground-original:
	uv run --locked python -m tools.run_experiment --id p0-original-r0 --owner bootstrap --round playground --strategy strategies/trend_follower.py --backtest data/round0/sample.csv --hypothesis "Run the unchanged organiser example on the canonical round0 path" --reject-if "Unexpected failure, penalty or mismatch"

playground-team:
	uv run --locked python -m tools.run_experiment --id p0-zubry-r0 --owner bootstrap --round playground --strategy strategies/zubry.py --backtest data/round0/sample.csv --hypothesis "The documented IOC reset prevents permanent waiting after a miss" --reject-if "State handling fails or unexpected penalty occurs"

compare:
	uv run --locked python -m tools.compare p0-original-r0 p0-zubry-r0
