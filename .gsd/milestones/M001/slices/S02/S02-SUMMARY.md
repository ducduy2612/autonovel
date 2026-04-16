---
id: S02
parent: M001
milestone: M001
provides:
  - ["language_instruction() helper in config.py for content-generating prompts", "analysis_language_note() helper in config.py for evaluation/analysis prompts", "All 15 LLM-calling scripts wired with language-aware prompt instructions"]
requires:
  - slice: S01
    provides: config.py with get_language() function and centralized config imports
affects:
  - ["S03", "S05"]
key_files:
  - (none)
key_decisions:
  - ["Two separate helper functions (language_instruction vs analysis_language_note) rather than one — content generators need a creative-writing instruction while evaluators need a preservation note with different tone and content", "review.py gained a system prompt where it previously had none — minimal placeholder added to carry the language note"]
patterns_established:
  - ["Pattern: Import language_instruction/analysis_language_note from config, append to system prompt via string concatenation (+ helper())", "Pattern: All LLM-calling scripts use centralized config imports instead of manual dotenv/os.environ", "Pattern: Helper functions return empty string for lang=en (no-op) so English pipeline is unchanged"]
observability_surfaces:
  - none
drill_down_paths:
  - [".gsd/milestones/M001/slices/S02/tasks/T01-SUMMARY.md", ".gsd/milestones/M001/slices/S02/tasks/T02-SUMMARY.md", ".gsd/milestones/M001/slices/S02/tasks/T03-SUMMARY.md"]
duration: ""
verification_result: passed
completed_at: 2026-04-16T16:33:53.098Z
blocker_discovered: false
---

# S02: Vietnamese prompts in all LLM-calling scripts

**All 15 LLM-calling scripts now import from config and append language-aware instructions — content generators produce Vietnamese when lang=vi, evaluators preserve Vietnamese text.**

## What Happened

This slice wired language-aware prompt instructions into every LLM-calling script in the pipeline. Three tasks completed the work:

**T01** added two helper functions to config.py: `language_instruction()` (returns a Vietnamese creative-writing instruction for content-generating prompts when lang=vi) and `analysis_language_note()` (returns a Vietnamese-awareness note for evaluation/analysis prompts when lang=vi). Both delegate to `get_language()` internally. Seven unit tests were added to test_config.py covering empty returns for en, non-empty returns for vi, presence of "Vietnamese" in text, and cross-function differentiation.

**T02** migrated 8 content-generating scripts (gen_world.py, gen_characters.py, gen_outline.py, gen_outline_part2.py, draft_chapter.py, gen_canon.py, gen_revision.py, seed.py) from manual dotenv/os.environ configuration to centralized config imports. Each script now imports `language_instruction` and appends it to the system prompt in its `call_writer()` payload. seed.py's different variable names were unified to config conventions.

**T03** migrated 7 evaluation/judging scripts (evaluate.py, review.py, reader_panel.py, compare_chapters.py, adversarial_edit.py, build_outline.py, build_arc_summary.py) similarly. Each imports `analysis_language_note` and appends it to system prompts. review.py received a new system prompt (previously had none). reader_panel.py had the note appended to all 4 reader personas.

All 26 tests pass. All 15 scripts compile cleanly. No load_dotenv or os.environ.get references remain in any migrated script.

## Verification

All verification passed:

1. **Unit tests**: `uv run pytest test_config.py -v` — 26/26 tests pass (19 existing + 7 new TestLanguageInstruction tests).

2. **Content script wiring**: Grep verification on all 8 content scripts confirms each has exactly 1 `from config import` line, 2 `language_instruction` references (import + usage), and 0 `load_dotenv` references.

3. **Evaluation script wiring**: Grep verification on all 7 evaluation scripts confirms each has exactly 1 `from config import` line, correct `analysis_language_note` count (2 for most, 5 for reader_panel.py with 4 personas + import), and 0 `load_dotenv` references.

4. **Syntax validation**: All 15 scripts pass `python3 -m py_compile`.

5. **Config import smoke test**: All exported symbols (analysis_language_note, language_instruction, JUDGE_MODEL, REVIEW_MODEL, WRITER_MODEL, API_KEY, API_BASE, CHAPTERS_DIR) import successfully from config.

## Requirements Advanced

- R002 — All 15 LLM-calling scripts now import and append language-aware instructions via language_instruction() and analysis_language_note()
- R003 — 8 content-generating scripts append language_instruction() which tells LLM to write in Vietnamese when lang=vi

## Requirements Validated

- R002 — Grep checks confirm all 15 scripts import and use the correct language helper. 26 unit tests pass including 7 new tests for the helpers.

## New Requirements Surfaced

None.

## Requirements Invalidated or Re-scoped

None.

## Deviations

None.

## Known Limitations

The language instruction is only as effective as the LLM's compliance — the wiring guarantees the instruction is sent, but actual Vietnamese output quality depends on the model. End-to-end verification is deferred to S05.

## Follow-ups

S03 (evaluation adaptation) will need to handle Vietnamese text in evaluate.py's regex-based slop detection. S05 will provide end-to-end runtime proof that the pipeline produces Vietnamese output.

## Files Created/Modified

- `config.py` — Added language_instruction() and analysis_language_note() helper functions
- `test_config.py` — Added 7 unit tests in TestLanguageInstruction class
- `gen_world.py` — Migrated to config imports, appended language_instruction() to system prompt
- `gen_characters.py` — Migrated to config imports, appended language_instruction() to system prompt
- `gen_outline.py` — Migrated to config imports, appended language_instruction() to system prompt
- `gen_outline_part2.py` — Migrated to config imports, appended language_instruction() to system prompt
- `draft_chapter.py` — Migrated to config imports, appended language_instruction() to system prompt
- `gen_canon.py` — Migrated to config imports, appended language_instruction() to system prompt
- `gen_revision.py` — Migrated to config imports, appended language_instruction() to system prompt
- `seed.py` — Migrated to config imports (unified var names), appended language_instruction() to system prompt
- `evaluate.py` — Migrated to config imports, appended analysis_language_note() to system prompt
- `review.py` — Migrated to config imports, added new system prompt with analysis_language_note()
- `reader_panel.py` — Migrated to config imports, appended analysis_language_note() to all 4 reader personas
- `compare_chapters.py` — Migrated to config imports, appended analysis_language_note() to system prompt
- `adversarial_edit.py` — Migrated to config imports, appended analysis_language_note() to system prompt
- `build_outline.py` — Migrated to config imports, appended analysis_language_note() to system prompt
- `build_arc_summary.py` — Migrated to config imports, appended analysis_language_note() to system prompt
