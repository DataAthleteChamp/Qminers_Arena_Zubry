# koziol.py: porównanie na trzech ścieżkach (R1, R2 publiczna, R2 prywatna walidacyjna)

`strategies/koziol.py` to plik zespołu, którego nie modyfikowałem. Kopię do przebiegów
(SHA-256 `cde5c940…4616`) zrobiłem w
`experiments/round_2/luklen123/20261107-koziol-crosscheck/`. Plik przechodzi lokalny preflight.
Przebiegi robiłem w oficjalnym symulatorze, bez zmian.

## Co robi strategia

- **Docelowa pozycja ±100 lotów.** Wynika z trendu: trzy średnie EMA (3/30/120 s) muszą być
  ułożone w tym samym kierunku.
- **Liniowa prognoza krótkiego ruchu ceny** z 11 cech: nierównowaga L1 i głębokości, przepływ
  agresorów z 50 ms, dopływ nowych zleceń, ruch ceny 100/250 ms wstecz i spread. Wagi są
  wpisane na stałe; na jakich danych je dopasowano, nie wiadomo.
- **Środek kwotowań** to mid + prognoza − 0,01 × (zapas − cel). Grid ma 3 poziomy po 32 loty,
  w ostrożności 16.
- **Stany SHOCK / RECOVERY / CAUTION** zależą od spreadu i głębokości L1.
- **Ekspozycja razem z otwartymi zleceniami jest twardo ograniczona do 100**, więc kara jest
  wykluczona.

## Wyniki

| Ścieżka | PnL | H1 / H2 | pnl_se | maxDD | Fille | Zapas (q99,7) |
|---|---|---|---|---|---|---|
| R1 (12 000 s, spokojny wzrost) | **+149 143** | 67 904 / 81 239 | 6 661 | 822 | 26 368 | 100 |
| R2 publiczna (krach, −310) | **+91 025** | 21 869 / 69 156 | 20 909 | 11 715 | 12 266 | 100 |
| R2 prywatna walidacyjna (wzrost ~+480) | **+28 827** | — | 37 466 | — | 23 195 | 100 |
| porównanie: s_20, R2 prywatna | −10 781 | — | 14 714 | — | 14 844 | 68 |
| porównanie: s1, R2 publiczna / R1 | +1 816 / +10 339 | — | 332 / 185 | 286 / 27 | — | 5 |

Wynik na prywatnej ścieżce policzyłem ze statystyk serwera:
gotówka 102 201 − 7 × 10 482 = 28 827.

## Wnioski

- **Strategia zarabia na wszystkich trzech ścieżkach**, także przy przeciwnych kierunkach
  trendu (R2 publiczna spada, R2 prywatna rośnie). Przewaga nie bierze się więc ze zgadnięcia
  kierunku.
- **Dominuje nasze makery s1 i s_1–s_20** na każdej ścieżce.
- **Na R2 wynik jest bardzo zmienny** (prywatnie tylko +0,77 SE), bo zapas często stoi przy
  ±100. Na R1 wynik jest wyraźny (~22 SE).
- **Otwarte pytania:**
  - na jakich danych dopasowano wagi prognozy? Jeśli na R2 publicznej, to +91 tys. jest in-sample;
  - który składnik daje zysk: cel trendowy, prognoza czy grid z dużym kwotowaniem?
    Do sprawdzenia ablacją na kopiach, na R1 i R2 jednocześnie.
