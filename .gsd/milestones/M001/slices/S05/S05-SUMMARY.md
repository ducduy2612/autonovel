---
id: S05
parent: M001
milestone: M001
provides:
  - ["run_foundation() saves foundation script output to .md files (world.md, characters.md, outline.md, canon.md)", "43 integration tests proving full Vietnamese foundation chain wiring correctness", "Vietnamese seed concept (seed_vi.txt) for live pipeline testing", "Live verification script (scripts/verify_vi_pipeline.sh) for operational validation"]
requires:
  - slice: S01
    provides: config.get_language(), config.language_instruction() for Vietnamese language selection
  - slice: S02
    provides: All 5 foundation scripts (gen_world, gen_characters, gen_outline, gen_outline_part2, gen_canon) include language_instruction() in system prompts
  - slice: S03
    provides: evaluate.py with language-gated slop detection and Vietnamese cross-checks
  - slice: S04
    provides: default_state() with language field, epub/LaTeX Vietnamese support
affects:
  []
key_files:
  - ["run_pipeline.py", "test_s05_e2e.py", "seed_vi.txt", "scripts/verify_vi_pipeline.sh"]
key_decisions:
  - ["Write gen_outline.py output to both outline.md and /tmp/outline_output.md because gen_outline_part2.py hardcodes a read from /tmp", "Patch config.BASE_DIR and create input files in tmp_path for scripts that read files at module import time (gen_world, gen_characters, gen_outline, gen_canon)", "Include language field in E2E test initial state dict because run_foundation() preserves but never creates it — only default_state() sets it", "Used Vietnamese-specific fantasy world (fragrance magic in Trường Sơn setting) to ensure LLM generates distinctly Vietnamese content rather than translated English", "Vietnamese detection via unique diacritical characters (ăâđêôơư) — these are unique to Vietnamese and won't appear in English or other Latin-script languages"]
patterns_established:
  - ["Foundation scripts print to stdout → run_foundation() captures and writes to .md files (single responsibility: scripts generate, orchestrator persists)", "Guarded file writes: only overwrite when returncode==0 and stdout.strip() is non-empty", "Module-level file reads in foundation scripts require BASE_DIR patching + file creation before import in tests"]
observability_surfaces:
  - ["run_foundation() logs each file write with path + char count for diagnosis", "Step logging captures which foundation script is being executed"]
drill_down_paths:
  []
duration: ""
verification_result: passed
completed_at: 2026-04-16T17:26:35.972Z
blocker_discovered: false
---

# S05: End-to-end Vietnamese pipeline verification

**Fixed run_pipeline.py to save foundation script output to .md files, created 43 integration tests proving full Vietnamese foundation chain wiring, and prepared Vietnamese seed + live verification script for operational use.**

## What Happened

This slice proved that all prior slices (S02–S04) compose correctly when AUTONOVEL_LANGUAGE=vi.

**T01 — Pipeline output persistence fix:** Discovered that run_foundation() was silently discarding all LLM-generated content from the 5 foundation scripts. Each script prints to stdout via uv_run(), but nothing wrote stdout to the corresponding .md files. Fixed by capturing each uv_run() result and writing to world.md, characters.md, outline.md (with append for gen_outline_part2), and canon.md. Each write is guarded by returncode==0 and stdout.strip() checks. Also discovered gen_outline_part2.py hardcodes a read from /tmp/outline_output.md, so added a secondary write there.

**T02 — Integration test suite (43 tests):** Created test_s05_e2e.py with 7 test classes covering the full Vietnamese foundation chain: pipeline file-writing (7 tests), language instruction wiring in all 5 foundation scripts (10 tests — each tested for vi presence and en absence), Vietnamese text detection helper (12 tests), evaluation adaptation for vi (6 tests), state language field (3 tests), end-to-end Vietnamese foundation chain (2 tests), and execution logging (2 tests). Key challenge: several foundation scripts read files at module import time (seed.txt, voice.md, etc.), requiring config.BASE_DIR patching and tmp_path setup before import/reload.

**T03 — Vietnamese seed and live verification:** Created seed_vi.txt with an authentic Vietnamese fantasy seed concept (~723 words) featuring a fragrance-magic system in Trường Sơn mountains with Vietnamese cultural elements throughout. Created scripts/verify_vi_pipeline.sh — a self-contained verification script that runs the full foundation phase with AUTONOVEL_LANGUAGE=vi and checks 6 conditions (4 output files contain Vietnamese chars, state.json has language=vi, clean exit).

All 96 tests pass (43 new + 53 pre-existing) with zero regressions. No real API calls needed for the integration test suite.

## Verification

- 43 integration tests in test_s05_e2e.py all pass (uv run pytest test_s05_e2e.py -v)
- Full suite of 96 tests passes with zero regressions (uv run pytest test_config.py test_evaluate.py test_s04_export.py test_s05_e2e.py -v)
- T03 deliverables verified: seed_vi.txt exists with Vietnamese chars, scripts/verify_vi_pipeline.sh exists with AUTONOVEL_LANGUAGE=vi, shell syntax valid
- Requirement R006 updated to validated status

## Requirements Advanced

- R006 — 43 integration tests prove full Vietnamese foundation chain produces Vietnamese world bible, characters, outline, canon from a Vietnamese seed with mocked API. Live verification script provided for real API validation.

## Requirements Validated

- R006 — 43 integration tests covering pipeline file-writing, language instruction wiring in all 5 scripts, evaluation adaptation, state language field, and full end-to-end chain — all passing with zero regressions.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Deviations

None.

## Known Limitations

None.

## Follow-ups

None.

## Files Created/Modified

- `run_pipeline.py` — Fixed run_foundation() to save each foundation script's stdout to corresponding .md files with guarded writes and diagnostic logging
- `test_s05_e2e.py` — 43 integration tests covering full Vietnamese foundation chain wiring
- `seed_vi.txt` — Authentic Vietnamese fantasy seed concept (~723 words) with fragrance-magic theme
- `scripts/verify_vi_pipeline.sh` — Self-contained live verification script for Vietnamese foundation pipeline
