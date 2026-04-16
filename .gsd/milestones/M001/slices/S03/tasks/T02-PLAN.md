---
estimated_steps: 14
estimated_files: 2
skills_used: []
---

# T02: Adapt judge prompt cross-checks for Vietnamese and write prompt tests

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

## Inputs

- ``evaluate.py` — from T01, with get_language import already added`
- ``config.py` — get_language() for language detection`

## Expected Output

- ``evaluate.py` — FOUNDATION_PROMPT and CHAPTER_PROMPT with {cross_checks} placeholder, _EN/_VI cross-check variants, prompt-building logic in evaluate_foundation()/evaluate_chapter()`
- ``test_evaluate.py` — TestPromptAdaptation class with 5 tests covering prompt construction for both languages`

## Verification

uv run pytest test_evaluate.py -v
