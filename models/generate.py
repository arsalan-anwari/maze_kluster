#!/usr/bin/env python
"""Train and serialise RF, GBT, and GP scorers from data/maze_runs.parquet.

Run from the project root:
    python models/generate.py

Requires data/maze_runs.parquet to exist, run data/generate.py first.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from maze_kluster.models.gbt import GBTScorer
from maze_kluster.models.gp import GPUCBScorer
from maze_kluster.models.rf import RFScorer

DATA_PATH = Path("data/maze_runs.parquet")


def main() -> None:
    argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    ).parse_args()

    if not DATA_PATH.exists():
        raise FileNotFoundError(f"{DATA_PATH} not found, run data/generate.py first")

    rf = RFScorer()
    rf.fit(DATA_PATH)
    rf.save()
    print("RF saved -> models/rf.pkl")
    for feature, imp in sorted(rf.feature_importances().items(), key=lambda x: -x[1]):
        print(f"  {feature}: {imp:.4f}")

    print()
    gbt = GBTScorer()
    gbt.fit(DATA_PATH)
    gbt.save()
    print("GBT saved -> models/gbt.pkl")

    print()
    gp = GPUCBScorer()
    gp.fit(DATA_PATH)
    gp.save()
    print("GP saved -> models/gp.pkl")
    if gp._pipeline is not None:
        print(f"Kernel: {gp._pipeline['gpr'].kernel_}")  # type: ignore[index]


if __name__ == "__main__":
    main()
