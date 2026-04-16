---
id: S04
parent: M001
milestone: M001
provides:
  - ["default_state() with language field from get_language()", "patch_epub_metadata() for dynamic lang patching in epub_metadata.yaml", "generate_latex_header() with conditional babel injection for Vietnamese", "build_tex.py uses config.py constants (BASE_DIR, CHAPTERS_DIR) instead of hardcoded paths"]
requires:
  - slice: S01
    provides: config.py get_language() function and BASE_DIR/CHAPTERS_DIR constants
affects:
  - ["S05"]
key_files:
  - ["run_pipeline.py", "typeset/build_tex.py", "typeset/epub_metadata.yaml", "test_s04_export.py"]
key_decisions:
  - ["Used regex-based YAML patching instead of PyYAML to avoid adding a dependency", "Wrapped build_tex.py module-level code in main() guard to enable clean test imports", "generate_latex_header() is a standalone function accepting an optional lang parameter (defaulting to get_language()), making it testable without env manipulation"]
patterns_established:
  - ["Regex YAML patching for simple flat YAML files — avoids adding PyYAML dependency", "Module-level code wrapped in main() with __name__ guard for testability", "Helper functions accept optional lang parameter defaulting to get_language() for env-free testing"]
observability_surfaces:
  - none
drill_down_paths:
  - [".gsd/milestones/M001/slices/S04/tasks/T01-SUMMARY.md", ".gsd/milestones/M001/slices/S04/tasks/T02-SUMMARY.md"]
duration: ""
verification_result: passed
completed_at: 2026-04-16T17:04:46.965Z
blocker_discovered: false
---

# S04: Export and metadata language support

**Export outputs reflect configured language: epub_metadata.yaml lang field, LaTeX babel injection for Vietnamese, state.json language field**

## What Happened

This slice wired the export and metadata layer to respect the configured pipeline language (from config.py's `get_language()`).

**T01 — state.json language field + epub metadata patching**: Added a `"language"` key to `default_state()` in `run_pipeline.py` that reads from `config.get_language()`, so state.json now propagates the configured language. Created a `patch_epub_metadata()` helper in `typeset/build_tex.py` that uses regex to swap the `lang:` line in `epub_metadata.yaml` before LaTeX content generation. Wrapped build_tex.py's module-level chapter-processing code into a `main()` function with `if __name__ == "__main__"` guard so the module can be imported for testing. Replaced hardcoded `/home/jeffq/autonovel/` paths with project-root-relative paths. 10 tests cover default language, vi language, epub metadata patching for both en and vi, no-change optimization, field preservation, missing file handling, and get_language() default propagation.

**T02 — Conditional Vietnamese babel support**: Added `generate_latex_header()` to build_tex.py that produces a LaTeX header block — when language is 'vi', it includes `\usepackage[vietnamese]{babel}` for proper Vietnamese hyphenation and localization. Updated build_tex.py to import `BASE_DIR` and `CHAPTERS_DIR` from config.py instead of computing them locally. The main() function prepends this header to `chapters_content.tex`. 5 new tests cover en header (no babel), vi header (includes babel), auto-generated comment, and env-driven behavior.

All 53 tests pass across test_config.py, test_evaluate.py, and test_s04_export.py.

## Verification

Ran `uv run pytest test_s04_export.py -v` — all 15 S04 tests pass (10 from T01 + 5 from T02). Ran `uv run pytest -v` — all 53 tests pass across the full suite with no regressions. Tests verify: (1) default_state() includes language='en' by default, (2) default_state() with AUTONOVEL_LANGUAGE=vi includes language='vi', (3) patch_epub_metadata() patches lang to 'vi' and 'en' correctly, (4) other YAML fields are preserved, (5) missing files don't error, (6) no-write when lang already matches, (7) get_language() used as default when lang arg is omitted, (8) LaTeX en header has no babel, (9) LaTeX vi header includes babel, (10) header includes auto-generated comment, (11) env-driven babel injection works for both en and vi.

## Requirements Advanced

- R005 — Delivered epub_metadata.yaml lang patching, LaTeX babel injection, and state.json language field — all verified by 15 automated tests

## Requirements Validated

- R005 — 15 tests covering state.json language field, epub metadata lang patching for en/vi, LaTeX babel injection, field preservation, no-op optimization, and missing file handling

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Deviations

Wrapped build_tex.py module-level code in main() with __name__ guard — necessary to allow clean test imports without triggering file I/O on missing chapter files. Replaced hardcoded /home/jeffq/autonovel/ paths with config.py-derived paths so the script works in any checkout.

## Known Limitations

LaTeX compilation is not tested (requires a LaTeX installation). The regex-based YAML patching assumes epub_metadata.yaml has a simple flat structure — it would need rework if the YAML becomes deeply nested. EB Garamond supports Vietnamese glyphs but actual PDF rendering is not verified in automated tests.

## Follow-ups

S05 will validate end-to-end pipeline with AUTONOVEL_LANGUAGE=vi, which serves as the real integration test for all four slices combined.

## Files Created/Modified

- `run_pipeline.py` — Added language field to default_state() reading from config.get_language()
- `typeset/build_tex.py` — Added patch_epub_metadata(), generate_latex_header(), wrapped code in main(), replaced hardcoded paths with config.py constants
- `typeset/epub_metadata.yaml` — Template file — lang field is now dynamically patched at runtime
- `test_s04_export.py` — 15 tests covering state language field, epub metadata patching, and LaTeX babel injection
