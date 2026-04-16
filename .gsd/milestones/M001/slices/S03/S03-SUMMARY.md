---
id: S03
parent: M001
milestone: M001
provides:
  - ["slop_score() returns language-aware results with empty English fields for vi", "FOUNDATION_PROMPT and CHAPTER_PROMPT cross-checks selected by language", "\"language\" field in slop_score() output dict for observability"]
requires:
  - slice: S01
    provides: config.py get_language() returning 'en' or 'vi'
affects:
  - ["S05"]
key_files:
  - ["evaluate.py", "test_evaluate.py"]
key_decisions:
  - ["Used local is_en boolean in slop_score() rather than separate functions per language — keeps existing structure intact, easy to extend", "Used _get_cross_checks(prefix) helper with globals() lookup — adding new languages only requires defining new _{LANG}_{PREFIX}_CROSS_CHECKS variables"]
patterns_established:
  - ["Language-gated pattern matching: gate regex lists behind is_en boolean at function entry", "Cross-check selection via globals() lookup: _get_cross_checks(prefix) resolves _{LANG}_{PREFIX}_CROSS_CHECKS dynamically"]
observability_surfaces:
  - none
drill_down_paths:
  - [".gsd/milestones/M001/slices/S03/tasks/T01-SUMMARY.md", ".gsd/milestones/M001/slices/S03/tasks/T02-SUMMARY.md"]
duration: ""
verification_result: passed
completed_at: 2026-04-16T16:54:27.081Z
blocker_discovered: false
---

# S03: Evaluation adaptation for Vietnamese

**slop_score() gates English regex patterns behind language check, prompt cross-checks split into EN/VI variants — Vietnamese evaluation is honest, English evaluation unchanged**

## What Happened

This slice adapted the evaluation layer for Vietnamese support across two tasks.

**T01 — slop_score() language gating:** Added `is_en = (get_language() == "en")` boolean at the top of `slop_score()`. When `language=vi`, all seven English-specific pattern lists (TIER1_BANNED, TIER2_SUSPICIOUS, TIER3_FILLER, TRANSITION_OPENERS, FICTION_AI_TELLS, STRUCTURAL_AI_TICS, TELLING_PATTERNS) are skipped, returning empty lists/zeros. Language-agnostic stats — `em_dash_density` and `sentence_length_cv` — still compute. The `slop_penalty` for vi only includes contributions from these two agnostic stats. Added `"language": get_language()` field to the returned dict for observability. Created 7 tests in `TestSlopScore`.

**T02 — Prompt cross-check adaptation:** Extracted hardcoded CROSS-CHECKS from FOUNDATION_PROMPT and CHAPTER_PROMPT into four module-level variables (`_EN_FOUNDATION_CROSS_CHECKS`, `_VI_FOUNDATION_CROSS_CHECKS`, `_EN_CHAPTER_CROSS_CHECKS`, `_VI_CHAPTER_CROSS_CHECKS`). Added `_get_cross_checks(prefix)` helper using `globals()` lookup pattern. Both prompt templates now use `{cross_checks}` placeholder populated at call time. FULL_NOVEL_PROMPT left unchanged (language-agnostic). Created 5 tests in `TestPromptAdaptation`. All 12 tests pass.

## Verification

All 12 tests pass via `uv run pytest test_evaluate.py -v`:
- 7 TestSlopScore tests: EN text with EN language (full detection), EN text with VI language (English patterns skipped), VI text with VI language (agnostic stats only), return shape consistency, penalty isolation for VI, em-dash computed both languages, sentence CV computed both languages.
- 5 TestPromptAdaptation tests: foundation EN cross-checks, foundation VI cross-checks, chapter EN cross-checks, chapter VI cross-checks, full novel prompt unchanged.

## Requirements Advanced

- R004 — slop_score() gates English regex behind is_en check, cross-checks split into EN/VI variants, 12 automated tests validate both paths

## Requirements Validated

- R004 — 12 tests covering slop_score gating, return shape consistency, penalty isolation, agnostic stat computation, and EN/VI prompt cross-check selection

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

- `evaluate.py` — Added is_en gating in slop_score(), extracted cross-checks into EN/VI variables, added _get_cross_checks() helper, added language field to slop_score output
- `test_evaluate.py` — Created with 12 tests: 7 TestSlopScore (gating, shape, penalty, agnostic stats) + 5 TestPromptAdaptation (cross-check injection for both prompts)
