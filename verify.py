#!/usr/bin/env python3
"""Verify the three published packing candidates with exact integer checks."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from decimal import Decimal
from pathlib import Path
from types import ModuleType
from typing import Any


ROOT = Path(__file__).resolve().parent
CHECKER = ROOT / "verifier" / "exact_checker.py"
PINNED_CHECKER_SHA256 = "0234eb7763dee32c3a1081139fb049978ecda593cf845f19bd4f44d2eaf8d739"

CANDIDATES: dict[str, dict[str, Any]] = {
    "PACKING_N600_SEED_2026083001_CANDIDATE.txt": {
        "n": 600,
        "coordinate_sha256": "b9794492f37d28e8d4f92900ef19ebd85f58530f97f5936c245e584c89f8b9b9",
        "exact_file": "PACKING_N600_SEED_2026083001_EXACT_CHECK.json",
        "exact_sha256": "5740e8b536c7ed8d54138fe41227683afdb5856d1f0dde39662c06cbfb32f958",
        "mpmath_file": "PACKING_N600_SEED_2026083001_MPMATH_CHECK.json",
        "mpmath_sha256": "29d9d6efaa88400ef860cdafce67b1ed16dfcf9b5dd99b6a0a0aac3f4a64342d",
        "printed_catalog_radius": "0.021479376754",
        "certified_radius": "0.02147937677931336792435345333619189507511634335902592795709860126783031076603618257014873085383241024",
    },
    "PACKING_N700_SEED_2026083001_CANDIDATE.txt": {
        "n": 700,
        "coordinate_sha256": "14ca8170ff3089e63d6e0730f4e4b7e199e3610109880d84d0be5b959d364ede",
        "exact_file": "PACKING_N700_SEED_2026083001_EXACT_CHECK.json",
        "exact_sha256": "7b608d1a92af327f2d17b25f3539dfba1195ead114703efcc5fdd892615ac847",
        "mpmath_file": "PACKING_N700_SEED_2026083001_MPMATH_CHECK.json",
        "mpmath_sha256": "47162a0e614e9189cab57cb757674fe41e53fc78273864686cd64fd1de6ab2bc",
        "printed_catalog_radius": "0.019903642828",
        "certified_radius": "0.01990364285635992080414501095152789833198973658477548808811217087782022076562630386337076619834542754",
    },
    "PACKING_N800_SEED_2026083001_CANDIDATE.txt": {
        "n": 800,
        "coordinate_sha256": "076bc719aa8124ea567c0f85bb9629242670006ea60e5e243737f0dc4190e66d",
        "exact_file": "PACKING_N800_SEED_2026083001_EXACT_CHECK.json",
        "exact_sha256": "a154a55d9a337a37e7be7bb8870f8ece7af3822d216a2b0df81f002ee166ec7f",
        "mpmath_file": "PACKING_N800_SEED_2026083001_MPMATH_CHECK.json",
        "mpmath_sha256": "9e6f906257c132ab6e6b4a7de00f24a91273ab5772fc4e7bbcefe952906651fa",
        "printed_catalog_radius": "0.018637592286",
        "certified_radius": "0.01863759233676851787349305044720107162570826540500351479481853408661754556406518746010543808969481480",
    },
}


class VerificationError(RuntimeError):
    """A file or a mathematical check did not match the published kit."""


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def load_checker() -> ModuleType:
    require(CHECKER.is_file(), f"missing checker: {CHECKER}")
    observed = sha256(CHECKER)
    require(
        observed == PINNED_CHECKER_SHA256,
        f"checker hash changed: expected {PINNED_CHECKER_SHA256}, found {observed}",
    )
    spec = importlib.util.spec_from_file_location("packing_exact_checker", CHECKER)
    require(spec is not None and spec.loader is not None, "could not load exact checker")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise VerificationError(f"could not read {path}: {error}") from error
    require(isinstance(value, dict), f"expected a JSON object in {path}")
    return value


def compare_saved_checks(
    path: Path,
    candidate_sha256: str,
    spec: dict[str, Any],
    fresh: dict[str, Any],
) -> None:
    exact_path = ROOT / "checks" / spec["exact_file"]
    mpmath_path = ROOT / "checks" / spec["mpmath_file"]
    require(sha256(exact_path) == spec["exact_sha256"], f"saved exact check changed: {exact_path}")
    require(sha256(mpmath_path) == spec["mpmath_sha256"], f"saved separate check changed: {mpmath_path}")

    exact = read_json(exact_path)
    separate = read_json(mpmath_path)
    require(exact.get("valid") is True, f"saved exact check is not valid: {exact_path}")
    require(all(exact.get("checks", {}).values()), f"a saved exact sub-check failed: {exact_path}")
    require(exact.get("sha256") == candidate_sha256, f"saved exact check names a different coordinate file: {path}")
    require(exact.get("verifier_sha256") == PINNED_CHECKER_SHA256, "saved exact check used a different checker")
    require(exact.get("limits", {}).get("n") == spec["n"], "saved exact check has the wrong circle count")

    require(separate.get("valid") is True, f"saved separate check is not valid: {mpmath_path}")
    require(separate.get("sha256") == candidate_sha256, "saved separate check names a different coordinate file")
    require(separate.get("report", {}).get("valid") is True, "saved separate report is not valid")
    require(separate.get("report", {}).get("n") == spec["n"], "saved separate report has the wrong circle count")

    saved_limits = exact["limits"]
    fresh_limits = fresh["limits"]
    for key in (
        "n",
        "scale",
        "scale_digits",
        "boundary_scaled_integer",
        "minimum_pair_squared_scaled_integer",
        "certified_radius_scaled_floor",
        "certified_radius_scaled_floor_decimal",
        "certified_radius_decimal",
        "limiting_constraint",
    ):
        require(fresh_limits.get(key) == saved_limits.get(key), f"fresh result differs from the saved exact check at {key}")
    require(
        fresh_limits["certified_radius_decimal"] == spec["certified_radius"],
        "fresh supported radius differs from the published value",
    )
    require(
        Decimal(fresh_limits["certified_radius_scaled_floor_decimal"])
        > Decimal(spec["printed_catalog_radius"]),
        "the safe 24-place radius does not exceed the printed catalog radius",
    )


def verify_one(
    path: Path,
    checker: ModuleType,
    guard: dict[str, Any],
    expected_n: int | None = None,
) -> dict[str, Any]:
    require(path.is_file(), f"missing coordinate file: {path}")
    bundled = CANDIDATES.get(path.name)
    if bundled is not None:
        expected_n = int(bundled["n"])
        observed_sha256 = sha256(path)
        require(observed_sha256 == bundled["coordinate_sha256"], f"coordinate file hash changed: {path}")
    else:
        require(expected_n is not None, "an outside file needs --expected-n")
        observed_sha256 = sha256(path)

    try:
        claim = checker.first_claim(path)
    except (OSError, ValueError) as error:
        raise VerificationError(str(error)) from error
    result = checker.evaluate(path, claim, checker.DEFAULT_SCALE_DIGITS, expected_n, guard)
    require(result.get("valid") is True, f"exact check failed for {path}: {result.get('error', 'wall or pair failure')}")
    require(result.get("sha256") == observed_sha256, f"checker read different bytes for {path}")
    require(all(result.get("checks", {}).values()), f"one or more exact sub-checks failed for {path}")
    require(result.get("limits", {}).get("n") == expected_n, f"wrong circle count in {path}")

    if bundled is not None:
        compare_saved_checks(path, observed_sha256, bundled, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check every wall, every circle pair, and the supported radius without rounding the coordinates."
    )
    parser.add_argument("coordinate_files", nargs="*", type=Path)
    parser.add_argument("--expected-n", type=int, help="required for one coordinate file outside this kit")
    args = parser.parse_args()

    checker = load_checker()
    guard = checker.runtime_guard()
    paths = args.coordinate_files or [ROOT / "data" / name for name in CANDIDATES]
    try:
        for path in paths:
            result = verify_one(path.resolve(), checker, guard, args.expected_n)
            limits = result["limits"]
            print(
                f"PASS: {limits['n']} circles; every wall and pair passed; "
                f"supported radius {limits['certified_radius_decimal']}"
            )
    except (OSError, VerificationError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 1

    if not args.coordinate_files:
        print(
            "PASS: all three fixed files match their saved hashes and checks. "
            "They are candidate records submitted to the catalog maintainer for verification. "
            "They are not accepted records or proofs of the best possible packings."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
