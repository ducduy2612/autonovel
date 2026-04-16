# S03: Evaluation adaptation for Vietnamese

**Goal:** Gate slop_score() to skip English regex patterns when language=vi, keeping language-agnostic stats (em-dash density, sentence-length CV). Adapt CROSS-CHECKS sections in FOUNDATION_PROMPT and CHAPTER_PROMPT to instruct the LLM judge to detect Vietnamese AI clichés when language=vi. English evaluation behavior must remain completely unchanged.
**Demo:** Run evaluate.py --phase=foundation with Vietnamese text — English regex slop detection is skipped, language-agnostic stats still run, LLM judge evaluates in Vietnamese. Run with English text — full regex detection runs as before.

## Must-Haves

- slop_score() returns empty lists for all English-specific fields (tier1_hits, tier2_hits, tier3_hits, fiction_ai_tells, structural_ai_tics, telling_violations) when language=vi
- slop_score() still computes em_dash_density and sentence_length_cv regardless of language
- slop_penalty is computed only from language-agnostic stats when language=vi
- FOUNDATION_PROMPT cross-checks reference Vietnamese AI patterns when language=vi, English patterns when language=en
- CHAPTER_PROMPT cross-checks reference Vietnamese AI patterns when language=vi, English patterns when language=en
- call_judge() system prompt already uses analysis_language_note() — no changes needed
- FULL_NOVEL_PROMPT unchanged (language-agnostic dimensions)
- All tests in test_evaluate.py pass

## Proof Level

- This slice proves: contract

## Integration Closure

- Upstream surfaces consumed: config.py get_language() (from S01)
- New wiring introduced: None — conditional logic inside existing functions
- What remains before milestone is truly usable end-to-end: S04 (generation scripts), S05 (end-to-end pipeline run)

## Verification

- When language=vi, slop_score() returns a dict with "language": "vi" field so downstream consumers and logs can identify which evaluation path was taken. This is the only observability addition — evaluation logs already capture the full result dict.

## Tasks

- [x] **T01: Gate slop_score() for language and write mechanical layer tests** `est:1h`
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
  - Files: `evaluate.py`, `test_evaluate.py`, `config.py`
  - Verify: uv run pytest test_evaluate.py -v

- [x] **T02: Adapt judge prompt cross-checks for Vietnamese and write prompt tests** `est:1h`
  Extract the CROSS-CHECKS sections from FOUNDATION_PROMPT and CHAPTER_PROMPT into separate variables. Create two variants for each:

1. `_EN_FOUNDATION_CROSS_CHECKS` — the existing 4 cross-check items (ANTI-SLOP patterns, negative space, convenient gaps, internal contradictions)
2. `_VI_FOUNDATION_CROSS_CHECKS` — Vietnamese-aware cross-checks that instruct the LLM to: detect Vietnamese AI clichés (repetitive sentence structures, unnatural phrasing, translation artifacts), check for missing cultural specificity, evaluate prose naturalness in Vietnamese
3. `_EN_CHAPTER_CROSS_CHECKS` — the existing 5 cross-check items (quote test, dialogue realism, scene vs summary, AI pattern check, earned vs given)
4. `_VI_CHAPTER_CROSS_CHECKS` — Vietnamese-aware chapter cross-checks that instruct the LLM to: detect Vietnamese AI writing patterns (uniform paragraph rhythm, translation-sounding prose), check dialogue sounds like natural Vietnamese speech, look for Vietnamese-specific prose clichés

Replace the hardcoded cross-checks in FOUNDATION_PROMPT and CHAPTER_PROMPT with a `{cross_checks}` format placeholder. In `evaluate_foundation()`, select the appropriate cross-checks based on `get_language()` and pass it as a format argument. Similarly for `evaluate_chapter()`.

FULL_NOVEL_PROMPT needs no changes — its dimensions (arc completion, pacing, etc.) are language-agnostic, and the system prompt already uses `analysis_language_note()`.

Extend `test_evaluate.py` with a `TestPromptAdaptation` class:
- `test_foundation_prompt_english_cross_checks`: AUTONOVEL_LANGUAGE=en → cross-checks mention English-specific patterns (ANTI-SLOP, structural formulas)
- `test_foundation_prompt_vietnamese_cross_checks`: AUTONOVEL_LANGUAGE=vi → cross-checks mention Vietnamese AI clichés
- `test_chapter_prompt_english_cross_checks`: AUTONOVEL_LANGUAGE=en → cross-checks mention English AI patterns
- `test_chapter_prompt_vietnamese_cross_checks`: AUTONOVEL_LANGUAGE=vi → cross-checks mention Vietnamese prose patterns
- `test_full_novel_prompt_unchanged`: FULL_NOVEL_PROMPT content is identical regardless of language

These tests should call the prompt-building functions directly (or inspect the constructed prompt strings) to verify the correct cross-checks are injected.
  - Files: `evaluate.py`, `test_evaluate.py`
  - Verify: uv run pytest test_evaluate.py -v

## Files Likely Touched

- evaluate.py
- test_evaluate.py
- config.py
