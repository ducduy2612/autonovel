---
id: T01
parent: S03
milestone: M001
key_files:
  - evaluate.py
  - test_evaluate.py
key_decisions:
  - Used a local `is_en` boolean inside slop_score() rather than creating separate functions per language, keeping the existing structure intact and making it easy to add more languages later
duration: 
verification_result: passed
completed_at: 2026-04-16T16:41:21.894Z
blocker_discovered: false
---

# T01: Gate slop_score() to skip English regex patterns when language=vi, keeping agnostic stats and adding language field for observability

**Gate slop_score() to skip English regex patterns when language=vi, keeping agnostic stats and adding language field for observability**

## What Happened

Refactored `slop_score()` in `evaluate.py` to gate all English-specific pattern matching (TIER1_BANNED, TIER2_SUSPICIOUS, TIER3_FILLER, TRANSITION_OPENERS, FICTION_AI_TELLS, STRUCTURAL_AI_TICS, TELLING_PATTERNS) behind an `is_en = (get_language() == "en")` check. When `language=vi`, all English-specific fields return empty lists/zeros, while `em_dash_density` and `sentence_length_cv` continue to be computed. The `slop_penalty` for vi only includes contributions from the two agnostic stats. Added a `"language"` field to the returned dict for observability. Created `test_evaluate.py` with 7 tests in `TestSlopScore` covering both language paths, return-shape consistency, penalty isolation for vi, and agnostic stat computation across languages.

## Verification

Ran `uv run pytest test_evaluate.py -v` — all 7 tests pass: test_english_text_en_language, test_english_text_vi_language, test_vietnamese_text_vi_language, test_return_shape_consistent, test_penalty_agnostic_only_for_vi, test_em_dash_computed_both_languages, test_sentence_cv_computed_both_languages.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `uv run pytest test_evaluate.py -v` | 0 | ✅ pass | 20ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `evaluate.py`
- `test_evaluate.py`
