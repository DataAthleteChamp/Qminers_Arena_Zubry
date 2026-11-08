# Czy da się przewidzieć spadek (lub skok) w R2 z danych z księgi?

Pytanie: czy przed dużymi ruchami ceny w R2 widać w księdze lub przepływie zleceń sygnały
ostrzegawcze, które pozwalają przygotować się wcześniej, zamiast tylko podążać za trendem?

## Dane i metoda

- **Taśmy:** R2 publiczna (SHA-256 `88ff641e…`) i R1 (`362e8208…`).
- **Rekonstrukcja księgi** jak w symulatorze, z próbką co 1 s (`per_second.py`):
  - głębokość 1/3/5/10 poziomów i do 5 ticków od najlepszej ceny,
  - wstawienia i anulowania ogółem oraz w pobliżu najlepszej ceny (≤ 2 ticki), osobno dla stron,
  - przepływ agresorów, zlecenia ≥ 500 lotów, sweepy, zlecenia IOC.
- **Cechy** (`precursors.py`) liczone wyłącznie z przeszłości, w oknach 10/30 s i względem
  mediany z 300 s:
  - zmienność, spread, głębokość względna, nierównowaga 1/5/10 poziomów,
  - nierównowaga anulowań i wstawień przy najlepszej cenie, bilans płynności,
  - przepływ i duzi agresorzy, sweepy, IOC,
  - momentum z 10–300 s i odchylenie od średniej 300 s.
- **Cele:** ruch mid w ciągu 30/60 s, ze znakiem (kierunek) i bez znaku (skala).
- **Test:** korelacja Spearmana na nienakładających się próbkach co 30 s, osobno dla R2a
  (0–3000 s), R2b (3000–6000 s) i R1. Pasmo szumu ±0,20 na połowę R2 i ±0,10 na R1.
- **Studium zdarzeń:** ruch w ciągu 60 s ≥ 2 SD (63 ticki). Na R2 jest 5 spadków
  (3600, 3813, 3934, 4233, 5650 s) i 4 wzrosty (1499, 2037, 5338, 5510 s).

## Wyniki

1. **Kierunku nie da się przewidzieć.** Żadna z 29 cech nie ma tego samego znaku korelacji
   z kierunkiem ruchu na R2a, R2b i R1.
   - Momentum i odchylenie od średniej zmieniają znak między połowami: R2a −0,20 (powrót do
     średniej), R2b +0,26 (kontynuacja).
   - Nierównowagi głębokości i przepływu na R2 mieszczą się w ±0,1, czyli w szumie.
2. **Brak prekursorów w 60 s przed zdarzeniem.** Średnie z-score cech w oknie 60 s przed
   startem dużego ruchu są bliskie 0 (|z| ≤ 0,45; największe dla momentum z 300 s).
3. **Sygnały pojawiają się dopiero w momencie startu ruchu**, nie przed nim. Przy spadkach
   to sweepy, spadek głębokości L1, szerszy spread i anulowania przy najlepszej cenie.
   To ten sam proces, który już trwa, a nie ostrzeżenie.
4. **Skalę ruchu da się przewidzieć słabo.** Spread z 10 s (+0,21), względna głębokość L1
   (−0,20) i zmienność z 30 s (+0,17) korelują ze skalą ruchu w ciągu 60 s na R2. Na R1
   ta zależność znika, bo nie ma tam reżimów zmienności.
5. **Po starcie duże ruchy trwają minutami.**
   - Spadki: po 10 s od startu do 300 s zostaje jeszcze 81–260 ticków w kierunku spadku
     (wszystkie 5).
   - Wzrosty: 29–220 ticków; dwa z czterech częściowo się cofnęły.
   - Ruch przebiega skokami: często 50–100 ticków w ciągu ~30 s.

## Wnioski dla strategii

- Nie da się z wyprzedzeniem „ustawić się pod spadek”. Nie ma wczesnego sygnału kierunku, który
  przetrwałby zmianę połówki taśmy czy rundy. Strategia zbudowana na takim sygnale z R2
  publicznej byłaby dopasowaniem do 5 zdarzeń.
- **Przygotowanie to zarządzanie ryzykiem, nie prognoza:**
  - mniejszy zapas przeciwny do ruchu, gdy rośnie ryzyko dużej skali (szerszy spread, płytsza
    L1, wyższa zmienność): to robi kara φ = γσ²/2 w s_25;
  - zero kwotowania w szoku.
- **Zysk na spadku przychodzi po jego wykryciu,** bo ruchy trwają minutami. Tak działa cel
  trendowy koziol.py. Do sprawdzenia jest szybsze wykrycie startu ruchu i wejście w pozycję
  (kilka sekund zamiast zgodności EMA 3/30/120 s): sweepy, spadek L1 i ruch o ≥ k·σ w ciągu
  10–20 s. Trzeba to oceniać na R1 i R2 jednocześnie.

## Ograniczenia

- Na R2 publicznej jest tylko 9 dużych ruchów, więc studium zdarzeń jest anegdotyczne.
- Korelacje na 100 nienakładających się próbkach na połowę mają szeroki błąd.
- R1 nie ma krachów, więc potwierdza tylko brak sygnału kierunku, a nie zachowanie przy krachu.
- Pliki: `experiments/round_2/luklen123/20261107-crash-precursors-001/` (`per_second.py`,
  `precursors.py`, `path_after_onset.py`, `out_*.log`).
