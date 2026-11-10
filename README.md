# WITHDRAWN: three circle-packing record claims

I previously presented these three layouts as candidate records. I withdraw that claim. The files fit 600 and 700 and 800 equal circles in a square and the exact checks show that the circles stay inside it and no two overlap at the checked radii (that is all these files establish).

## What the checks establish

Each saved file has fixed circle positions and a checked radius. The table gives radii rounded down and the verifier reads each printed value back and checks it with exact wall and pair tests. These are feasibility checks only.

| Circles | Checked radius |
| ---: | ---: |
| 600 | 0.02147937677931336792435345333619189507511634335902592795709860126783031076603618257014873085383241024 |
| 700 | 0.01990364285635992080414501095152789833198973658477548808811217087782022076562630386337076619834542754 |
| 800 | 0.01863759233676851787349305044720107162570826540500351479481853408661754556406518746010543808969481479 |

The first public 800-circle display rounded above its exact pair limit. The corrected final digit is recorded in [CORRECTION_2026-08-31_V1.md](CORRECTION_2026-08-31_V1.md). The original saved evidence stays unchanged.

## Verify all three in one command

Use Python 3. No package install or network access is needed.

```sh
python3 verify.py
```

The command checks the saved file hashes. It then reads each 24-place coordinate as an integer, checks all four walls, and checks every pair of circles. It calculates a downward supported radius from the exact minimum squared distance. It parses every displayed supported radius and tests it again with exact integers.

The saved check reports remain unchanged as historical evidence. Their exact squared distances are valid. The 800-circle `certified_radius_decimal` and `pair_radius_decimal` fields used nearest rounding and are superseded only as public feasible-radius displays.

Run the known-answer failure tests with:

```sh
python3 tests/test_verify.py
```

Those tests prove that the checker rejects a missing circle, two circles at the same point, and a circle that crosses a wall. They also prove that the old 800-circle display fails, while the corrected last digit passes.

## Files

- `data/` has the three coordinate files.
- `checks/` has the three exact-check reports and the three separate check reports from the frozen run.
- `verifier/exact_checker.py` is the byte-for-byte checker used in the run.
- `verify.py` pins the checker and data hashes and verifies the kit in one command.
- `ARTIFACTS.sha256` records the source hashes.
- `CORRECTION_2026-08-31_V1.md` records the display correction and keeps the old evidence in view.

The copied checker came from Project Aletheia's Record Forge II packing run. Checker SHA-256: `0234eb7763dee32c3a1081139fb049978ecda593cf845f19bd4f44d2eaf8d739`.

## Claim limit

The files establish valid layouts at the checked radii. The record claim is withdrawn. These checks cover these fixed files and do not prove the best possible layout.

## License

The proposed license uses CC0 1.0 for the coordinate data and saved check reports, and the MIT License for the code. See `LICENSE.md`. The repository owner must approve these terms before public release.
