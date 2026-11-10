# Correction: radius display and withdrawn improvement claims

First correction: 2026-08-31. This note was corrected again on 2026-11-10.

I previously said that the three files kept numerical gains and that their reported improvements stood. I withdraw those improvement claims and the record claims. The checks establish valid layouts at the checked radii (nothing more).

## The radius-display correction

The first public table showed this 800-circle value as feasible:

`0.01863759233676851787349305044720107162570826540500351479481853408661754556406518746010543808969481480`

Its last digit came from nearest rounding and put the display above the exact pair limit. The corrected 101-place value is rounded down:

`0.01863759233676851787349305044720107162570826540500351479481853408661754556406518746010543808969481479`

The exact integer pair test passes the corrected value and fails the old value. The test is:

`4 * radius_integer^2 * coordinate_scale^2 <= minimum_pair_squared_integer * 10^(2 * radius_digits)`

The coordinate file did not change. Its SHA-256 is:

`076bc719aa8124ea567c0f85bb9629242670006ea60e5e243737f0dc4190e66d`

The safe 24-place radius is:

`0.018637592336768517873493`

The saved exact-check file did not change. Its SHA-256 is:

`a154a55d9a337a37e7be7bb8870f8ece7af3822d216a2b0df81f002ee166ec7f`

That file is historical evidence and its `certified_radius_decimal` and `pair_radius_decimal` fields keep the old nearest-rounded display. The exact minimum squared pair distance stays available and `verify.py` uses that integer and rounds down and reads the displayed number back and tests it again.

## What changed on 2026-11-10

The earlier correction fixed one displayed digit but still claimed numerical gains for the three files. That comparison claim is now withdrawn. No coordinate file or saved check report was deleted or rewritten. The files establish feasibility at the checked radii and do not establish a record or the best possible layout.
