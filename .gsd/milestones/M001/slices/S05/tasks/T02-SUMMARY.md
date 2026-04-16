---
id: T02
parent: S05
milestone: M001
key_files:
  - test_s05_e2e.py
key_decisions:
  - Patch config.BASE_DIR and create input files in tmp_path for scripts that read files at module import time (gen_world, gen_characters, gen_outline, gen_canon)
  - Include language field in E2E test initial state dict because run_foundation() preserves but never creates it — only default_state() sets it
duration: 
verification_result: passed
completed_at: 2026-04-16T17:21:24.187Z
blocker_discovered: false
---

# T02: Created test_s05_e2e.py with 43 integration tests covering Vietnamese foundation chain wiring

**Created test_s05_e2e.py with 43 integration tests covering Vietnamese foundation chain wiring**

## What Happened

Created `test_s05_e2e.py` with 43 comprehensive integration tests across 7 test classes covering the full Vietnamese foundation pipeline chain. All tests use mocked API calls (no ANTHROPIC_API_KEY needed).

**Test categories implemented:**

1. **TestPipelineFileWriting (7 tests)** — Validates T01 fix: verifies `run_foundation()` writes each script's stdout to the correct `.md` file (world.md, characters.md, outline.md, canon.md), that gen_outline_part2.py output is appended (not overwritten) to outline.md, that voice_fingerprint.py doesn't write planning doc files, and that failed/empty scripts don't overwrite good prior output.

2. **TestLanguageInstructionWiring (10 tests)** — Validates S02: for each of the 5 foundation scripts (gen_world, gen_characters, gen_outline, gen_outline_part2, gen_canon), mocks httpx.post to capture the API payload and asserts the system prompt contains the Vietnamese creative-writing instruction when AUTONOVEL_LANGUAGE=vi and excludes it when AUTONOVEL_LANGUAGE=en. Required patching config.BASE_DIR and creating input files in tmp_path because scripts read files at module import time.

3. **TestVietnameseDetection (12 tests)** — Tests the `contains_vietnamese()` helper that detects Vietnamese-specific diacritical characters (ă, â, đ, ê, ô, ơ, ư). Covers each char individually, uppercase, mixed text, English-only (false), empty string (false), and Latin accents without Vietnamese chars (false).

4. **TestEvaluationAdaptation (6 tests)** — Validates S03: tests that `slop_score()` with lang=vi returns empty English pattern lists, that `_get_cross_checks('FOUNDATION')` returns Vietnamese cross-checks when lang=vi, and `_get_cross_checks('CHAPTER')` returns Vietnamese cross-checks when lang=vi, plus English counterparts.

5. **TestStateLanguageField (3 tests)** — Validates S04: tests that `default_state()` returns language='vi' when AUTONOVEL_LANGUAGE=vi and language='en' when en.

6. **TestEndToEndVietnameseFoundationChain (2 tests)** — The main integration tests: mock uv_run to return fake Vietnamese content for each script, call run_foundation() with AUTONOVEL_LANGUAGE=vi, verify all output files exist, are non-empty, contain Vietnamese characters, outline contains both parts, and state preserves language='vi'. Also verifies English chain produces no Vietnamese chars.

7. **TestScriptExecutionLogging (2 tests)** — Verifies that run_foundation() logs which script is being tested and logs output file path/size for diagnosis.

**Key implementation decision:** The language instruction wiring tests needed to import scripts that read files at module level (gen_world.py reads seed.txt, voice.md, etc.). Solved by creating all required input files in tmp_path and patching config.BASE_DIR before import/reload. The E2E tests include `language` in the initial state dict because `run_foundation()` preserves but doesn't add the language key — it's set by `default_state()` in the real pipeline.

## Verification

All 43 new tests pass. All 53 pre-existing tests continue to pass. Total: 96 tests passing.

Verified with:
1. `uv run pytest test_s05_e2e.py -v` — 43 passed
2. `uv run pytest test_config.py test_evaluate.py test_s04_export.py test_s05_e2e.py -v` — 96 passed, 0 failed
3. No ANTHROPIC_API_KEY required — all API calls mocked

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `uv run pytest test_s05_e2e.py -v` | 0 | ✅ pass | 5000ms |
| 2 | `uv run pytest test_config.py test_evaluate.py test_s04_export.py test_s05_e2e.py -v` | 0 | ✅ pass | 6000ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `test_s05_e2e.py`
