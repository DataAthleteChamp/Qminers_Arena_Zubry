"""Price-mirror a tape: price -> 2*PIVOT - price and B <-> A. Microstructure is identical,
direction is reversed (a crash becomes a rally). Usage: mirror_tape.py <in.csv> <out.csv>
"""

from __future__ import annotations

import csv
import sys

PIVOT = 10_000


def main(src: str, dst: str) -> None:
    with open(src, newline="") as fi, open(dst, "w", newline="") as fo:
        r = csv.reader(fi)
        w = csv.writer(fo, lineterminator="\n")
        w.writerow(next(r))
        for row in r:
            if row[1] == "Insert":
                row[3] = "A" if row[3] == "B" else "B"
                row[5] = str(2 * PIVOT - int(row[5]))
            w.writerow(row)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
