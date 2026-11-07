# Warianty koziol.py s_21–s_36: test tez ze `stategy_and_dataset.txt`

Pytanie: które zmiany proponowane w dokumencie `stategy_and_dataset.txt` poprawiają
`strategies/koziol.py`? Dokument proponował:

- mikrocenę Stoikova i MLOFI zamiast prognozy,
- karę za zapas φ = γσ²/2,
- stan ryzyka sterowany VPIN i procesem Hawkesa,
- ochronę pozycji w kolejce,
- rezygnację z celu trendowego z EMA.

## Metoda

- **Silnik.** `koziol_engine_template.py` zawiera kod `koziol.py` bez zmian, a każda teza to
  wyłączana flaga. `generate_k.py` wypisuje z niego pliki `strategies/s_<i>.py`.
- **Kontrola.** Silnik bez zmian odtwarza oryginał co do jednostki: R2 publiczna +91 025,
  R1 +149 143.
- **Dane.** R2 publiczna (SHA-256 `88ff641e…`, 6000 s) i R1 (`362e8208…`, 12 000 s).
  Symulator oficjalny.
- **Ocena na obu taśmach.** s_20, strojony tylko pod R2 publiczną, przegrał na prywatnej
  walidacji, więc tym razem oceniam na R1 i R2 jednocześnie.
- **Szum.** R2 publiczna ma pnl_se ok. 21 tys. i rozróżnia warianty słabo. R1 ma pnl_se
  ok. 5–7 tys.
- Pliki robocze: `experiments/round_2/luklen123/20261107-koziol-variants-001/`.

## Wyniki (PnL, kara 0 wszędzie, zapas q99,7 = 95–100)

| Plik | Zmiana względem koziol.py | R1 | R2 publiczna | R2 se |
|---|---|---|---|---|
| kontrola | brak | 149 143 | 91 025 | 20 909 |
| s_21 | bez prognozy 11 cech | 146 559 | 90 132 | 21 054 |
| s_22 | bez celu trendowego | **174 514** | 57 317 | 11 206 |
| s_23 | mikrocena zamiast mid | 145 210 | 87 997 | 20 935 |
| s_24 | mikrocena + MLOFI zamiast prognozy | 146 942 | 80 272 | 21 549 |
| s_25 | kara φ = γσ²/2 (γ 0,01, min 0,005) | **165 320** | 84 869 | 22 898 |
| s_26 | asymetryczna bramka VPIN | 142 883 | 85 668 | 20 970 |
| s_27 | zamrożenie strony 250 ms po agresorze ≥ 500 | 134 437 | **93 350** | 21 166 |
| s_28 | bramka zmienności → RECOVERY | 149 143 | 87 788 | 21 015 |
| s_29 | ochrona pozycji w kolejce (1 tick) | 102 750 | 66 629 | 21 319 |
| s_30 | cel trendowy ±50 | 169 916 | 71 570 | 15 276 |
| s_31 | φ + trend ±50 | **175 288** | 65 963 | 16 060 |
| s_32 | φ + zamrożenie | 153 177 | 86 452 | 22 358 |
| s_33 | trend ±50 + zamrożenie | 159 660 | 76 271 | 15 410 |
| s_34 | φ + trend ±50 + zamrożenie | 165 072 | 68 825 | 15 655 |
| s_35 | φ + trend ±75 | 173 051 | 72 578 | 19 163 |
| s_36 | φ z γ 0,02 | 155 155 | 82 716 | 23 048 |

## Wnioski

- **Teza „trend szkodzi” jest fałszywa dla R2.** Cel trendowy kosztuje ok. 25 tys. na R1
  (brak silnych trendów), ale daje ok. 34 tys. na R2 publicznej. Na prywatnej R2 (trend w górę)
  `koziol.py` z pełnym trendem zarobił +28,8 tys., a maker bez trendu (s_20) stracił 10,8 tys.
  Cel trendowy działa więc jak zabezpieczenie na rynek z trendami, a R2 jest takim rynkiem.
- **Kara za zapas φ = γσ²/2 to jedyna zmiana z dokumentu, która wyraźnie pomaga.** Daje
  +16 tys. na R1 (ok. 2,5 SE) i −6 tys. na R2 (0,3 SE, szum). Silniejsza kara (γ 0,02) jest
  gorsza.
- **Mikrocena, MLOFI i VPIN nie poprawiają wyniku.** Prognoza 11 cech daje ok. 1–3 tys.
- **Ochrona pozycji w kolejce szkodzi wyraźnie** na obu taśmach, tak samo jak wcześniej
  u makerów.
- **Bramka zmienności niczego nie zmienia na R1** (nigdy się tam nie włącza), a na R2 jest
  w granicach szumu.
- **Zamrożenie strony pomaga na R2** (+2 tys., szum), ale kosztuje 15 tys. na R1.

## Rekomendacja

- **Główny kandydat: s_25,** czyli koziol.py z karą zależną od zmienności i pełnym trendem.
  Ma najlepszą sumę R1 + R2 i nie traci na R2 ponad szum.
- **Alternatywy:**
  - `koziol.py` bez zmian: jedyny z wynikiem na prywatnej walidacji (+28 827);
  - s_35: trend ±75, mniejszy rozrzut na R2, ale −12 tys. względem s_25 na R2 publicznej.
- **Przed wyborem:** wgrać s_25 na walidację prywatną i porównać z +28 827 `koziol.py`.

## Ograniczenia

- R2 publiczna ma se ok. 21 tys., więc różnic między wariantami poniżej ok. 20 tys. nie da się
  na niej rozstrzygnąć.
- Wagi prognozy koziol.py pochodzą z nieznanego zbioru.
- Nie było walidacji wariantów w sandboksie serwera.
