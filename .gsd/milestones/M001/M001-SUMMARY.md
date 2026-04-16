---
id: M001
title: "Vietnamese Language Support"
status: complete
completed_at: 2026-04-16T17:31:11.467Z
key_decisions:
  - D001: AUTONOVEL_LANGUAGE env var via .env — consistent with existing model config pattern, python-dotenv already loaded
  - D002: Inline conditional instructions per script — minimal structural change for single target language; refactor to shared prompt system if adding more languages
  - D003: Skip English regex for Vietnamese, keep language-agnostic stats, LLM judge evaluates directly — English patterns would false-pass Vietnamese text
  - Two helper functions (language_instruction vs analysis_language_note) — content generators need creative-writing instruction while evaluators need preservation note
  - Regex-based YAML patching for epub_metadata.yaml — avoids adding PyYAML dependency for simple flat YAML
  - Module-level code wrapped in main() guard in build_tex.py — enables clean test imports
  - run_foundation() as orchestrator persists foundation script stdout to .md files — scripts generate, orchestrator persists
key_files:
  - config.py
  - test_config.py
  - test_evaluate.py
  - test_s04_export.py
  - test_s05_e2e.py
  - .env.example
  - evaluate.py
  - run_pipeline.py
  - typeset/build_tex.py
  - typeset/epub_metadata.yaml
  - seed_vi.txt
  - scripts/verify_vi_pipeline.sh
  - gen_world.py
  - gen_characters.py
  - gen_outline.py
  - gen_outline_part2.py
  - draft_chapter.py
  - gen_canon.py
  - gen_revision.py
  - seed.py
  - review.py
  - reader_panel.py
  - compare_chapters.py
  - adversarial_edit.py
  - build_outline.py
  - build_arc_summary.py
lessons_learned:
  - Foundation scripts printed to stdout but run_foundation() didn't persist output — always verify the orchestrator actually saves what scripts produce, not just that scripts run successfully
  - Several foundation scripts read files at module import time (seed.txt, voice.md) using config.BASE_DIR — tests must patch BASE_DIR and create input files before import/reload
  - gen_outline_part2.py hardcodes a read from /tmp/outline_output.md — discovered this dependency only during integration testing; always check for hardcoded paths in scripts
  - Vietnamese detection via unique diacritical characters (ăâđêôơư) is reliable for test assertions — these don't appear in English or other Latin-script languages
  - Helper functions returning empty string for lang=en (no-op pattern) ensures English pipeline is completely unchanged — critical for backward compatibility
---

# M001: Vietnamese Language Support

**Added full Vietnamese language support to the autonovel pipeline — config module, language-aware prompts in all 15 LLM-calling scripts, evaluation adaptation, export/metadata support, and 96 integration tests proving the chain works end-to-end.**

## What Happened

M001 delivered Vietnamese language support across the entire autonovel pipeline through 5 slices completed sequentially:

**S01 — Config module**: Created config.py as the single import point for all pipeline configuration. It centralizes load_dotenv(), exports all env vars (API_KEY, models, paths, keys), and provides get_language() returning 'en' (default) or 'vi' from AUTONOVEL_LANGUAGE. Added .env.example documentation and pytest as a dev dependency. 19 tests cover all config behaviors.

**S02 — Vietnamese prompts**: Added two helper functions to config.py — language_instruction() (for content generators, returns a Vietnamese creative-writing instruction when lang=vi) and analysis_language_note() (for evaluators, returns a Vietnamese-awareness note). Migrated all 15 LLM-calling scripts from manual dotenv/os.environ to centralized config imports. Each script appends the appropriate language helper to its system prompt. 26 tests pass.

**S03 — Evaluation adaptation**: Modified slop_score() to gate all 7 English regex pattern lists behind an is_en boolean check. When lang=vi, English patterns return empty results while language-agnostic stats (em_dash_density, sentence_length_cv) still compute. Split hardcoded CROSS-CHECKS from FOUNDATION_PROMPT and CHAPTER_PROMPT into EN/VI variants with a _get_cross_checks() helper using globals() lookup. 12 tests cover both language paths.

**S04 — Export and metadata**: Added language field to default_state() in run_pipeline.py. Created patch_epub_metadata() for dynamic lang patching in epub_metadata.yaml via regex (avoiding PyYAML dependency). Added generate_latex_header() with conditional \usepackage[vietnamese]{babel} injection. Wrapped build_tex.py module-level code in main() for testability. Replaced hardcoded paths with config.py constants. 15 tests cover all export behaviors.

**S05 — End-to-end verification**: Discovered and fixed a critical bug — run_foundation() was silently discarding all LLM-generated content from foundation scripts (each prints to stdout but nothing wrote to .md files). Fixed by capturing uv_run() stdout and writing to world.md, characters.md, outline.md, and canon.md with guarded writes. Created 43 integration tests covering the full Vietnamese foundation chain: pipeline file-writing, language instruction wiring in all 5 scripts, Vietnamese text detection, evaluation adaptation, state language field, and end-to-end chain. Created seed_vi.txt (authentic Vietnamese fantasy seed) and scripts/verify_vi_pipeline.sh for live verification.

All 96 tests pass with zero regressions. No real API calls required for the test suite.

## Success Criteria Results

### S01: Config module returns 'vi' when AUTONOVEL_LANGUAGE=vi, 'en' by default. .env.example documented.
✅ **Met.** config.py created with get_language() returning 'en' by default and 'vi' when env var set. .env.example updated. 19 tests in test_config.py pass.

### S02: All LLM-calling scripts produce Vietnamese output when lang=vi.
✅ **Met.** All 15 scripts migrated to centralized config imports. 8 content scripts use language_instruction(), 7 evaluation scripts use analysis_language_note(). Grep verification confirms correct wiring. 26 tests pass.

### S03: English regex slop detection skipped for Vietnamese, agnostic stats still run, LLM judge evaluates in Vietnamese.
✅ **Met.** slop_score() gates all English regex behind is_en boolean. Language-agnostic stats (em_dash_density, sentence_length_cv) compute for both languages. Cross-checks split into EN/VI variants. 12 tests pass.

### S04: epub_metadata.yaml lang field, LaTeX babel injection, state.json language field.
✅ **Met.** patch_epub_metadata() patches lang field dynamically. generate_latex_header() injects \usepackage[vietnamese]{babel} for vi. default_state() includes language field from get_language(). 15 tests pass.

### S05: Full foundation loop produces Vietnamese output from Vietnamese seed.
✅ **Met.** Fixed run_foundation() to persist foundation script output. 43 integration tests prove full chain produces Vietnamese content from Vietnamese seed with mocked API. All 96 tests pass.

## Definition of Done Results

### All slices complete
✅ All 5 slices (S01–S05) marked complete in roadmap. GSD database confirms all slice statuses are 'complete'.

### All slice summaries exist
✅ All 5 slice summary files exist at .gsd/milestones/M001/slices/S0*/S0*-SUMMARY.md.

### Cross-slice integration verified
✅ S05 explicitly tested integration across S01–S04 with 43 integration tests covering the full Vietnamese foundation chain. No cross-slice boundary mismatches detected.

### All tests pass with zero regressions
✅ uv run pytest runs all 96 tests across test_config.py, test_evaluate.py, test_s04_export.py, test_s05_e2e.py — all pass in 0.12s.

## Requirement Outcomes

| Requirement | Status Transition | Evidence |
|---|---|---|
| R001 | active → validated | config.py with get_language() delivered in S01. 19 tests in test_config.py pass. All 96 tests pass. |
| R002 | active → validated (S02) | All 15 LLM-calling scripts import and use language helpers. 26 tests + grep verification. |
| R003 | active → validated | S05 E2E tests prove foundation chain produces Vietnamese output. 43 integration tests pass. |
| R004 | active → validated (S03) | slop_score() gates English regex behind is_en. 12 tests cover both language paths. |
| R005 | active → validated (S04) | Export layer adapted: epub metadata, LaTeX babel, state.json language field. 15 tests pass. |
| R006 | active → validated (S05) | 43 integration tests prove full Vietnamese foundation chain. seed_vi.txt + verify script created. |

## Deviations

None. All slices delivered as planned with no blockers or replans.

## Follow-ups

["Live verification: Run scripts/verify_vi_pipeline.sh with real ANTHROPIC_API_KEY to confirm Vietnamese output quality with actual LLM responses", "D002 revisit: If adding more languages beyond Vietnamese, refactor inline conditional instructions to a shared prompt system", "D003 revisit: Add Vietnamese-specific slop patterns once research identifies common Vietnamese AI-writing tells", "Drafting and revision phases (chapter generation, revision loops) were not tested end-to-end — only foundation phase has full integration coverage", "LaTeX compilation not tested (requires LaTeX installation) — verify PDF rendering of Vietnamese diacritics in a live environment"]
