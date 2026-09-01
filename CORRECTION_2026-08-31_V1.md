# Correction, version 1: 800-circle radius display

Date: 2026-08-31

The first public table showed this 800-circle value as feasible:

`0.01863759233676851787349305044720107162570826540500351479481853408661754556406518746010543808969481480`

Its last digit is wrong for a feasible display. The value came from ordinary nearest rounding. The exact pair limit is slightly lower.

The corrected 101-place value is rounded down:

`0.01863759233676851787349305044720107162570826540500351479481853408661754556406518746010543808969481479`

The exact integer pair test passes the corrected value. It fails the old value. The test is:

`4 * radius_integer^2 * coordinate_scale^2 <= minimum_pair_squared_integer * 10^(2 * radius_digits)`

The coordinate file did not change.

SHA-256: `076bc719aa8124ea567c0f85bb9629242670006ea60e5e243737f0dc4190e66d`

The safe 24-place radius is still:

`0.018637592336768517873493`

The displayed gains for the 600-, 700-, and 800-circle files remain 1.2, 1.4, and 2.7 parts per billion.

The saved exact-check file also did not change.

SHA-256: `a154a55d9a337a37e7be7bb8870f8ece7af3822d216a2b0df81f002ee166ec7f`

That file is historical evidence. Its `certified_radius_decimal` and `pair_radius_decimal` fields contain the old nearest-rounded display. Its exact minimum squared pair distance remains valid. The repaired `verify.py` uses that exact integer, rounds down, parses the displayed result, and tests the result again.

No coordinate file or saved check report was deleted or rewritten. This correction changes one last displayed digit. It does not change the three coordinate files or their reported improvements. It does not make an optimality or accepted-record claim.
