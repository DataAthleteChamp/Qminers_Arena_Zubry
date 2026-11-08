"""Render the R2 hybrid grid into sweep/<name>.py (spread gate always on).

Usage: uv run --locked python sweep.py
"""

from __future__ import annotations

import itertools

import generate as g

OUT = g.HERE / "sweep"


def main() -> None:
    OUT.mkdir(exist_ok=True)
    n = 0
    for vol, win, big, tox in itertools.product(("2.0", "2.5", "3.0"), ("30", "60"),
                                                ("0", "500", "1000"), (False, True)):
        over = {"REQUIRE_SPREAD": "1", "VOL_MAX": vol, "VOL_WINDOW_S": win, "BIG_TAKER": big,
                "COOLDOWN_S": "0.25", "TOX_GATE": str(tox)}
        name = f"v{vol.replace('.', '')}_w{win}_b{big}_t{int(tox)}"
        (OUT / f"{name}.py").write_text(g.render(f"Sweep variant {name}.", over))
        n += 1
    print(f"wrote {n} variants to {OUT}")


def main2() -> None:
    """Second grid: finer vol/window/cooldown, then size/inventory/skew at the centre."""
    out = g.HERE / "sweep2"
    out.mkdir(exist_ok=True)
    base = {"REQUIRE_SPREAD": "1", "BIG_TAKER": "500"}
    specs: dict[str, dict[str, str]] = {}
    for vol, win, cool in itertools.product(("1.5", "2.0", "2.5"), ("15", "20", "30"),
                                            ("0.25", "0.5")):
        specs[f"v{vol.replace('.', '')}_w{win}_c{cool.replace('.', '')}"] = {
            "VOL_MAX": vol, "VOL_WINDOW_S": win, "COOLDOWN_S": cool}
    centre = {"VOL_MAX": "2.0", "VOL_WINDOW_S": "30", "COOLDOWN_S": "0.25"}
    for size in ("1", "3", "4"):
        specs[f"centre_q{size}"] = {**centre, "QUOTE_SIZE": size}
    for cap in ("10", "40"):
        specs[f"centre_cap{cap}"] = {**centre, "MAX_INVENTORY": cap}
    for skew in ("0.0", "0.1"):
        specs[f"centre_skew{skew.replace('.', '')}"] = {**centre, "INVENTORY_SKEW": skew}
    for name, over in specs.items():
        (out / f"{name}.py").write_text(g.render(f"Sweep2 variant {name}.", {**base, **over}))
    print(f"wrote {len(specs)} variants to {out}")


def main3() -> None:
    """Third grid: quote size with an inventory cap well inside the +-100 penalty line."""
    out = g.HERE / "sweep3"
    out.mkdir(exist_ok=True)
    base = {"REQUIRE_SPREAD": "1", "BIG_TAKER": "500", "COOLDOWN_S": "0.25",
            "VOL_MAX": "2.0", "VOL_WINDOW_S": "20"}
    n = 0
    for size in (4, 6, 8, 10, 15, 20):
        cap = min(80, 10 * size)
        for mode, skew in (("fix", 0.05), ("scl", 0.1 / size)):
            over = {**base, "QUOTE_SIZE": str(size), "MAX_INVENTORY": str(cap),
                    "INVENTORY_SKEW": f"{skew:.4f}"}
            name = f"q{size}_cap{cap}_{mode}"
            (out / f"{name}.py").write_text(g.render(f"Sweep3 variant {name}.", over))
            n += 1
    print(f"wrote {n} variants to {out}")


def main4() -> None:
    """Fourth grid: where does size scaling stop (cap stays below the +-100 penalty line)."""
    out = g.HERE / "sweep4"
    out.mkdir(exist_ok=True)
    base = {"REQUIRE_SPREAD": "1", "BIG_TAKER": "500", "COOLDOWN_S": "0.25",
            "VOL_MAX": "2.0", "VOL_WINDOW_S": "20", "INVENTORY_SKEW": "0.05"}
    grid = [(25, 90), (30, 90), (40, 90), (50, 90), (30, 60), (45, 90)]
    for size, cap in grid:
        name = f"q{size}_cap{cap}"
        over = {**base, "QUOTE_SIZE": str(size), "MAX_INVENTORY": str(cap)}
        (out / f"{name}.py").write_text(g.render(f"Sweep4 variant {name}.", over))
    print(f"wrote {len(grid)} variants to {out}")


def main5() -> None:
    """Fifth grid: sizes 60/75 and the gate neighbourhood at size 50 (cap 90)."""
    out = g.HERE / "sweep5"
    out.mkdir(exist_ok=True)
    base = {"REQUIRE_SPREAD": "1", "BIG_TAKER": "500", "COOLDOWN_S": "0.25",
            "VOL_MAX": "2.0", "VOL_WINDOW_S": "20", "INVENTORY_SKEW": "0.05",
            "MAX_INVENTORY": "90", "QUOTE_SIZE": "50"}
    specs = {
        "q60_cap90": {"QUOTE_SIZE": "60"},
        "q75_cap90": {"QUOTE_SIZE": "75"},
        "q50_v25_w15": {"VOL_MAX": "2.5", "VOL_WINDOW_S": "15"},
        "q50_v20_w30": {"VOL_WINDOW_S": "30"},
        "q50_v15_w20": {"VOL_MAX": "1.5"},
        "q50_nofreeze": {"BIG_TAKER": "0"},
    }
    for name, over in specs.items():
        (out / f"{name}.py").write_text(g.render(f"Sweep5 variant {name}.", {**base, **over}))
    print(f"wrote {len(specs)} variants to {out}")


if __name__ == "__main__":
    import sys

    {"2": main2, "3": main3, "4": main4, "5": main5}.get(sys.argv[1] if len(sys.argv) > 1 else "", main)()
