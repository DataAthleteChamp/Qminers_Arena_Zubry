"""Generate strategies/s_<i>.py deep-move strategies from crash_engine_template.py.

Usage: uv run --locked python generate_c.py <strategies_dir>
"""

from __future__ import annotations

import re
import sys
import textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = (HERE / "crash_engine_template.py").read_text()

SPECS: dict[int, tuple[str, dict[str, str]]] = {
    43: (
        "Jeździec na głębokim ruchu bez market makingu: gdy mid w 20 s przesunie się o >= 2 "
        "sigma (sigma z EWMA 120 s), wchodzi IOC na 60 lotów w kierunku ruchu. Wychodzi "
        "trailing stopem 1,5 sigma*sqrt(20) od najlepszej ceny, po 300 s albo po odwrotnym "
        "sygnale.",
        {"MAKER": "False", "DETECT": "True", "RIDE": "True"},
    ),
    44: (
        "Maker z bezpiecznikiem: kwotuje 5 lotów przy spreadzie 1 i spokojnej zmienności, a "
        "przy wykryciu startu ruchu lub drenażu płynności (5-sekundowa średnia L1 < 35% średniej 120 s) "
        "wycofuje kwotowania i zamyka pozycję IOC. Wraca do kwotowania po 30 s spokoju.",
        {"DETECT": "True", "DRAIN": "True", "BREAKER": "True"},
    ),
    45: (
        "Maker z wczesnym ostrzeganiem bez zamykania pozycji: przy wykryciu startu ruchu lub "
        "drenażu płynności tylko wycofuje kwotowania na 30 s. Zapas schodzi pasywnie po "
        "powrocie do kwotowania.",
        {"DETECT": "True", "DRAIN": "True", "BREAKER": "True", "BREAKER_FLATTEN": "False"},
    ),
    46: (
        "Maker, który przy wykryciu głębokiego ruchu przestaje kwotować i jedzie z ruchem "
        "(IOC 60 lotów, trailing stop 1,5 sigma*sqrt(20), maks. 300 s). Po wyjściu z jazdy "
        "wraca do kwotowania 5 lotów.",
        {"DETECT": "True", "RIDE": "True"},
    ),
    47: (
        "Pełna hybryda obronno-ofensywna: maker 5 lotów, jazda z wykrytym ruchem (IOC 60 "
        "lotów, trailing stop) oraz bezpiecznik na drenaż płynności, który wycofuje kwotowania "
        "i zamyka pozycję.",
        {"DETECT": "True", "RIDE": "True", "DRAIN": "True", "BREAKER": "True"},
    ),
    48: (
        "Kontrola rodziny: sam maker 5 lotów przy spreadzie 1 z względną bramką zmienności "
        "(30 s vol <= 1,5x vol długoterminowej), bez detektora, bezpiecznika i jazdy.",
        {},
    ),
}


def render(desc: str, over: dict[str, str]) -> str:
    src = TEMPLATE.replace("__DESCRIPTION__", textwrap.fill(desc, width=96) + "\n", 1)
    for k, v in over.items():
        src, n = re.subn(rf"^{k} = [^#\n]+", f"{k} = {v}  ", src, flags=re.M)
        if n != 1:
            raise SystemExit(f"constant {k} not found exactly once")
    return src


def main() -> None:
    out = Path(sys.argv[1])
    for i, (desc, over) in SPECS.items():
        if desc.count(". ") + 1 > 3:
            raise SystemExit(f"s_{i}: description longer than 3 sentences")
        (out / f"s_{i}.py").write_text(render(desc, over))
    print(f"wrote s_{min(SPECS)}..s_{max(SPECS)} to {out}")


if __name__ == "__main__":
    main()
