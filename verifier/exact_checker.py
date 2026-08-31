#!/usr/bin/env python3
"""Exact integer verifier for Record Forge II square packing certificates."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import socket
import sys
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any


ROOT = Path("/data/adp/investigations/record_forge_2_packing_ramsey_2026-08-30_v1")
PACKING = ROOT / "packing"
CONTROLS = PACKING / "controls"
RECEIPTS = PACKING / "receipts"
DEFAULT_SCALE_DIGITS = 24
DECIMAL_PATTERN = re.compile(r"^-?(?:0|[1-9][0-9]*)\.[0-9]+$")
PARENT_CERTIFICATES = {
    600: Path("/data/adp/investigations/record_forge_2026-08-23/codex_t3_t4/certificates/T3_N600_V3_RUNG_2e-11_SEED_2026082304.txt"),
    700: Path("/data/adp/investigations/record_forge_2026-08-23/codex_t3_t4/certificates/T3_N700_V4_EXACT_CLAIM_RUNG_2e-11_SEED_2026082304.txt"),
    800: Path("/data/adp/investigations/record_forge_2026-08-23/codex_t3_t4/certificates/T3_N800_V3_RUNG_1e-11_SEED_2026082304.txt"),
}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def runtime_guard() -> dict[str, Any]:
    banned = {"anthropic", "google.generativeai", "ollama", "openai"}
    loaded = sorted(name for name in sys.modules if name in banned)
    if loaded:
        raise RuntimeError(f"LLM module loaded: {loaded}")

    def deny_socket(*_args, **_kwargs):
        raise RuntimeError("network disabled in exact packing verifier")

    socket.socket = deny_socket
    return {
        "assert_no_llm": "PASS",
        "banned_module_roots": sorted(banned),
        "socket_ban": "ACTIVE",
    }


def atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp.{os.getpid()}")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def scaled_integer(text: str, scale_digits: int) -> int:
    if not DECIMAL_PATTERN.fullmatch(text):
        raise ValueError(f"non-canonical decimal text: {text!r}")
    fractional = text.partition(".")[2]
    if len(fractional) > scale_digits:
        raise ValueError(
            f"decimal has {len(fractional)} places but frozen scale has {scale_digits}: {text}"
        )
    scale = 10**scale_digits
    value = Decimal(text) * scale
    if value != value.to_integral_value():
        raise ValueError(f"decimal is not exact on frozen scale: {text}")
    return int(value)


def fixed_decimal(value: int, scale_digits: int) -> str:
    sign = "-" if value < 0 else ""
    magnitude = abs(value)
    scale = 10**scale_digits
    whole, fraction = divmod(magnitude, scale)
    return f"{sign}{whole}.{fraction:0{scale_digits}d}"


def certificate_rows(
    path: Path,
    claimed_radius_text: str,
    scale_digits: int,
    expected_n: int | None,
) -> tuple[list[tuple[int, int]], int]:
    points: list[tuple[int, int]] = []
    indices: list[int] = []
    row_claims: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        fields = stripped.split()
        if len(fields) != 4:
            raise ValueError(f"certificate row must have four fields: {stripped}")
        indices.append(int(fields[0]))
        points.append(
            (
                scaled_integer(fields[1], scale_digits),
                scaled_integer(fields[2], scale_digits),
            )
        )
        row_claims.append(fields[3])
    if not points:
        raise ValueError("certificate has no coordinate rows")
    if indices != list(range(1, len(points) + 1)):
        raise ValueError("indices are not exactly 1..n")
    if expected_n is not None and len(points) != expected_n:
        raise ValueError(f"expected {expected_n} points but found {len(points)}")
    if len(set(points)) != len(points):
        raise ValueError("duplicate integer centers")
    if any(text != claimed_radius_text for text in row_claims):
        raise ValueError("claim text differs between the argument and at least one coordinate row")
    radius = scaled_integer(claimed_radius_text, scale_digits)
    return points, radius


def exact_limits(points: list[tuple[int, int]], scale_digits: int) -> dict[str, Any]:
    scale = 10**scale_digits
    half = scale // 2
    boundary = scale
    boundary_detail: dict[str, Any] | None = None
    side_names = ("left", "right", "bottom", "top")
    for index, (x_coord, y_coord) in enumerate(points, start=1):
        margins = (half + x_coord, half - x_coord, half + y_coord, half - y_coord)
        local_side = min(range(4), key=margins.__getitem__)
        if margins[local_side] < boundary:
            boundary = margins[local_side]
            boundary_detail = {"point": index, "side": side_names[local_side]}
    minimum_d2: int | None = None
    pair_detail: list[int] | None = None
    for first, (x1, y1) in enumerate(points):
        for second in range(first + 1, len(points)):
            x2, y2 = points[second]
            d2 = (x1 - x2) ** 2 + (y1 - y2) ** 2
            if minimum_d2 is None or d2 < minimum_d2:
                minimum_d2 = d2
                pair_detail = [first + 1, second + 1]
    if minimum_d2 is None:
        raise ValueError("at least two points are required")
    pair_floor = math.isqrt(minimum_d2) // 2
    certified_floor = min(boundary, pair_floor)
    with localcontext() as context:
        context.prec = max(100, scale_digits * 4)
        pair_radius = Decimal(minimum_d2).sqrt() / (Decimal(2) * Decimal(scale))
        boundary_radius = Decimal(boundary) / Decimal(scale)
        certified = min(boundary_radius, pair_radius)
    return {
        "n": len(points),
        "scale_digits": scale_digits,
        "scale": str(scale),
        "boundary_scaled_integer": str(boundary),
        "boundary_radius": fixed_decimal(boundary, scale_digits),
        "boundary_limiter": boundary_detail,
        "minimum_pair_squared_scaled_integer": str(minimum_d2),
        "pair_radius_decimal": format(pair_radius, "f"),
        "pair_radius_scaled_floor": str(pair_floor),
        "pair_limiter": {"points": pair_detail},
        "certified_radius_decimal": format(certified, "f"),
        "certified_radius_scaled_floor": str(certified_floor),
        "certified_radius_scaled_floor_decimal": fixed_decimal(certified_floor, scale_digits),
        "next_scaled_decimal": fixed_decimal(certified_floor + 1, scale_digits),
        "limiting_constraint": "boundary" if boundary <= pair_floor else "pair",
    }


def evaluate(
    path: Path,
    claimed_radius_text: str,
    scale_digits: int,
    expected_n: int | None,
    guard: dict[str, Any],
) -> dict[str, Any]:
    try:
        points, radius = certificate_rows(path, claimed_radius_text, scale_digits, expected_n)
        limits = exact_limits(points, scale_digits)
        threshold = (2 * radius) ** 2
        boundary_ok = int(limits["boundary_scaled_integer"]) >= radius
        pairs_ok = int(limits["minimum_pair_squared_scaled_integer"]) >= threshold
        valid = radius > 0 and boundary_ok and pairs_ok
        return {
            "schema": "record-forge-2-packing-exact-check-v1",
            "claim_authority": "NONE",
            "valid": valid,
            "path": str(path),
            "sha256": digest(path),
            "claimed_radius_text": claimed_radius_text,
            "claimed_radius_scaled_integer": str(radius),
            "scale_digits": scale_digits,
            "checks": {
                "positive_radius": radius > 0,
                "all_four_boundaries": boundary_ok,
                "all_unordered_pairs": pairs_ok,
                "claim_text_exact_in_every_row": True,
                "indices_exactly_1_through_n": True,
                "centers_unique_on_frozen_scale": True,
            },
            "limits": limits,
            "runtime_guard": guard,
            "verifier_path": str(Path(__file__).resolve()),
            "verifier_sha256": digest(Path(__file__).resolve()),
        }
    except (OSError, ValueError, ArithmeticError) as error:
        return {
            "schema": "record-forge-2-packing-exact-check-v1",
            "claim_authority": "NONE",
            "valid": False,
            "path": str(path),
            "sha256": digest(path) if path.is_file() else None,
            "claimed_radius_text": claimed_radius_text,
            "scale_digits": scale_digits,
            "error": str(error),
            "runtime_guard": guard,
            "verifier_path": str(Path(__file__).resolve()),
            "verifier_sha256": digest(Path(__file__).resolve()),
        }


def first_claim(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            fields = stripped.split()
            if len(fields) != 4:
                raise ValueError(f"bad first row in {path}")
            return fields[3]
    raise ValueError(f"no rows in {path}")


def run_controls(guard: dict[str, Any]) -> dict[str, Any]:
    fixture_specs = {
        "square4_valid": (CONTROLS / "square4_valid.txt", "0.250000", True),
        "boundary_spoil": (CONTROLS / "boundary_spoil.txt", "0.250000", False),
        "pair_spoil": (CONTROLS / "pair_spoil.txt", "0.250000", False),
        "claim_mismatch": (CONTROLS / "claim_mismatch.txt", "0.250000", False),
    }
    fixtures: dict[str, Any] = {}
    for name, (path, claim, expected) in fixture_specs.items():
        check = evaluate(path, claim, DEFAULT_SCALE_DIGITS, 4, guard)
        fixtures[name] = {
            "expected_valid": expected,
            "observed_valid": check["valid"],
            "passed": check["valid"] is expected,
            "check": check,
        }
    pair_points, pair_radius = certificate_rows(
        CONTROLS / "pair_spoil.txt", "0.250000", DEFAULT_SCALE_DIGITS, 4
    )
    pair_limits = exact_limits(pair_points, DEFAULT_SCALE_DIGITS)
    naive_boundary_only_accepts_pair_spoil = (
        int(pair_limits["boundary_scaled_integer"]) >= pair_radius
    )
    parent_checks: dict[str, Any] = {}
    for n_value, path in PARENT_CERTIFICATES.items():
        claim = first_claim(path)
        check = evaluate(path, claim, DEFAULT_SCALE_DIGITS, n_value, guard)
        parent_checks[str(n_value)] = {
            "expected_valid": True,
            "observed_valid": check["valid"],
            "passed": check["valid"],
            "parent_max_claim_scaled_integer": check.get("limits", {}).get(
                "certified_radius_scaled_floor"
            ),
            "strict_improvement_target_scaled_integer": (
                str(int(check["limits"]["certified_radius_scaled_floor"]) + 1)
                if check["valid"]
                else None
            ),
            "strict_improvement_target_decimal": (
                fixed_decimal(
                    int(check["limits"]["certified_radius_scaled_floor"]) + 1,
                    DEFAULT_SCALE_DIGITS,
                )
                if check["valid"]
                else None
            ),
            "check": check,
        }
    formal_path = RECEIPTS / "PACKING_FORMALIZATION.json"
    formal = json.loads(formal_path.read_text(encoding="utf-8"))
    formal_fixture_match = (
        formal.get("passed") is True
        and formal.get("independent_kernel_fixtures", {}).get("square4_valid") is True
        and formal.get("independent_kernel_fixtures", {}).get("boundary_spoil_rejected") is True
        and formal.get("independent_kernel_fixtures", {}).get("pair_spoil_rejected") is True
    )
    passed = (
        all(row["passed"] for row in fixtures.values())
        and all(row["passed"] for row in parent_checks.values())
        and naive_boundary_only_accepts_pair_spoil
        and formal_fixture_match
    )
    payload = {
        "schema": "record-forge-2-packing-verifier-controls-v1",
        "claim_authority": "NONE",
        "passed": passed,
        "scale_digits": DEFAULT_SCALE_DIGITS,
        "fixtures": fixtures,
        "broken_baseline": {
            "name": "boundary-only verifier",
            "pair_spoil_accepted": naive_boundary_only_accepts_pair_spoil,
            "expected_to_accept_pair_spoil": True,
            "failed_for_right_reason": naive_boundary_only_accepts_pair_spoil,
            "reason": "Deleting pair checks accepts circles whose centers are too close."
        },
        "parent_certificate_checks": parent_checks,
        "formal_receipt_path": str(formal_path),
        "formal_receipt_sha256": digest(formal_path),
        "formal_fixture_match": formal_fixture_match,
        "runtime_guard": guard,
        "verifier_path": str(Path(__file__).resolve()),
        "verifier_sha256": digest(Path(__file__).resolve()),
    }
    output = RECEIPTS / "PACKING_VERIFIER_CONTROLS.json"
    atomic_json(output, payload)
    print(json.dumps({**payload, "output": str(output), "output_sha256": digest(output)}, indent=2, sort_keys=True))
    return payload


def main() -> int:
    guard = runtime_guard()
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("controls")
    verify = subparsers.add_parser("verify")
    verify.add_argument("certificate", type=Path)
    verify.add_argument("claimed_radius")
    verify.add_argument("--scale-digits", type=int, default=DEFAULT_SCALE_DIGITS)
    verify.add_argument("--expected-n", type=int)
    verify.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.command == "controls":
        payload = run_controls(guard)
        return 0 if payload["passed"] else 1
    payload = evaluate(
        args.certificate,
        args.claimed_radius,
        args.scale_digits,
        args.expected_n,
        guard,
    )
    if args.output:
        atomic_json(args.output, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
