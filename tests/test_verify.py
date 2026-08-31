#!/usr/bin/env python3
"""Known-answer tests for the public packing verifier."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import verify  # noqa: E402


def data_rows(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]


def expect_invalid(checker, guard, path: Path, expected_n: int, label: str) -> None:
    claim = checker.first_claim(path)
    result = checker.evaluate(path, claim, checker.DEFAULT_SCALE_DIGITS, expected_n, guard)
    if result.get("valid") is not False:
        raise AssertionError(f"{label} was accepted")
    print(f"PASS: rejected {label}")


def main() -> int:
    checker = verify.load_checker()
    guard = checker.runtime_guard()
    source = ROOT / "data" / "PACKING_N600_SEED_2026083001_CANDIDATE.txt"
    baseline = verify.verify_one(source, checker, guard)
    if baseline.get("valid") is not True:
        raise AssertionError("known-valid file failed")
    print("PASS: accepted the known-valid 600-circle file")

    original_lines = source.read_text(encoding="utf-8").splitlines()
    header = [line for line in original_lines if not (line.strip() and not line.lstrip().startswith("#"))]
    rows = data_rows(source.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="packing-verifier-test-") as temp_name:
        temp = Path(temp_name)

        short = temp / "short.txt"
        short.write_text("\n".join(header + rows[:-1]) + "\n", encoding="utf-8")
        expect_invalid(checker, guard, short, 600, "a file with one missing circle")

        overlap_rows = list(rows)
        first = overlap_rows[0].split()
        second = overlap_rows[1].split()
        overlap_rows[1] = " ".join((second[0], first[1], first[2], second[3]))
        overlap = temp / "overlap.txt"
        overlap.write_text("\n".join(header + overlap_rows) + "\n", encoding="utf-8")
        expect_invalid(checker, guard, overlap, 600, "two circles at the same point")

        wall_rows = list(rows)
        first = wall_rows[0].split()
        wall_rows[0] = " ".join((first[0], "-0.500000000000000000000000", first[2], first[3]))
        wall = temp / "wall.txt"
        wall.write_text("\n".join(header + wall_rows) + "\n", encoding="utf-8")
        expect_invalid(checker, guard, wall, 600, "a circle crossing the left wall")

    print("PASS: all known-answer tests behaved as required")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
