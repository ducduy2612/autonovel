---
id: T02
parent: S04
milestone: M001
key_files:
  - typeset/build_tex.py
  - test_s04_export.py
key_decisions:
  - generate_latex_header() is a standalone function accepting an optional lang parameter (defaulting to get_language()), making it testable without env manipulation
duration: 
verification_result: passed
completed_at: 2026-04-16T17:02:32.186Z
blocker_discovered: false
---

# T02: Add conditional Vietnamese babel support to LaTeX template generation

**Add conditional Vietnamese babel support to LaTeX template generation**

## What Happened

Updated build_tex.py to import BASE_DIR and CHAPTERS_DIR from config.py instead of computing them locally, eliminating the redundant _PROJECT_ROOT-derived path constants. Added a generate_latex_header() function that produces a LaTeX header block for chapters_content.tex — when get_language() returns 'vi', the header includes \usepackage[vietnamese]{babel} for proper Vietnamese hyphenation and localization. The main() function now prepends this header to the generated chapters_content.tex. Added 5 new tests in test_s04_export.py covering: (1) en header has no babel, (2) vi header includes babel, (3) auto-generated comment present, (4) vi babel injected from AUTONOVEL_LANGUAGE env, (5) en header from env has no babel. All 53 tests in the full suite pass.

## Verification

Ran `uv run pytest test_s04_export.py -v` — all 15 tests pass (10 from T01 + 5 new). Also ran the full suite `uv run pytest -v` — all 53 tests pass across test_config.py, test_evaluate.py, and test_s04_export.py with no regressions.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `uv run pytest test_s04_export.py -v` | 0 | ✅ pass | 2000ms |
| 2 | `uv run pytest -v` | 0 | ✅ pass | 4000ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `typeset/build_tex.py`
- `test_s04_export.py`
