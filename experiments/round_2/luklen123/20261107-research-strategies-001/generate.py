"""Generate standalone strategies/s_<i>.py files from engine_template.py and SPECS.

Each spec: (description of at most 3 sentences, {CONSTANT: python literal}).
Usage: uv run --locked python generate.py <strategies_dir>
"""

from __future__ import annotations

import re
import sys
import textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = (HERE / "engine_template.py").read_text()

S1 = {"REQUIRE_SPREAD": "1", "VOL_MAX": "3.0"}  # validated s1 regime gate
HYBRID = {  # R2 sweep plateau centre
    "REQUIRE_SPREAD": "1",
    "VOL_MAX": "2.0",
    "VOL_WINDOW_S": "20",
    "BIG_TAKER": "500",
    "COOLDOWN_S": "0.25",
    "INVENTORY_SKEW": "0.05",
}

SPECS: dict[int, tuple[str, dict[str, str]]] = {
    # ---------------- single mechanisms from round2-strategies-research.txt
    1: (
        "Maker L1 z podwójną bramką reżimu: kwotuje tylko przy spreadzie 1 tick i zmienności "
        "1 s z 60 s <= 2,5 ticka. Poza reżimem wycofuje kwotowania i zostawia jedynie stronę "
        "redukującą zapas.",
        {"REQUIRE_SPREAD": "1", "VOL_MAX": "2.5"},
    ),
    2: (
        "Maker L1 ze strażnikiem pozycji w kolejce FIFO, liczonej dokładnie ze snapshotu. "
        "Gdy wolumen poziomu spada poniżej 150 lotów, a przed nami stoi ponad 30 lotów rynku, "
        "zlecenie jest wycofywane i nie wraca na ten sam poziom.",
        {"QUEUE_GUARD": "True"},
    ),
    3: (
        "Maker L1 z progową (bang-bang) kontrolą zapasu i kwotowaniem po 1 locie. "
        "Powyżej |Q| = 5 kwotuje tylko stronę redukującą, a powyżej |Q| = 25 likwiduje "
        "nadwyżkę zleceniem IOC do |Q| = 15.",
        {"BANG_BANG": "True", "QUOTE_SIZE": "1", "MAX_INVENTORY": "30"},
    ),
    4: (
        "Maker L1 z ucinaniem strat (scratch/stop): zlecenie redukujące stoi na najlepszej "
        "cenie, a gdy rynek odejdzie o 2 ticki od średniej ceny wejścia, pozycja jest "
        "zamykana zleceniem IOC.",
        {"STOP_TICKS": "2"},
    ),
    5: (
        "Maker L1 z zamrożeniem strony po zleceniu blokowym. Po agresorze >= 500 lotów "
        "zawiesza kwotowanie po uderzonej stronie na 250 ms.",
        {"BIG_TAKER": "500", "COOLDOWN_S": "0.25"},
    ),
    6: (
        "Maker L1 z bramką toksyczności VPIN (koszyki 5000 lotów, okno 20 koszyków). "
        "Wstrzymuje kwotowanie, gdy VPIN przekracza 90. percentyl swojej dotychczasowej "
        "historii, liczonej online bez zaglądania w przyszłość.",
        {"VPIN_GATE": "True"},
    ),
    7: (
        "Maker L1 z testem skoków ceny opartym na wariacji dwupotęgowej (bipower) na siatce "
        "1 s w oknie 60 s. Gdy statystyka Z > 2,33, wycofuje kwotowania do czasu, aż skok "
        "wyjdzie z okna.",
        {"JUMP_GATE": "True"},
    ),
    8: (
        "Maker L1 z bramką intensywności dużych agresorów (uproszczony proxy procesu "
        "Hawkesa): wykładniczo zanikający licznik zleceń > 183 lotów, z połowicznym zanikiem "
        "10 s. Wstrzymuje kwotowanie, gdy intensywność przekracza 90. percentyl własnej "
        "historii.",
        {"TOX_GATE": "True"},
    ),
    # ---------------- combinations
    9: (
        "Pełna architektura z researchu „Regime-Gated Asymmetric Maker”: bramka spread = 1 "
        "i zmienność <= 2,5, strażnik kolejki, kontrola zapasu 5/15/25 po 1 locie, stop 2 "
        "ticki i zamrożenie strony na 250 ms po agresorze >= 500. W stresie zapas "
        "powyżej 10 jest redukowany zleceniem IOC.",
        {
            "REQUIRE_SPREAD": "1",
            "VOL_MAX": "2.5",
            "QUEUE_GUARD": "True",
            "BANG_BANG": "True",
            "QUOTE_SIZE": "1",
            "MAX_INVENTORY": "30",
            "STOP_TICKS": "2",
            "BIG_TAKER": "500",
            "COOLDOWN_S": "0.25",
            "FLATTEN_IN_STRESS": "True",
            "FLATTEN_ABOVE": "10",
        },
    ),
    10: (
        "Zwalidowany maker s1 (spread = 1, zmienność <= 3) połączony ze strażnikiem pozycji "
        "w kolejce FIFO.",
        {**S1, "QUEUE_GUARD": "True"},
    ),
    11: (
        "Zwalidowany maker s1 (spread = 1, zmienność <= 3) z zamrożeniem strony na 250 ms "
        "po agresorze >= 500 lotów.",
        {**S1, "BIG_TAKER": "500", "COOLDOWN_S": "0.25"},
    ),
    12: (
        "Zwalidowany maker s1 (spread = 1, zmienność <= 3) z dodatkową bramką "
        "toksyczności VPIN.",
        {**S1, "VPIN_GATE": "True"},
    ),
    13: (
        "Zwalidowany maker s1 (spread = 1, zmienność <= 3) z dodatkowym testem skoków "
        "bipower.",
        {**S1, "JUMP_GATE": "True"},
    ),
    14: (
        "Zwalidowany maker s1 (spread = 1, zmienność <= 3) z dodatkową bramką intensywności "
        "dużych agresorów (proxy Hawkesa).",
        {**S1, "TOX_GATE": "True"},
    ),
    15: (
        "Zwalidowany maker s1 (spread = 1, zmienność <= 3) z progową kontrolą zapasu "
        "5/15/25 i kwotowaniem po 1 locie.",
        {**S1, "BANG_BANG": "True", "QUOTE_SIZE": "1", "MAX_INVENTORY": "30"},
    ),
    # ---------------- R2-optimised hybrids (sweeps 1-5): same gate, rising size/risk
    **{
        i: (
            f"Hybryda zoptymalizowana pod R2: kwotuje {size} lotów na najlepszej cenie tylko przy "
            "spreadzie 1 i zmienności 1 s z 20 s <= 2,0 ticka, a po agresorze >= 500 lotów "
            f"zamraża uderzoną stronę na 250 ms. Limit zapasu {cap} lotów trzyma pozycję "
            f"poniżej progu kary 100, a profil ryzyka to {risk}.",
            {**HYBRID, "QUOTE_SIZE": str(size), "MAX_INVENTORY": str(cap)},
        )
        for i, size, cap, risk in (
            (16, 4, 40, "niski"),
            (17, 10, 80, "umiarkowany"),
            (18, 20, 80, "średni"),
            (19, 30, 90, "wysoki"),
            (20, 50, 90, "bardzo wysoki"),
        )
    },
}


def render(desc: str, over: dict[str, str]) -> str:
    wrapped = textwrap.fill(desc, width=96) + "\n"
    src = TEMPLATE.replace("__DESCRIPTION__", wrapped, 1)
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
    print(f"wrote {len(SPECS)} strategies to {out}")


if __name__ == "__main__":
    main()
