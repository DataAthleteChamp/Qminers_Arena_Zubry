"""Generate strategies/s_<i>.py extensions of kuba.py from kuba_engine_template.py.

Usage: uv run --locked python generate_kuba.py <strategies_dir> [--only 54,55] [--control path]
"""

from __future__ import annotations

import re
import sys
import textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = (HERE / "kuba_engine_template.py").read_text()

K = "kuba.py"
SPECS: dict[int, tuple[str, dict[str, str]]] = {
    54: (f"{K} z niższym progiem uzupełniania poziomu: dokłada zlecenie już przy braku >= 4 lotów "
         "(zamiast 8), więc poziomy gridu szybciej wracają do pełnej wielkości.",
         {"TOPUP_MIN": "4"}),
    55: (f"{K} z wyższym progiem uzupełniania poziomu (>= 16 lotów zamiast 8): mniej drobnych "
         "zleceń, mniej ryzyka dokładania w trakcie sweepa.",
         {"TOPUP_MIN": "16"}),
    56: (f"{K} z maksymalnie 3 zleceniami na poziom gridu (zamiast 2) i 9 na stronę, aby "
         "dłużej utrzymywać pełną wielkość przy częściowych wypełnieniach.",
         {"MAX_PER_LEVEL": "3", "SLOT_MULT": "3"}),
    57: (f"{K} z szerszą ochroną przed luką: strona jest krucha już przy <= 150 lotach na "
         "najlepszej cenie (zamiast 100) z luką >= 2 ticki za nią.",
         {"GAP_QTY": "150"}),
    58: (f"{K} z węższą ochroną przed luką: strona jest krucha dopiero przy <= 60 lotach na "
         "najlepszej cenie z luką >= 2 ticki.",
         {"GAP_QTY": "60"}),
    59: (f"{K}, w którym krucha strona (cienka najlepsza cena z luką za nią) jest całkowicie "
         "wycofywana zamiast zmniejszana do 12 lotów.",
         {"FRAGILE_SIZE": "0"}),
    60: (f"{K} z łagodniejszą ochroną przed luką: na kruchej stronie zostaje 20 lotów "
         "zamiast 12.",
         {"FRAGILE_SIZE": "20"}),
    61: (f"{K}, w którym strona jest krucha przy <= 100 lotach na najlepszej cenie bez "
         "względu na lukę za nią (ochrona przed cienką kolejką).",
         {"GAP_TICKS": "1"}),
    62: (f"{K} z późniejszym wejściem w tryb SHOCK: dopiero przy spreadzie >= 4 ticki "
         "(zamiast 3).",
         {"SHOCK_SPREAD": "4"}),
    63: (f"{K} z łagodniejszym warunkiem trybu NORMAL: wystarczy >= 50 lotów po obu stronach "
         "najlepszej ceny (zamiast 100).",
         {"MIN_L1": "50"}),
    64: (f"{K} z ostrzejszym warunkiem trybu NORMAL: wymaga >= 200 lotów po obu stronach "
         "najlepszej ceny (zamiast 100).",
         {"MIN_L1": "200"}),
    65: (f"{K} z dłuższym powrotem po szoku: tryb NORMAL dopiero po 500 ms stabilnego rynku "
         "(zamiast 200 ms).",
         {"RECOVERY_US": "500_000"}),
    66: (f"{K} z gridem 4-poziomowym (zamiast 3), czyli z dodatkową płynnością głębiej w "
         "księdze.",
         {"GRID_LEVELS": "4"}),
    67: (f"{K} z większym kwotowaniem: 40 lotów na poziom (zamiast 32), przy tym samym "
         "limicie pozycji 100.",
         {"QUOTE_SIZE": "40"}),
    68: (f"{K} z celem trendowym +-75 lotów (zamiast +-100), aby zmniejszyć ekspozycję "
         "kierunkową.",
         {"TARGET_SCALE": "0.75"}),
    69: (f"{K} bez zmniejszania kwotowania o połowę w trybach CAUTION i RECOVERY.",
         {"CAUTION_DIV": "1"}),
    # ---------------- round 2: combinations around the accepted changes (s_67, s_56)
    70: (f"{K} z kwotowaniem 40 lotów i maksymalnie 3 zleceniami na poziom gridu (połączenie "
         "s_67 i s_56).",
         {"QUOTE_SIZE": "40", "MAX_PER_LEVEL": "3", "SLOT_MULT": "3"}),
    71: (f"{K} z kwotowaniem 48 lotów na poziom (zamiast 32), przy limicie pozycji 100.",
         {"QUOTE_SIZE": "48"}),
    72: (f"{K} z kwotowaniem 36 lotów na poziom (zamiast 32), przy limicie pozycji 100.",
         {"QUOTE_SIZE": "36"}),
    73: (f"{K} z kwotowaniem 40 lotów i 20 lotami na kruchej stronie (zamiast 12).",
         {"QUOTE_SIZE": "40", "FRAGILE_SIZE": "20"}),
    74: (f"{K} z kwotowaniem 40 lotów i szerszą ochroną przed luką (krucha strona przy <= 150 "
         "lotach na najlepszej cenie).",
         {"QUOTE_SIZE": "40", "GAP_QTY": "150"}),
    # ---------------- robust successive-halving HPO winner (20261108-kuba-robust-hpo-001)
    75: (f"{K} z parametrami z odpornej optymalizacji (successive halving na 15 taśmach): "
         "dwa razy szybsze EMA trendu (2/15/60 s), kara za zapas 0,0065, 36 lotów, szok od "
         "spreadu 4, bez zmniejszania kwotowania w trybie ostrożności. Bije s_67 na 15 z 15 "
         "taśm testowych.",
         {"QUOTE_SIZE": "36", "INVENTORY_SKEW": "0.0065", "EMA_SECONDS": "(2, 15, 60)",
          "GAP_QTY": "60", "FRAGILE_SIZE": "8", "TOPUP_MIN": "16", "SHOCK_SPREAD": "4",
          "RECOVERY_US": "500000", "MIN_L1": "50", "CAUTION_DIV": "1"}),
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
    only = None
    if "--only" in sys.argv:
        only = {int(x) for x in sys.argv[sys.argv.index("--only") + 1].split(",")}
    if "--control" in sys.argv:
        Path(sys.argv[sys.argv.index("--control") + 1]).write_text(
            render("Kontrola: silnik kuba bez zmian.", {}))
    n = 0
    for i, (desc, over) in SPECS.items():
        if only is not None and i not in only:
            continue
        if desc.count(". ") + 1 > 3:
            raise SystemExit(f"s_{i}: description longer than 3 sentences")
        (out / f"s_{i}.py").write_text(render(desc, over))
        n += 1
    print(f"wrote {n} strategies")


if __name__ == "__main__":
    main()
