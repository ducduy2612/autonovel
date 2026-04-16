---
id: T01
parent: S02
milestone: M001
key_files:
  - config.py
  - test_config.py
key_decisions:
  - (none)
duration: 
verification_result: passed
completed_at: 2026-04-16T16:22:57.896Z
blocker_discovered: false
---

# T01: Add language_instruction() and analysis_language_note() helpers to config.py with 7 pytest tests

**Add language_instruction() and analysis_language_note() helpers to config.py with 7 pytest tests**

## What Happened

Added two new public helper functions to config.py:

1. `language_instruction()` — returns a Vietnamese creative-writing instruction string (telling the LLM to write prose, descriptions, dialogue, and narrative in natural literary Vietnamese) when `get_language()=="vi"`, otherwise returns an empty string. Designed to be appended to content-generating prompts.

2. `analysis_language_note()` — returns a Vietnamese-awareness note (telling the LLM the text is Vietnamese, English responses are fine for analysis, but quoted Vietnamese must be preserved exactly) when `get_language()=="vi"`, otherwise returns an empty string. Designed for evaluation/analysis prompts.

Both functions delegate to `get_language()` internally, staying DRY. The instruction text is stored in module-level constants (`_VI_CREATIVE_INSTRUCTION`, `_VI_ANALYSIS_NOTE`) for clarity and easy future editing.

Added `TestLanguageInstruction` class to test_config.py with 7 tests covering: empty returns for "en", non-empty returns for "vi", presence of "Vietnamese" in the text, and cross-function differentiation. All 26 tests (19 existing + 7 new) pass.

## Verification

Ran `uv run pytest test_config.py -v` — all 26 tests pass (19 existing + 7 new TestLanguageInstruction tests). The new tests verify: language_instruction() returns "" for en, returns non-empty containing "Vietnamese" for vi; analysis_language_note() returns "" for en, returns non-empty containing "Vietnamese" for vi; the two functions return different text.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `cd /home/converter/code/autonovel/.gsd/worktrees/M001 && uv run pytest test_config.py -v` | 0 | ✅ pass | 3000ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `config.py`
- `test_config.py`
