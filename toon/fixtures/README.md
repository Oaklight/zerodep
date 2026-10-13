# TOON conformance fixtures

`spec/encode/` and `spec/decode/` are the official conformance fixtures of the
TOON specification, copied verbatim.

| | |
|---|---|
| Upstream repository | https://github.com/toon-format/spec |
| Upstream path | `tests/fixtures/{encode,decode}/*.json` |
| Upstream commit | `d09c3d33e37389345a74bd96981eb96dd9be6c5e` (tag `v4.4.0`) |
| Specification version | 4.4 |
| Fixture cases | 160 encode, 404 decode (564 total) |
| Upstream license | MIT (Copyright (c) 2025-PRESENT Johann Schopplich) |

The same files are the copy that `toon-format/toon-python` runs in its own CI
(`tests/fixtures/`, byte-identical at `toon-python@91413d1`). They are vendored
here so the conformance gate runs with the network off and against a fixed
upstream revision instead of a floating clone.

Do not edit these files by hand. To refresh them, copy the two directories from
a newer `toon-format/spec` tag and update the commit hash, version, and counts
in this table and in `toon/conformance_baseline.json`.

Each fixture file is a JSON object with a `version` field (the baseline spec
version), a `category` (`encode` or `decode`), and a `tests` array. Each test
carries `name`, `input`, `expected`, an optional `shouldError` flag, optional
`options` (`delimiter`, `indentSize`, `strict`), and an optional `specSection`
reference used to group failures by section.
