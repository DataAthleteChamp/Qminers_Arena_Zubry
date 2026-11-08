"""Turn the kuba.py snapshot into kuba_engine_template.py with its magic numbers as constants.
Each replacement must match exactly the expected number of times.
Usage: uv run --locked python parametrize.py
"""

from pathlib import Path

HERE = Path(__file__).resolve().parent
src = (HERE.parent / "20261107-kuba-crosscheck" / "kuba.py").read_text()

NEW_CONSTANTS = '''GAP_GUARD = True
SHOCK_SPREAD = 3  # spread >= this -> SHOCK
MIN_L1 = 100  # min(bid, ask) L1 lots required for NORMAL
CAUTION_DIV = 2  # quote-size divisor in CAUTION / RECOVERY
GAP_QTY = 100  # best level at or below this many lots ...
GAP_TICKS = 2  # ... with the next level this many ticks behind -> fragile side
FRAGILE_SIZE = 12  # quote size on a fragile side
TOPUP_MIN = 8  # smallest top-up order
MAX_PER_LEVEL = 2  # resting orders allowed per grid level
SLOT_MULT = 2  # max resting orders per side = SLOT_MULT * GRID_LEVELS
TARGET_SCALE = 1.0  # trend target = TARGET_SCALE * POSITION_LIMIT * direction
'''

REPL = [
    ('"""Typed active-policy port of the user-supplied Grid; fit provenance unknown."""',
     '"""__DESCRIPTION__"""', 1),
    ("GAP_GUARD = True\n", NEW_CONSTANTS, 1),
    ("        if spread >= 3:", "        if spread >= SHOCK_SPREAD:", 1),
    ("min(bid_quantity, ask_quantity) >= 100", "min(bid_quantity, ask_quantity) >= MIN_L1", 2),
    ("bid_quantity <= 100 and next_bid is not None and bid - next_bid >= 2",
     "bid_quantity <= GAP_QTY and next_bid is not None and bid - next_bid >= GAP_TICKS", 1),
    ("ask_quantity <= 100 and next_ask is not None and next_ask - ask >= 2",
     "ask_quantity <= GAP_QTY and next_ask is not None and next_ask - ask >= GAP_TICKS", 1),
    ("quantity = QUOTE_SIZE // 2", "quantity = QUOTE_SIZE // CAUTION_DIV", 2),
    ("min(quantity, 12) if side in self.fragile_sides",
     "min(quantity, FRAGILE_SIZE) if side in self.fragile_sides", 1),
    ("if len(matching) >= 2 or", "if len(matching) >= MAX_PER_LEVEL or", 1),
    ("(matching and size < 8)", "(matching and size < TOPUP_MIN)", 1),
    ("if slots < 2 * GRID_LEVELS:", "if slots < SLOT_MULT * GRID_LEVELS:", 1),
    ("self.target = POSITION_LIMIT * direction",
     "self.target = round(TARGET_SCALE * POSITION_LIMIT * direction)", 1),
]

for old, new, n in REPL:
    found = src.count(old)
    if found != n:
        raise SystemExit(f"expected {n} x {old!r}, found {found}")
    src = src.replace(old, new)
(HERE / "kuba_engine_template.py").write_text(src)
print("wrote kuba_engine_template.py")
