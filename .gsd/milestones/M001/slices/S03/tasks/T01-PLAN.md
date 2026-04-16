---
estimated_steps: 10
estimated_files: 3
skills_used: []
---

# T01: Gate slop_score() for language and write mechanical layer tests

Add `from config import get_language` to evaluate.py. Refactor `slop_score()` so that when `get_language() == 'vi'`, all English-specific pattern matching is skipped: TIER1_BANNED, TIER2_SUSPICIOUS, TIER3_FILLER, TRANSITION_OPENERS, FICTION_AI_TELLS, STRUCTURAL_AI_TICS, and TELLING_PATTERNS. For vi, return empty lists/zeros for all English-specific dict keys, but still compute em_dash_density and sentence_length_cv. The slop_penalty should be computed only from language-agnostic stats (em-dash density and sentence-length CV) when language=vi. Add a `"language": get_language()` field to the returned dict for observability.

Create `test_evaluate.py` with a `TestSlopScore` class containing:
- `test_english_text_en_language`: English sample text, AUTONOVEL_LANGUAGE=en → full detection runs, tier1/tier2/tier3 lists may be non-empty
- `test_english_text_vi_language`: English sample text, AUTONOVEL_LANGUAGE=vi → English patterns skipped, all English-specific fields are empty/zero
- `test_vietnamese_text_vi_language`: Vietnamese sample text, AUTONOVEL_LANGUAGE=vi → English patterns skipped, agnostic stats computed
- `test_return_shape_consistent`: Both languages return the same dict keys
- `test_penalty_agnostic_only_for_vi`: When vi, penalty only reflects em-dash density and sentence-length CV
- `test_em_dash_computed_both_languages`: em_dash_density is computed regardless of language
- `test_sentence_cv_computed_both_languages`: sentence_length_cv is computed regardless of language

Use `monkeypatch` or `os.environ` to set AUTONOVEL_LANGUAGE before importing/reloading evaluate. Follow the same reload pattern as test_config.py.

## Inputs

- ``evaluate.py` — current slop_score() function to gate`
- ``config.py` — get_language() function to import`

## Expected Output

- ``evaluate.py` — slop_score() gated by get_language(), 'language' field in return dict`
- ``test_evaluate.py` — TestSlopScore class with 7 tests covering both language paths`

## Verification

uv run pytest test_evaluate.py -v
