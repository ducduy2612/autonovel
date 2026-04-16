---
id: T02
parent: S03
milestone: M001
key_files:
  - evaluate.py
  - test_evaluate.py
key_decisions:
  - Used _get_cross_checks(prefix) helper with globals() lookup rather than if/else chains, making it easy to add more languages by just adding new _{LANG}_{PREFIX}_CROSS_CHECKS variables
  - Kept item 4 (INTERNAL CONTRADICTIONS) identical in both EN and VI foundation cross-checks since it's language-agnostic, differing only in items 1-3 which are language-specific
duration: 
verification_result: passed
completed_at: 2026-04-16T16:52:38.125Z
blocker_discovered: false
---

# T02: Extract FOUNDATION_PROMPT and CHAPTER_PROMPT cross-checks into EN/VI variants with {cross_checks} placeholder, add _get_cross_checks() helper, and write 5 prompt-adaptation tests

**Extract FOUNDATION_PROMPT and CHAPTER_PROMPT cross-checks into EN/VI variants with {cross_checks} placeholder, add _get_cross_checks() helper, and write 5 prompt-adaptation tests**

## What Happened

Extracted the hardcoded CROSS-CHECKS sections from both FOUNDATION_PROMPT and CHAPTER_PROMPT into four separate module-level variables: `_EN_FOUNDATION_CROSS_CHECKS` (existing 4 English checks: ANTI-SLOP patterns, negative space, convenient gaps, internal contradictions), `_VI_FOUNDATION_CROSS_CHECKS` (Vietnamese-aware: AI cliché detection, cultural specificity, prose naturalness, internal contradictions), `_EN_CHAPTER_CROSS_CHECKS` (existing 5 English checks: quote test, dialogue realism, scene vs summary, AI pattern check, earned vs given), and `_VI_CHAPTER_CROSS_CHECKS` (Vietnamese-aware: quote test with Vietnamese focus, dialogue naturalness with particles/pronouns, scene vs summary, Vietnamese AI pattern check, earned vs given). Replaced the inline cross-checks in both prompt templates with a `{cross_checks}` format placeholder. Added `_get_cross_checks(prefix)` helper that selects the correct variant based on `get_language()`. Updated `evaluate_foundation()` to pass `cross_checks=_get_cross_checks("FOUNDATION")` and `evaluate_chapter()` to pass `cross_checks=_get_cross_checks("CHAPTER")` as format arguments. FULL_NOVEL_PROMPT left unchanged — its dimensions are language-agnostic. Added `TestPromptAdaptation` class with 5 tests verifying EN/VI cross-check injection for both prompts and FULL_NOVEL_PROMPT immutability. All 12 tests (7 T01 + 5 T02) pass.

## Verification

Ran `uv run pytest test_evaluate.py -v` — all 12 tests pass: 7 TestSlopScore tests from T01 and 5 new TestPromptAdaptation tests (test_foundation_prompt_english_cross_checks, test_foundation_prompt_vietnamese_cross_checks, test_chapter_prompt_english_cross_checks, test_chapter_prompt_vietnamese_cross_checks, test_full_novel_prompt_unchanged). Also manually verified prompt formatting with both languages via Python one-liner checks.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `uv run pytest test_evaluate.py -v` | 0 | ✅ pass | 30ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `evaluate.py`
- `test_evaluate.py`
