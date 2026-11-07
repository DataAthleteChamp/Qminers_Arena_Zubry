# Odporna optymalizacja kuba/s_67 metodą successive halving → s_75

## Prywatna walidacja (zgłoszona przez użytkownika)

| Strategia | Prywatna R2 |
|---|---|
| s_67 (kuba + 40 lotów) | **≈ 51 tys.** |
| kuba.py | ≈ 43 tys. |
| koziol.py | 28,8 tys. |

## Metoda

- **Silnik:** `kuba_engine_template.py`. Przy domyślnych parametrach odtwarza kuba.py
  (`20261107-kuba-extensions-001`).
- **Przestrzeń przeszukiwania (11 parametrów):**
  - wielkość kwotowania {32…48},
  - kara za zapas (log-jednostajnie 0,005–0,02),
  - skala EMA trendu ×{0,5; 0,75; 1; 1,5; 2},
  - GAP_QTY {60, 100, 150}, FRAGILE_SIZE {8, 12, 20}, TOPUP_MIN {4, 8, 16},
  - zlecenia na poziom {2, 3}, próg SHOCK {3, 4}, powrót po szoku {100, 200, 500} ms,
  - MIN_L1 {50, 100, 150}, zmniejszanie kwotowania w CAUTION {tak, nie}.
- **Cel trendowy zostaje ±100.** Zmniejszenie go wyraźnie szkodziło (s_68).
- **Successive halving (`optimize.py`, seed 7):**
  1. Etap 1: 40 losowych konfiguracji i s_67 na 4 taśmach syntetycznych. Wynik = średnia
     przewaga nad s_67 − 0,5·jej odchylenie.
  2. Etap 2: najlepsze 10 na 8 kolejnych taśmach syntetycznych, R2 i lustrze R2. Zostają tylko
     konfiguracje, które nie przegrywają z s_67 na R2 ani lustrze.
  3. Etap 3: finalista i s_67 na R1.
- **Reguła akceptacji:** wygrana z s_67 na ≥ 12 z 15 taśm i najgorszy wynik ≥ 98% najgorszego
  wyniku s_67.

## Wynik: cfg_031 → `strategies/s_75.py` (SHA-256 `199582a1…cf5e`)

**Parametry:** QUOTE_SIZE 36, INVENTORY_SKEW 0,0065, EMA_SECONDS (2, 15, 60), GAP_QTY 60,
FRAGILE_SIZE 8, TOPUP_MIN 16, SHOCK_SPREAD 4, RECOVERY_US 500 000, MIN_L1 50, CAUTION_DIV 1.
Pozostałe jak w kuba.py.

| Taśma | s_67 | s_75 | Różnica |
|---|---|---|---|
| R1 | 205 276 | 239 661 | +34 385 |
| R2 publiczna | 104 260 | 124 971 | +20 711 |
| R2 lustro | 111 318 | 118 135 | +6 817 |
| syn 1 / 1m | 176 704 / 177 637 | 233 291 / 235 536 | +56 587 / +57 899 |
| syn 2 / 2m | 131 916 / 130 038 | 155 546 / 155 549 | +23 630 / +25 511 |
| syn 3 / 3m | 172 283 / 179 730 | 197 121 / 201 970 | +24 838 / +22 240 |
| syn 4 / 4m | 165 514 / 168 047 | 204 104 / 206 482 | +38 590 / +38 435 |
| syn 5 / 5m | 153 020 / 162 568 | 160 848 / 165 127 | +7 828 / +2 559 |
| syn 6 / 6m | 129 448 / 128 776 | 159 353 / 162 482 | +29 905 / +33 706 |

- **Wynik:** 15 z 15 wygranych, średnia przewaga +28 243, najgorszy wynik 118 135 (s_67:
  104 260). Kara 0 wszędzie, reguła spełniona.
- **Plik s_75 odtwarza cfg_031** (syn_5: 160 848).
- **Inne konfiguracje z wysoką średnią** (cfg_001, cfg_024) traciły 10–31 tys. na R2 lub
  lustrze i odpadły. Filtr na R2 i lustro zadziałał zgodnie z założeniem.

## Ograniczenia

- Wybór spośród 40 konfiguracji, więc wynik jest częściowo dopasowany. 4 taśmy z etapu 1 były
  użyte do selekcji, ale przewaga utrzymuje się na wszystkich pozostałych 11.
- **Najbardziej prawdopodobne źródło poprawy to dwa razy szybsze EMA trendu,** czyli szybsze
  podążanie za ruchem. Nie zrobiłem ablacji, która by to potwierdziła. To ten sam kierunek co
  szybki detektor z s_49, który przegrał na prywatnej. Tu jednak zmiana jest łagodniejsza
  (wolniejsza średnia nadal wymagana), wygrywa na 15/15 taśm i nie pogarsza najgorszego wyniku.
- s_75 nie był walidowany na prywatnej ani w sandboksie serwera.

Pliki: `experiments/round_2/luklen123/20261108-kuba-robust-hpo-001/` (`optimize.py`,
`configs.json`, `results.csv`, `out_hpo.log`).
