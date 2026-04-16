---
id: T01
parent: S04
milestone: M001
key_files:
  - run_pipeline.py
  - typeset/build_tex.py
  - test_s04_export.py
key_decisions:
  - Used regex-based YAML patching instead of PyYAML to avoid adding a dependency
  - Wrapped build_tex.py module-level code in main() guard to enable clean test imports
duration: 
verification_result: passed
completed_at: 2026-04-16T16:59:46.070Z
blocker_discovered: false
---

# T01: Add language field to state.json and dynamic lang patching in epub_metadata.yaml

**Add language field to state.json and dynamic lang patching in epub_metadata.yaml**

## What Happened

Added a `"language"` field to `default_state()` in `run_pipeline.py` that reads from `config.get_language()`, so state.json now propagates the configured language (e.g. "en" or "vi"). Created a `patch_epub_metadata()` helper in `typeset/build_tex.py` that regex-patches the `lang:` line in `epub_metadata.yaml` before LaTeX content generation, using `get_language()` as the default source. Wrapped the existing module-level chapter-processing code in `build_tex.py` into a `main()` function with `if __name__ == "__main__"` guard so the module can be imported for testing without triggering file I/O on missing chapter files. Also replaced the hardcoded `/home/jeffq/autonovel/` paths with project-root-relative paths derived from `Path(__file__).resolve().parent.parent`. Created `test_s04_export.py` with 10 tests covering default language, vi language, epub metadata patching for both en and vi, no-change optimization, field preservation, missing file handling, and get_language() default propagation. All 36 tests (10 new + 26 existing) pass.

## Verification

Ran `uv run pytest test_s04_export.py test_config.py -v` — all 36 tests pass. Tests verify: (1) default_state() includes language='en' by default, (2) default_state() with AUTONOVEL_LANGUAGE=vi includes language='vi', (3) patch_epub_metadata() patches lang to 'vi' and 'en' correctly, (4) other YAML fields are preserved, (5) missing files don't error, (6) no-write when lang already matches, (7) get_language() used as default when lang arg is omitted.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `uv run pytest test_s04_export.py test_config.py -v` | 0 | ✅ pass | 3000ms |

## Deviations

Wrapped existing module-level code in build_tex.py into a main() function with __name__ guard — not in the plan but necessary because the chapter-processing loop ran on import and failed when no chapter files existed. Also replaced hardcoded /home/jeffq/autonovel/ paths with project-root-relative paths so the script works in any checkout.

## Known Issues

None.

## Files Created/Modified

- `run_pipeline.py`
- `typeset/build_tex.py`
- `test_s04_export.py`
