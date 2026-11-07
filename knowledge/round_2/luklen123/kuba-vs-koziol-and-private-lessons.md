# kuba.py kontra koziol.py i s_49: wnioski z prywatnej walidacji R2

## Prywatna walidacja R2 (PnL zgłoszone przez użytkownika)

| Strategia | Prywatna R2 |
|---|---|
| kuba.py | **≈ +43 tys.** |
| koziol.py | +28 827 |
| s_20 | −10 781 |
| s_49 | **≈ −16 tys.** |

## Czym kuba.py różni się od koziol.py

`strategies/kuba.py` (plik zespołu, SHA-256 `eea52c9d…`) ma ten sam rdzeń co koziol.py: prognozę
11 cech, cel trendowy EMA 3/30/120 s, stałą karę 0,01, grid 3×32 i stany. Dodaje dwa
mechanizmy wykonania:

- **`FIFO_TOPUPS`:** częściowo wypełniony poziom gridu dostaje drugie zlecenie uzupełniające
  (jeśli brakuje ≥ 8 lotów, maks. 2 zlecenia na poziom). Pierwotne zlecenie zachowuje miejsce
  w kolejce, a poziom wraca do pełnej wielkości.
- **`GAP_GUARD`:** jeśli najlepszy poziom ma ≤ 100 lotów, a następny jest ≥ 2 ticki dalej,
  strona jest „krucha”. Kwotowanie spada tam do 12 lotów, a nadmiar jest anulowany. To lokalna
  ochrona przed przeskokiem ceny przez lukę w księdze.

## Porównanie na 15 taśmach (oficjalny symulator, kara 0 wszędzie)

| Taśma | koziol | kuba | tylko top-ups | tylko gap guard | s_41 | s_49 |
|---|---|---|---|---|---|---|
| R1 | 149 143 | **183 477** | 183 811 | 148 831 | 165 471 | — |
| R2 publiczna | 91 025 | **103 998** | 100 195 | 95 005 | 100 157 | 100 148 |
| R2 lustro | 89 365 | **108 222** | 100 368 | 96 961 | 98 305 | 97 689 |
| Syntetyczne: mediana | 155 920 | **162 727** | 159 841 | 158 625 | 156 534 | 156 906 |
| Syntetyczne: minimum | 123 583 | 123 920 | **124 938** | 121 024 | 89 270 | 89 631 |

- **kuba.py bije koziol.py na 15 z 15 taśm.**
- **Top-ups daje większość zysku:** R1 +34 tys., R2 +9 tys., lustro R2 +11 tys.
- **Gap guard dokłada głównie na R2 i jej lustrze.** Razem z top-ups daje najlepszy wynik
  na obu.
- **s_41 i s_49 nie mają tej spójności.** Na R2, jej lustrze i części syntetycznych są lepsze,
  ale na `syn_1m` i `syn_2m` gorsze (najgorszy wynik 89 tys. wobec 124 tys.). Na prywatnej
  przegrały z koziol o ~45 tys.

## Wnioski

1. **Na prywatnej zadziałały poprawki wykonania** (utrzymanie miejsca i wielkości w kolejce,
   ochrona przed luką), a nie nowe warstwy sygnałów (detektor ruchu, IOC, kara zależna od σ).
2. **Kryterium, które przewidziałoby kolejność na prywatnej:** wariant musi bić bazę na prawie
   każdej taśmie, a jego najgorszy wynik nie może być gorszy od najgorszego wyniku bazy.
   Wyższa średnia albo lepszy wynik na R2 publicznej nie wystarcza. kuba.py to kryterium
   spełnia; s_41 i s_49 nie (najgorszy wynik 89 tys. wobec 124 tys.).
3. **Następne kroki:** kolejne poprawki wykonania budować na kuba.py i odrzucać wszystko, co
   nie spełnia kryterium z punktu 2.

Pliki: `experiments/round_2/luklen123/20261107-kuba-crosscheck/` (kopie, ablacje,
`matrix_kuba.csv`, `out_compare.log`).
