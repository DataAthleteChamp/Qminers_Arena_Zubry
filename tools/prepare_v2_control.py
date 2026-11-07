"""Create one frozen midpoint control from the v2 candidate for a paired public test."""

from __future__ import annotations

import argparse

from tools.common import ROOT, inside, sha256, write_once


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default="research/experiments/r0-v2-mm-depth/strategy.py")
    parser.add_argument("--out", default="research/candidates/v2-midpoint-control.py")
    args = parser.parse_args()
    source = inside(args.source)
    text = source.read_text()
    needle = "IMBALANCE_WEIGHT = 1.0"
    if text.count(needle) != 1:
        raise ValueError("Control must differ only at the declared imbalance weight.")
    destination = inside(args.out)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x") as handle:
        handle.write(text.replace(needle, "IMBALANCE_WEIGHT = 0.0"))
    write_once(
        destination.with_suffix(".json"),
        {
            "source": str(source.relative_to(ROOT)),
            "source_sha256": sha256(source),
            "control_sha256": sha256(destination),
            "changed_parameter": {"IMBALANCE_WEIGHT": [1.0, 0.0]},
            "unchanged": ["inventory policy", "quote size", "latency", "engine", "data"],
            "scope": "one predeclared control; public v2 tape is consumed validation data",
        },
    )
    print(destination)


if __name__ == "__main__":
    main()
