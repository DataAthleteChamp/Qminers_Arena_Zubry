# Zbiór `round2_public.csv`: podsumowanie i charakterystyka

Notatka opisuje publiczną taśmę rynku z rundy 2 i wnioski z niej dla budowy strategii.
Szczegółowa analiza (po angielsku) jest w `round2-public-tape-profile.md`, a backtesty
strategii w `s1-regime-gated-maker.md`. Wszystkie liczby to statystyki **in-sample** z jednej
publicznej ścieżki. Nic tu nie mówi o wyniku na danych prywatnych.

## 1. Metryka pliku

| | |
|---|---|
| Ścieżka | `data/round2/round2_public.csv` (surowe dane, nieśledzone przez git, niezmieniane) |
| Rozmiar | 78 512 311 B, 2 193 064 wiersze danych + nagłówek |
| SHA-256 | `88ff641e962540c66fa1cc4a3547585d31838d0929340150690cabb4f3cfb9f4` |
| Zakres czasu | 0,000067 – 5999,996013 s, czyli **6000 s (100 min)** |
| Instrument | jeden, zanonimizowany: nie wyciągamy wniosków o aktywie z poziomu ceny |

## 2. Format i znaczenie kolumn

`Time,Operation,OrderId,Side,Volume,Price,Lifespan`

| Kolumna | Znaczenie |
|---|---|
| `Time` | sekundy z rozdzielczością µs. Rosną ściśle monotonicznie i nie ma dwóch zdarzeń w tej samej chwili. W callbackach symulatora czas jest w µs. |
| `Operation` | `Insert` (nowe zlecenie) albo `Cancel` (usunięcie po `OrderId`; pozostałe pola są wtedy puste) |
| `OrderId` | unikalne ID zlecenia, bez duplikatów wśród wstawień |
| `Side` | `B` = kupno (bid), `A` = sprzedaż (ask) |
| `Volume` | liczba lotów, liczba całkowita ≥ 1 |
| `Price` | cena w tickach, liczba całkowita (tick = 1) |
| `Lifespan` | `G` = limit rezydujący w księdze (GTC), `F` = IOC (reszta niewypełniona przepada) |

Taśma zawiera wyłącznie zlecenia. **Transakcji w niej nie ma**: powstają w trakcie
odtwarzania, gdy `Insert` krzyżuje się z drugą stroną księgi. Obowiązuje priorytet ceny, potem
czasu, a transakcja zawiera się po cenie zlecenia, które już stało w księdze. Taśma nie reaguje
na nasze zlecenia.

## 3. Skład zdarzeń

| | Liczba | Udział |
|---|---|---|
| Insert | 1 123 282 | 51,2% |
| Cancel | 1 069 782 | 48,8% |
| Insert po stronie B / A | 561 544 / 561 738 | ~50 / 50 |
| Insert typu G / F (IOC) | 1 069 859 / 53 423 | 95,2% / 4,8% |

- Średnio ~366 zdarzeń na sekundę, a tempo jest stałe we wszystkich blokach 10-minutowych
  (~112 tys. Insert i ~107 tys. Cancel na blok).
- Odstęp między zdarzeniami: średnio 2,7 ms, mediana 1,8 ms, p99 14 ms, maksimum 0,17 s.
  To mniej więcej tyle samo co nasze opóźnienie 5 ms, więc **w czasie naszej reakcji rynek
  zdąży wykonać kilka zdarzeń**.
- 150 476 anulowań (14% wszystkich) dotyczy zleceń, które były już w całości wypełnione. Są
  nieszkodliwe (puste operacje); tak samo było w R1.

## 4. Rozmiary i ceny zleceń

- Wolumen jednego zlecenia: mediana 15, Q1 = 4, Q3 = 52, p90 = 155, p99 = 985, maksimum 72 482.
  Najczęstsze wartości to 1, 2, 3… lotów, a rozkład ma bardzo długi ogon.
- Ceny wstawień mieszczą się w przedziale 9444–10017.
- Gdzie stają nowe zlecenia rezydujące (odległość od najlepszej ceny po tej samej stronie):

  | Miejsce | Udział |
  |---|---|
  | dołączenie do najlepszej ceny | 49% |
  | 1 tick za najlepszą ceną | 34% |
  | 2 ticki za | 7% |
  | wewnątrz spreadu (poprawiające cenę) | 1,4% |

- „Ściany” (zlecenia ≥ 2000 lotów stające na najlepszej cenie, n = 1679) żyją ~0,3 s i są
  wypełniane tylko w ~2%. Ich wpływ na kierunek ceny wynosi najwyżej 0,18 ticka, czyli **nie
  są użytecznym sygnałem**.

## 5. Księga zleceń (odtworzona)

| Miara | Wartość |
|---|---|
| Spread (udział czasu) | 1 tick 83,9% · 2 ticki 11,6% · 3 ticki 3,1% · ≥4 ticki 1,5% |
| Księga skrzyżowana lub zablokowana | nigdy |
| Wolumen na najlepszej cenie (L1), bid | p10 = 55, **mediana 713**, p90 = 2592 lotów |
| Wolumen na najlepszej cenie (L1), ask | p10 = 57, **mediana 743**, p90 = 2609 lotów |
| Czas, przez który najlepszy bid stoi na jednej cenie | mediana 0,13 s, p90 1,2 s |
| Czas życia zleceń GTC | mediana 0,29 s, p90 0,89 s, p99 1,95 s |
| Wypełnienie wolumenu GTC | 9% (reszta jest anulowana) |

Kolejka na najlepszej cenie jest głęboka, ok. 700 lotów. Rynek bardzo szybko wymienia
zlecenia, więc nasze małe zlecenie trafia na koniec długiej kolejki, ale stojący przed nim
wolumen szybko znika przez anulowania.

## 6. Dynamika ceny

Środek kwotowań (mid) zaczyna na 10000,0 i kończy na 9689,5. Minimum to 9455,0, maksimum
10007,5, czyli **zakres 552 ticków**.

| Blok (10 min) | Mid start → koniec | Min – max | σ zmiany mid w 1 s | Średni spread |
|---|---|---|---|---|
| 0 | 9998,5 → 9900,5 | 9899,5 – 10001,5 | 2,45 | 1,22 |
| 1 | 9901,5 → 9875,5 | 9858,5 – 9905,5 | 1,32 | 1,11 |
| 2 | 9874,5 → 9912,5 | 9842,0 – 9955,5 | 3,02 | 1,16 |
| 3 | 9912,5 → 9899,5 | 9843,5 – 9946,5 | 3,68 | 1,27 |
| 4 | 9899,5 → 9923,5 | 9899,5 – 10000,0 | 3,39 | 1,18 |
| 5 | 9923,5 → 9943,5 | 9921,5 – 10007,5 | 3,02 | 1,11 |
| **6** | **9945,5 → 9584,5** | 9582,0 – 9949,5 | **6,17** | **1,65** |
| 7 | 9582,5 → 9480,0 | 9459,0 – 9584,0 | 2,80 | 1,25 |
| 8 | 9479,5 → 9680,0 | 9475,5 – 9680,0 | 5,19 | 1,14 |
| 9 | 9682,5 → 9690,5 | 9647,0 – 9824,5 | 4,46 | 1,45 |

- **Zmienność:** σ zmiany mid wynosi 3,8 ticka na 1 s, 12,2 na 10 s, 31,7 na 60 s i 142 na
  600 s.
- **Iloraz wariancji** (wariancja zmiany na horyzoncie h podzielona przez h × wariancję
  zmiany 1 s) wynosi ~1,0 do 10 s, a potem rośnie: 1,16 przy 60 s, 1,78 przy 300 s, 2,35 przy
  600 s. Na długich horyzontach ruchy są trwałe, ale tę wartość ciągnie głównie krach z bloku 6.
- **Krachy i odbicia:** największe ruchy w ciągu 60 s to −145, −128, −111, +128, +116 i
  +102 ticki. W trakcie takiego ruchu średni spread wynosi 2–3 ticki, a wolumen na najlepszej
  cenie spada do ~120–190 lotów.
- **Grupowanie zmienności:** okresy, w których σ z ostatnich 60 s przekracza 3, zajmują 31%
  czasu, jest ich 24, a typowy trwa ~60 s (mediana). Bieżący spread sam przewiduje skalę ruchu:
  średni |ruch mid w ciągu 10 s| to 4,7 ticka przy spreadzie 1, 10,9 przy spreadzie 2, 14,2 przy
  spreadzie 3 i 29 przy spreadzie ≥4.
- **Mikrostruktura:** mid zmienia się w 29 107 zdarzeniach. 83% tych zmian to 0,5 ticka (zmiana
  jednej strony). Kolejne zmiany mają ten sam kierunek z autokorelacją znaku **+0,24**, czyli
  idą seriami, a nie odbijają się w tę i z powrotem.
- **Trendu nie warto grać.** Zbiorcza korelacja odchylenia od średniej 600 s z ruchem w ciągu
  następnych 30 s wynosi +0,13, ale wynika z jednego krachu. W 7 z 9 bloków 10-minutowych jest
  ujemna, czyli cena wraca do średniej.

## 7. Transakcje i agresorzy

- 197 588 transakcji, łącznie 6,999 mln lotów (~1167 lotów na sekundę). Pochodzą z 51 336
  zleceń agresywnych (agresor = zlecenie, które zdejmuje płynność; ~8,6 na sekundę).
- Kupujący stanowią 49,7% wolumenu agresorów, czyli brak trwałej przewagi którejkolwiek strony.
- Rozmiar zlecenia agresora: mediana 58, p90 = 333, p99 = 1170, maksimum 5092 lotów. 7168
  z nich (14%) zjada kilka poziomów cenowych naraz.
- Odstęp między agresorami: średnio 0,117 s, mediana 0,078 s. Autokorelacja kierunku jest słaba:
  0,03 dla kolejnego zlecenia, 0,01 dla dziesiątego.
- Zlecenie, które zostaje wypełnione, stoi w księdze do tego momentu typowo 0,30 s (mediana).

**Zysk makera po transakcji** (ticki na lot, ważone wolumenem): cena transakcji minus mid po
czasie h, ze znakiem z perspektywy makera.

| h | 0 | 5 ms | 50 ms | 0,5 s | 10 s | 60 s | 300 s |
|---|---|---|---|---|---|---|---|
| Zysk makera | +0,58 | +0,49 | +0,24 | −0,38 | −0,53 | −0,49 | −0,98 |

Ten sam zysk po 10 s według rozmiaru agresora:

| Rozmiar agresora (loty) | Zysk makera po 10 s |
|---|---|
| ≤ 18 | **+0,61** |
| 18–41 | +0,37 |
| 41–82 | +0,10 |
| 82–183 | +0,07 |
| > 183 | **−0,49** |

Ten sam zysk po 10 s według zmienności z ostatnich 60 s: od −0,34 do +0,07 w spokojnych
ćwiartkach i **−1,03** w najbardziej zmiennej ćwiartce.

**Dalszy ruch ceny po agresorze**, liczony od t+5 ms (czyli od chwili, gdy możemy zareagować)
do t+10 s, w tickach w kierunku agresora:

| Rozmiar agresora (loty) | Dalszy ruch |
|---|---|
| < 50 | +0,14 |
| 50–200 | +0,52 |
| 200–500 | +0,80 |
| 500–1000 | +1,44 |
| ≥ 1000 | +2,16 |

## 8. Sygnały, których nie ma albo które są słabe

| Sygnał | R2 | Komentarz |
|---|---|---|
| Nierównowaga wolumenu na najlepszych cenach → ruch mid w 1 s | korelacja 0,04 | W R1 było 0,24. **Ten sygnał przestał działać.** |
| Bilans wolumenu agresorów z 5–60 s → ruch mid w 5–60 s | korelacja ≤ 0,05 | słaby |
| Ściany ≥ 2000 lotów | ≤ 0,18 ticka | brak |
| Odchylenie od średniej kroczącej (trend) | znak zmienia się między blokami | niestabilny |
| Granie za agresorem (przekroczenie spreadu po ≥ 300–1000 lotach) | netto ≈ 0 | nieopłacalne poza rzadkim ogonem |

## 9. Porównanie z rundą 1

| | R1 (`round1.csv`, 12 000 s) | R2 publiczna (6000 s) |
|---|---|---|
| Zdarzenia na sekundę, rozkład wolumenów, czas życia zleceń | ~367/s, mediana 15, ~0,31 s | identyczne |
| σ zmiany mid w 1 s | 0,92 | **3,80** |
| Zakres mid | 104 ticki | **552 ticki** |
| Spread = 1 tick | 93% czasu | 84% czasu |
| Mediana wolumenu na najlepszej cenie | ~920 | ~720 |
| Autokorelacja znaku zmian mid | +0,07 | +0,24 |
| Grupowanie zmienności | brak (0,01) | jest (0,20) |
| Zysk makera po 10 s | +0,08 | −0,53 |
| zubry_v2 w oficjalnym symulatorze | **+11 206** | **−4032** |

Wniosek: **ten sam generator zleceń, inny proces ceny.** W R2 doszły okresy wysokiej zmienności,
skoki i krachy. Prywatna taśma R2 prawdopodobnie pochodzi z tego samego procesu, ale kierunek
i moment krachów są nieznane.

## 10. Konsekwencje dla strategii

1. Proste stanie na najlepszej cenie traci, bo małe zlecenie na końcu ~700-lotowej kolejki
   wypełniają głównie duzi, dobrze poinformowani agresorzy.
2. Najsilniejsze narzędzie to **filtr reżimu**: nie kwotować przy wysokiej zmienności z
   ostatnich 60 s i (pomocniczo) przy spreadzie > 1. Okresy wysokiej zmienności trwają ~60 s,
   więc da się na nie zareagować mimo opóźnienia 5 ms.
3. Wycofywanie strony po każdym agresorze ≥ 200 lotów jest za częste, bo takie zlecenia
   przychodzą mniej więcej co sekundę, i w backteście szkodziło.
4. Zapas trzymać daleko od ±100. W krachu każdy lot zapasu może stracić 100+ ticków, a wycena
   końcowa polega na likwidacji po cenach drugiej strony księgi, nie po mid.
5. Wynik zweryfikowany w oficjalnym symulatorze: `strategies/s1.py` (filtr spreadu i
   zmienności) daje +1816 na R2 publicznej, z dodatnimi obiema połowami, i 10 339 na R1,
   bez kar.

## 11. Ograniczenia

- Jedna 100-minutowa ścieżka, zdominowana przez krach z bloku 6 (3600–4200 s).
- Zysk makera liczony względem mid odtworzonej księgi publicznej. Pomija pozycję w kolejce i
  nasze opóźnienie, więc daje tylko orientację, a nie wynik realnego wypełnienia.
- Odtwarzanie księgi: `experiments/round_2/luklen123/20261107-round2-public-tape-profile/reconstruct.py`
  (dopasowanie zleceń jak w symulatorze). Statystyki: `analyze.py`, `analyze2.py`, `regime.py`,
  a ich wyniki w plikach `out_*.log` w tym samym folderze.
