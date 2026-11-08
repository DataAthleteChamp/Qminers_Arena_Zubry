# Strategie na rynek z częstymi, głębokimi zmianami kursu (s_43–s_53)

Pytanie: które mechanizmy pozwalają przetrwać, a najlepiej zarobić na rynku z częstymi
głębokimi ruchami w obie strony? Oceniane na wielu ścieżkach, a nie na jednej publicznej taśmie.

## Stanowisko testowe (14 taśm, oficjalny symulator)

- **R2 publiczna i jej lustro.** Lustro: cena → 20 000 − cena, strony B/A zamienione, czyli ta
  sama mikrostruktura z odwróconym kierunkiem (`mirror_tape.py`).
- **6 syntetycznych taśm kryzysowych po 1800 s i ich 6 luster** (`gen_crash_tape.py`, seedy 1–6).
  - Ukryta wartość godziwa z epizodami spadku lub wzrostu (50/50) co ~5 min: dryf 1,5–4
    tick/s przez 40–200 s, skoki, w 40% przypadków częściowe odbicie.
  - Makerzy poszerzają kwotowania i wycofują płynność w epizodzie; poinformowani agresorzy
    pchają cenę.
  - Profil seed 1: σ zmian mid 1 s 3,83 (R2: 3,80), spread 1 tick przez 73% czasu, L1 ~80
    lotów, σ ruchu w 60 s 118 (R2: 32). Głębokie ruchy są więc dużo częstsze niż w R2.
- **Lustra sprawiają, że zestaw jest neutralny kierunkowo z założenia.** Strategie z silnika
  kryzysowego dają identyczny wynik na oryginale i lustrze, co potwierdza symetrię kodu.
- **Zastrzeżenie:** generator ma wbudowane trwałe epizody trendu, więc przecenia czyste
  podążanie za trendem. Rozstrzygające są R2 i lustro R2.

## Strategie

- **Silnik kryzysowy** (`crash_engine_template.py`, wszystkie progi względne):
  - **s_43, jeździec:** detektor ruchu 2σ√20 → wejście IOC na 60 lotów, wyjście trailing stopem
    1,5σ√20, po 300 s albo przy odwrotnym sygnale;
  - **s_44:** maker 5 lotów z bezpiecznikiem (detektor lub drenaż L1 → wycofanie kwotowań
    i zamknięcie pozycji IOC);
  - **s_45:** to samo co s_44, ale bez zamykania pozycji;
  - **s_46:** maker + jazda;
  - **s_47:** maker + jazda + bezpiecznik;
  - **s_48:** sam maker (kontrola).
- **Rodzina koziol** (`koziol_engine_template.py`):
  - **s_49:** s_41 + natychmiastowe wejście IOC 100;
  - **s_50:** s_41 z progiem detektora tylko względnym (min. 5 ticków);
  - **s_51:** s_50 + IOC 100;
  - **s_52:** s_41 + ostrzeżenie o drenażu → RECOVERY;
  - **s_53:** koziol + ostrzeżenie o drenażu.
- **Odniesienia:** koziol.py, s_25, s_41, s1.
- **Ostrzeżenie o drenażu:** 5-sekundowa średnia głębokości L1 < 35% średniej 120 s. Na R2 to
  3,9% czasu, a kolejny ruch w ciągu 60 s jest wtedy średnio 2× większy (38 wobec 19 ticków).
  Na syntetycznych: 14% czasu, ruch 169 wobec 81. To wczesny sygnał skali ruchu, nie kierunku.
  Pierwsza wersja (surowe L1 albo spread ≥ 3) odpalała się przez większość czasu i blokowała
  makera: 0 transakcji.

## Wyniki (PnL, kara 0 we wszystkich 210 przebiegach)

| Strategia | Syntetyczne: średnia / mediana / min / dodatnie | Wzrosty / spadki (średnia) | R2 | Lustro R2 |
|---|---|---|---|---|
| s_49 | 150 542 / 156 906 / 89 631 / 12 z 12 | 153 576 / 147 509 | 100 148 | 97 689 |
| s_41 | 149 169 / 156 534 / 89 270 / 12 z 12 | 152 468 / 145 870 | 100 157 | 98 305 |
| koziol.py | 149 662 / 155 920 / **123 583** / 12 z 12 | 147 962 / 151 362 | 91 025 | 89 365 |
| s_52 | 148 588 / 155 452 / 90 029 / 12 z 12 | 151 967 / 145 209 | 99 879 | 98 033 |
| s_51 | 150 028 / 155 009 / 88 437 / 12 z 12 | 153 104 / 146 952 | 100 576 | 96 594 |
| s_50 | 148 413 / 154 108 / 88 247 / 12 z 12 | 151 659 / 145 167 | 96 054 | 97 109 |
| s_53 | 148 400 / 153 790 / 122 181 / 12 z 12 | 146 665 / 150 134 | 89 871 | 88 456 |
| s_25 | 147 053 / 152 680 / 120 174 / 12 z 12 | 145 323 / 148 783 | 84 869 | 85 232 |
| s_43 jeździec | 85 779 / 82 496 / 58 801 / 12 z 12 | identyczne | **−14 654** | −14 654 |
| s_47 hybryda kryzysowa | 80 009 / 81 955 / 60 692 / 12 z 12 | identyczne | −10 734 | −10 734 |
| s_46 maker + jazda | 55 332 / 54 610 / 21 116 / 12 z 12 | identyczne | −12 794 | −12 794 |
| s_44 maker + bezpiecznik | 2 189 / 1 840 / 467 / 12 z 12 | identyczne | **4 480** | 4 480 |
| s1 | 1 004 / 1 038 / 674 / 12 z 12 | identyczne | 1 816 | 1 816 |
| s_48 sam maker | 270 / 394 / −3 528 / 10 z 12 | identyczne | 524 | 524 |
| s_45 maker bez zamykania | −3 830 / −1 998 / −19 278 / 4 z 12 | identyczne | 4 471 | 4 471 |

Średni maxDD na taśmach syntetycznych: koziol 44 tys., s_41 51 tys., s_44 3,5 tys.,
s_43 2 tys.

## Wnioski

1. **Najlepiej działa rodzina koziol: cel trendowy, grid i kara za zapas.** Jest dodatnia na
   wszystkich 14 taśmach i na lustrze R2 daje prawie tyle samo co na oryginale, więc jej wynik
   nie zależy od kierunku.
   - Detektor startu ruchu (s_41, s_49) podnosi średnią i wynik na R2 (+9 tys. w obu
     kierunkach), ale obniża minimum: na `syn_2m` −35 tys. przez fałszywe sygnały przy odbiciach.
   - koziol.py bez detektora ma najlepsze minimum i najmniejszy drawdown.
2. **Czyste jeżdżenie na krachu (s_43, s_46, s_47) nie przenosi się na prawdziwą R2.** Na R2
   i lustrze traci 10–15 tys., mimo zysku na syntetycznych, które z konstrukcji mają trwałe
   trendy. Wejście IOC po wykryciu płaci spread przy rozszerzonym rynku, a ruchy w R2 są
   bardziej poszarpane.
3. **Obronna ręka dla makera:** bezpiecznik z zamknięciem pozycji (s_44) zamienia stratę
   samego makera w mały, stabilny zysk (12/12 dodatnich, R2 +4,5 tys., maxDD 1,2 tys.).
   Samo wycofanie kwotowań bez zamknięcia (s_45) jest najgorsze. **Przygotowanie bez wyjścia
   z pozycji nie chroni.**
4. **Ostrzeżenie o drenażu jest prawdziwym sygnałem skali,** ale w koziol nic nie dokłada
   (s_52 ≈ s_41, s_53 ≈ koziol): jego maszyna stanów już ogranicza kwotowania w szoku.

## Rekomendacja

- **Rynek z częstymi głębokimi ruchami:**
  - s_41 lub s_49, jeśli liczy się wynik;
  - koziol.py, jeśli liczy się najgorszy scenariusz.
- **Wariant niskiego ryzyka:** s_44. Mały, ale stabilny zysk i bardzo mały drawdown.
- **Czysty jeździec:** tylko jako badanie; na prawdziwych danych traci.

## Ograniczenia

- Taśmy syntetyczne pochodzą z mojego prostego modelu agentowego, z ukrytym trendem w
  epizodach i cieńszą płynnością niż R2. Bezwzględne liczby są więc tylko orientacyjne.
- Lustro R2 to ta sama ścieżka z odwróconym kierunkiem, a nie nowe dane.
- Pliki: `experiments/round_2/luklen123/20261107-deep-move-strategies-001/` (generator, lustra,
  silnik, macierze `matrix_*.csv`, `out_*.log`). Taśmy nie są commitowane.
