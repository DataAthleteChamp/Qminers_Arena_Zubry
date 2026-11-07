"""Independent replay smoke test: same-price FIFO, NOT official Qminers engine validation."""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXE = ROOT / "tools" / "independent_fifo_replay"
SRC = ROOT / "tools" / "independent_fifo_replay.cpp"
DATA = ROOT / "tests" / "fifo_queue_example.csv"
subprocess.run(["c++", "-O3", "-std=c++17", str(SRC), "-o", str(EXE)], check=True)

def run(size: int) -> dict:
    return json.loads(subprocess.check_output(
        [str(EXE), str(DATA), "0", str(size), "100", "1"], text=True
    ))

small, medium, large = run(2), run(32), run(96)
assert small["volume"] == 2, small
assert medium["volume"] == 20, medium
assert large["volume"] == 20, large
assert all(r["penalty"] == 0 for r in (small, medium, large))
assert all(r["accepted_queue_ahead_p50"] == 70 for r in (small, medium, large))
print("PASS: 90 sell lots clear 70 ahead, leaving 20 to user; increasing q32 to q96 does not increase fill")
