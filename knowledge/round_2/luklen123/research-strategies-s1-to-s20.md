# Strategie s_1–s_20: mechanizmy z researchu, kombinacje i hybrydy pod R2

Pytanie: które mechanizmy z `round2-strategies-research.txt` poprawiają makera na publicznej
taśmie R2, oraz jak je połączyć?

## Dane i metoda

- Taśma R2 public: SHA-256 `88ff641e…cfb9f4`, 6000 s. Symulator oficjalny, niezmieniony.
- Kod: wspólny silnik `engine_template.py`. `generate.py` wypisuje z niego samodzielne pliki
  `strategies/s_<i>.py`, każdy z maks. 3-zdaniowym opisem na górze. Siatki parametrów robi
  `sweep.py`, a przebiegi `run_files.py`. Wszystko leży w
  `experiments/round_2/luklen123/20261107-research-strategies-001/`.
- Kontrola: silnik z ustawieniami s1 daje wynik identyczny z `strategies/s1.py`
  (+1816, 9111 filli).
- H1 i H2 to połowy taśmy, policzone z wyceny PnL co 1 s z pełnego przebiegu (stan księgi
  zachowany).
- Przy optymalizacji pod R2 (na prośbę) wybierano środek obszaru dobrych wyników, a nie
  pojedynczy rekord.
- Poprawka do researchu: stała w statystyce testu skoków (Barndorff-Nielsen i Shephard) to
  (π/2)² + π − 5 ≈ 0,609, a nie „+π−3”.

## Wyniki: mechanizmy pojedyncze i kombinacje (R2)

| Plik | Mechanizm | PnL | H1 / H2 | maxDD |
|---|---|---|---|---|
| s_1 | bramka spread = 1 + zmienność ≤ 2,5 | **2116** | 1174 / 942 | 186 |
| s_2 | strażnik pozycji w kolejce (bez bramki) | −777 | 757 / −1534 | 2827 |
| s_3 | progowa kontrola zapasu 5/15/25, 1 lot | −1657 | | 1998 |
| s_4 | stop 2 ticki przez IOC | −7884 | | 8309 |
| s_5 | zamrożenie strony 250 ms po agresorze ≥ 500 | −1984 | | 3171 |
| s_6 | bramka VPIN | −3688 | | 4203 |
| s_7 | test skoków bipower | −3733 | | 3937 |
| s_8 | intensywność dużych agresorów (proxy Hawkesa) | 846 | 452 / 394 | 1239 |
| s_9 | pełna architektura z researchu | 377 | 125 / 252 | 112 |
| s_10 | s1 + strażnik kolejki | 1432 | | 234 |
| s_11 | s1 + zamrożenie strony | **2123** | 1290 / 833 | 247 |
| s_12 | s1 + VPIN | 1480 | | 302 |
| s_13 | s1 + test skoków | 727 | | 284 |
| s_14 | s1 + intensywność dużych agresorów | 1813 | | 286 |
| s_15 | s1 + progowa kontrola zapasu | 828 | | 155 |
| s1 | kontrola | 1816 | 1116 / 700 | 286 |
| zubry_v2 | punkt odniesienia | −4032 | | 4563 |

Pomagają tylko dwa mechanizmy: **bramka reżimu** oraz **zamrożenie strony po dużym agresorze**.
Pozostałe szkodzą:

- **Stop przez IOC** płaci spread dokładnie w złym momencie.
- **VPIN i test skoków** wyłączają kwotowanie w okresach, które były zyskowne.
- **Strażnik kolejki** wycofuje zlecenie tuż przed wypełnieniem przez małych agresorów.
- **Progowa kontrola zapasu** i kwotowanie po 1 locie zmniejszają zysk, a ryzyka praktycznie
  nie ograniczają, bo zapas i tak jest mały.

## Optymalizacja hybrydy pod R2 (siatki 1–5, łącznie 85 wariantów)

1. **Siatka 1:** próg zmienności {2,0; 2,5; 3,0} × okno {30; 60} × zamrożenie {brak; 500; 1000}
   × intensywność {wył.; wł.}. Wszystkie 36 wariantów wyszły na plus, z obiema połowami
   dodatnimi. Średni wpływ parametrów:

   | Parametr | Średni PnL |
   |---|---|
   | okno 30 s | 2745 |
   | okno 60 s | 2153 |
   | zamrożenie po ≥ 500 lotach | 2567 |
   | bez zamrożenia | 2350 |
   | próg zmienności 2,0 | 2549 |
   | próg zmienności 3,0 | 2329 |

   Bramka intensywności nie daje różnicy (efekt ≈ 0).
2. **Siatka 2:**
   - Okno 15–20 s z progiem 1,5–2,5 daje 2900–3150; zamrożenie 250 ms jest lepsze niż 500 ms.
   - Przesunięcie ceny względem zapasu ustawione na 0 daje 3618, ale z maxDD 1265, więc
     odrzucone.
   - **Wielkość kwotowania działa niemal liniowo:** 1 lot → 1453, 2 → 2885, 3 → 3994,
     4 → 5002.
3. **Siatki 3–5:** wielkość kwotowania (zmienność 2,0, okno 20, zamrożenie 500/250 ms,
   limit zapasu ≤ 90):

| Kwotowanie | Limit zapasu | PnL | H1 / H2 | pnl_se | maxDD | Zapas (q99,7) |
|---|---|---|---|---|---|---|
| 4 | 40 | 5 576 | 3 442 / 2 134 | 632 | 474 | 8 |
| 10 | 80 | 11 393 | 6 899 / 4 494 | 1 408 | 1 711 | 20 |
| 20 | 80 | 24 053 | 11 979 / 12 074 | 2 958 | 2 208 | 38 |
| 30 | 90 | 29 234 | 17 887 / 11 347 | 3 683 | 3 137 | 49 |
| 50 | 90 | 45 141 | 25 487 / 19 654 | 7 129 | 3 510 | 66 |
| 60 | 90 | 45 791 | | 8 403 | 7 495 | 76 |
| 75 | 90 | 48 354 | | 10 144 | 11 477 | 89 |

- **Skąd liniowość:** taśma nie reaguje na nasze zlecenia. Większe zlecenie na końcu kolejki
  bierze większy kawałek każdego sweepa, który do niego dojdzie, a przewaga na lot pozostaje
  dodatnia.
- **Ryzyko na jednostkę zysku rośnie.** PnL/pnl_se spada z ~10 przy 2 lotach do ~6 przy
  50 lotach. Powyżej 50 lotów zysk się wypłaszcza, a drawdown rośnie gwałtownie.
- **Wrażliwość przy 50 lotach:** sąsiednie ustawienia bramki dają 36–41 tys., a bez
  zamrożenia 36 tys. Przy dużym kwotowaniu zamrożenie ma znaczenie.
- Zapas nie może przekroczyć limitu: strategia przy każdym zleceniu sprawdza, ile zostało do
  limitu, a zapasu nie zmienia żadne zlecenie IOC. Limit ≤ 90 wyklucza karę przy ±100.

Finalne hybrydy mają tę samą bramkę i różnią się tylko wielkością kwotowania:
s_16 = 4 loty, s_17 = 10, s_18 = 20, s_19 = 30, s_20 = 50.

## Walidacja na prywatnym zbiorze: s_20 (wynik negatywny)

Statystyki z serwera przekazał użytkownik 2026-11-07:

| | Publiczna R2 | Prywatny zbiór walidacyjny |
|---|---|---|
| Fille | 8 018 | 14 844 |
| Wolumen | 353 070 | 647 192 |
| Pozycja końcowa | 0 | −20 |
| Gotówka | — | 198 859 |
| Cena wyceny końcowej | — | 10 482 |
| Kara | 0 | 0 |
| pnl_se | 7 129 | 14 714 |
| Zapas q50 / q68 / q95 / q99,7 | — / — / — / 66 | 13 / 25 / 46 / 68 |

**PnL = 198 859 − 20 × 10 482 = −10 781** (publicznie +45 141).

- **Przewaga na lot:** +0,128 ticka publicznie, −0,017 ticka na prywatnym (z ≈ −0,73).
- **Przewaga makera nie przeniosła się na inną ścieżkę.** Wielkość kwotowania tylko ją
  przemnożyła. Kontrola zapasu zadziałała: brak kary, zapas taki jak publicznie.
- **Prywatna ścieżka wygląda na inny reżim.** Cena prawdopodobnie wzrosła o ~480 ticków.
  To szacunek przy założeniu startu przy ~10 000, jak na obu znanych taśmach. Do tego było
  ~1,85× więcej filli, czyli bramka częściej była otwarta.
- **Wniosek:** wybór parametrów pod jedną publiczną ścieżkę był przeuczony. Kolejne warianty
  muszą być dodatnie na R1 i R2 jednocześnie. Do zbadania jest bramka lub przesunięcie
  kwotowań zależne od dryfu (kierunku), nie tylko od zmienności.

## Ograniczenia

- Wszystko to wyniki in-sample na jednej 100-minutowej publicznej ścieżce, wybrane spośród
  ~100 wariantów, więc najlepsze liczby są optymistyczne.
- Prywatna taśma R2 to inna ścieżka. Wielkość kwotowania mnoży przewagę na lot, ale też
  ewentualną stratę.
- Regulamin liczy ujemny PnL rundy jako 0, co premiuje większą wariancję. Mimo to wybór
  między s_17 a s_20 to decyzja o apetycie na ryzyko, nie wniosek z danych.
- Hybryd nie testowano na R1, bo optymalizacja była pod R2 (na prośbę). Nie było też walidacji
  w sandboksie serwera.
