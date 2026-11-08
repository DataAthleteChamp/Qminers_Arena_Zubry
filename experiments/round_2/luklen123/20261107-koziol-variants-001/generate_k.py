"""Generate strategies/s_<i>.py koziol variants from koziol_engine_template.py.

Usage: uv run --locked python generate_k.py <strategies_dir> [--control <path>]
"""

from __future__ import annotations

import re
import sys
import textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = (HERE / "koziol_engine_template.py").read_text()

DYN = {"SKEW_GAMMA": "0.01", "INVENTORY_SKEW_MIN": "0.005"}

SPECS: dict[int, tuple[str, dict[str, str]]] = {
    21: (
        "Wariant koziol.py bez liniowej prognozy 11 cech: środek kwotowań to mid minus kara za "
        "odchylenie zapasu od celu trendowego. Ablacja sprawdzająca, ile zysku daje prognoza.",
        {"USE_PREDICTION": "False"},
    ),
    22: (
        "Wariant koziol.py bez celu trendowego z EMA 3/30/120 s: zapas jest ściągany do zera "
        "jak w klasycznym makerze. Testuje tezę dokumentu, że podążanie za trendem szkodzi.",
        {"USE_TREND_TARGET": "False"},
    ),
    23: (
        "Wariant koziol.py, w którym środek kwotowań liczony jest od mikroceny Stoikova "
        "(mid ważony wolumenem L1) zamiast od mid. Prognoza i cel trendowy bez zmian.",
        {"MICRO_WEIGHT": "1.0"},
    ),
    24: (
        "Wariant koziol.py, w którym statyczną prognozę 11 cech zastępuje mikrocena Stoikova "
        "z korektą wielopoziomowej nierównowagi księgi (MLOFI, 5 poziomów, zanik 0,5).",
        {"USE_PREDICTION": "False", "MICRO_WEIGHT": "1.0", "MLOFI_COEF": "0.5"},
    ),
    25: (
        "Wariant koziol.py z karą za zapas zależną od zmienności, phi = gamma * sigma^2 / 2 "
        "(gamma 0,01, sigma^2 jako EWMA kwadratów zmian mid 1 s, minimum 0,005). Kara rośnie w "
        "okresach wysokiej zmienności, a w spokoju maleje.",
        {"SKEW_GAMMA": "0.01", "INVENTORY_SKEW_MIN": "0.005"},
    ),
    26: (
        "Wariant koziol.py z asymetryczną bramką VPIN (koszyki 5000 lotów, 20 koszyków, próg "
        "90. percentyla liczony online). Przy toksycznym przepływie usuwa kwotowania po "
        "stronie, w którą uderzają agresorzy.",
        {"VPIN_GATE": "True"},
    ),
    27: (
        "Wariant koziol.py z zamrożeniem strony na 250 ms po zleceniu agresora >= 500 lotów, "
        "czyli mechanizmem, który pomógł makerom s_11 i s_16-s_20.",
        {"BIG_TAKER": "500"},
    ),
    28: (
        "Wariant koziol.py z bramką zmienności: gdy odchylenie zmian mid 1 s z 20 s przekracza "
        "3 ticki, strategia przechodzi w tryb RECOVERY i kwotuje tylko w stronę celu zapasu.",
        {"VOL_MAX": "3.0"},
    ),
    29: (
        "Wariant koziol.py z ochroną pozycji w kolejce: zlecenie gridu, które znalazło się do "
        "1 ticka za siatką, nie jest anulowane, więc zachowuje priorytet FIFO.",
        {"KEEP_BAND": "1"},
    ),
    30: (
        "Wariant koziol.py z celem trendowym zmniejszonym o połowę (+-50 lotów zamiast +-100). "
        "Ogranicza ekspozycję kierunkową i rozrzut wyniku kosztem części zysku z trendu.",
        {"TREND_SCALE": "0.5"},
    ),
    # ---------------- hybrids of the components that helped on R1 and/or R2 public
    31: (
        "Hybryda koziol.py: kara za zapas zależna od zmienności (gamma 0,01) oraz cel "
        "trendowy zmniejszony do +-50 lotów.",
        {**DYN, "TREND_SCALE": "0.5"},
    ),
    32: (
        "Hybryda koziol.py: kara za zapas zależna od zmienności (gamma 0,01) oraz zamrożenie "
        "strony na 250 ms po agresorze >= 500 lotów; pełny cel trendowy +-100.",
        {**DYN, "BIG_TAKER": "500"},
    ),
    33: (
        "Hybryda koziol.py: cel trendowy +-50 lotów oraz zamrożenie strony na 250 ms po "
        "agresorze >= 500 lotów.",
        {"TREND_SCALE": "0.5", "BIG_TAKER": "500"},
    ),
    34: (
        "Hybryda koziol.py łącząca trzy pomocne zmiany: karę za zapas zależną od zmienności "
        "(gamma 0,01), cel trendowy +-50 lotów i zamrożenie strony po agresorze >= 500 lotów.",
        {**DYN, "TREND_SCALE": "0.5", "BIG_TAKER": "500"},
    ),
    35: (
        "Hybryda koziol.py: kara za zapas zależna od zmienności (gamma 0,01) oraz cel "
        "trendowy +-75 lotów, kompromis między zyskiem z trendu na R2 a jego kosztem na R1.",
        {**DYN, "TREND_SCALE": "0.75"},
    ),
    36: (
        "Wariant koziol.py z mocniejszą karą za zapas zależną od zmienności (gamma 0,02, "
        "minimum 0,005) i pełnym celem trendowym +-100.",
        {"SKEW_GAMMA": "0.02", "INVENTORY_SKEW_MIN": "0.005"},
    ),
    # ---------------- s_25 + fast move-onset detector (crash-precursors.md)
    37: (
        "s_25 z szybkim wykryciem startu ruchu: gdy mid w 20 s przesunie się o >= 2,5 sigma "
        "(min. 15 ticków), cel zapasu natychmiast przechodzi na +-100 w kierunku ruchu na "
        "180 s. Wejście w pozycję tylko pasywnie przez grid.",
        {**DYN, "FAST_K": "2.5"},
    ),
    38: (
        "s_25 z szybkim wykryciem startu ruchu (20 s, 2,5 sigma, min. 15 ticków, 180 s) i "
        "natychmiastowym wejściem zleceniem IOC do 50 lotów w kierunku ruchu.",
        {**DYN, "FAST_K": "2.5", "FAST_IOC_QTY": "50"},
    ),
    39: (
        "s_25 z szybszym wykryciem startu ruchu na oknie 10 s (2,5 sigma, min. 15 ticków), "
        "cel +-100 w kierunku ruchu przez 180 s, wejście pasywne.",
        {**DYN, "FAST_K": "2.5", "FAST_LOOKBACK_S": "10"},
    ),
    40: (
        "s_25 z wykryciem startu ruchu (20 s, 2,5 sigma, min. 15 ticków) i krótszym "
        "utrzymaniem celu: 60 s zamiast 180 s.",
        {**DYN, "FAST_K": "2.5", "FAST_HOLD_S": "60"},
    ),
    41: (
        "s_25 z czulszym wykryciem startu ruchu (20 s, 2,0 sigma, min. 15 ticków), cel "
        "+-100 w kierunku ruchu przez 180 s.",
        {**DYN, "FAST_K": "2.0"},
    ),
    42: (
        "s_25 z ostrożniejszym wykryciem startu ruchu (20 s, 3,5 sigma, min. 25 ticków), "
        "cel +-100 w kierunku ruchu przez 180 s.",
        {**DYN, "FAST_K": "3.5", "FAST_MIN_TICKS": "25.0"},
    ),
    # ---------------- deep-move market versions of s_41 (deep-move-strategies-001)
    49: (
        "s_41 z natychmiastowym wejściem IOC do 100 lotów po wykryciu startu ruchu: pozycja "
        "przeciwna do ruchu jest od razu zamykana i odwracana, zamiast czekać na pasywny grid.",
        {**DYN, "FAST_K": "2.0", "FAST_IOC_QTY": "100"},
    ),
    50: (
        "s_41 z czysto względnym progiem detektora (2 sigma, minimum tylko 5 ticków zamiast "
        "15), aby działał na rynkach o innej skali zmienności niż R2.",
        {**DYN, "FAST_K": "2.0", "FAST_MIN_TICKS": "5.0"},
    ),
    51: (
        "s_41 z względnym progiem detektora (min. 5 ticków) i natychmiastowym wejściem IOC do "
        "100 lotów w kierunku wykrytego ruchu.",
        {**DYN, "FAST_K": "2.0", "FAST_MIN_TICKS": "5.0", "FAST_IOC_QTY": "100"},
    ),
    52: (
        "s_41 z wczesnym ostrzeżeniem o drenażu płynności: gdy 5-sekundowa średnia głębokości "
        "L1 spadnie poniżej 35% średniej 120 s, przez 30 s kwotuje tylko w stronę celu zapasu, "
        "połową wielkości.",
        {**DYN, "FAST_K": "2.0", "DRAIN_RATIO": "0.35"},
    ),
    53: (
        "koziol.py z wczesnym ostrzeżeniem o drenażu płynności (5-sekundowa średnia L1 < 35% "
        "średniej 120 s): przez 30 s kwotuje tylko w stronę celu zapasu, połową wielkości.",
        {"DRAIN_RATIO": "0.35"},
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
    if "--control" in sys.argv:
        path = Path(sys.argv[sys.argv.index("--control") + 1])
        path.write_text(render("Kontrola: silnik koziol bez zmian.", {}))
        print(f"wrote control {path}")
    only = None
    if "--only" in sys.argv:
        only = {int(x) for x in sys.argv[sys.argv.index("--only") + 1].split(",")}
    if "--s25-control" in sys.argv:
        path = Path(sys.argv[sys.argv.index("--s25-control") + 1])
        path.write_text(render("Kontrola: s_25 z bieżącego silnika.", SPECS[25][1]))
        print(f"wrote s_25 control {path}")
    for i, (desc, over) in SPECS.items():
        if only is not None and i not in only:
            continue
        if desc.count(". ") + 1 > 3:
            raise SystemExit(f"s_{i}: description longer than 3 sentences")
        (out / f"s_{i}.py").write_text(render(desc, over))
    print(f"wrote {len(SPECS)} strategies to {out}")


if __name__ == "__main__":
    main()
