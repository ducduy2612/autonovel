# S03: Evaluation adaptation for Vietnamese — UAT

**Milestone:** M001
**Written:** 2026-04-16T16:54:27.081Z

# S03: Evaluation adaptation for Vietnamese — UAT

**Milestone:** M001
**Written:** 2026-04-16

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: Changes are in pure Python logic with no runtime/server dependencies. Automated tests cover all behavioral contracts.

## Preconditions

- Working directory is the project root with `.env` containing `AUTONOVEL_LANGUAGE=en` (default)
- `uv` is installed and project dependencies are available

## Smoke Test

```bash
uv run pytest test_evaluate.py -v
```
All 12 tests pass.

## Test Cases

### 1. English slop detection unchanged

1. Set `AUTONOVEL_LANGUAGE=en`
2. Run `uv run pytest test_evaluate.py::TestSlopScore::test_english_text_en_language -v`
3. **Expected:** Test passes — English text triggers full regex detection (tier1/tier2/tier3 lists may be non-empty)

### 2. Vietnamese skips English regex

1. Set `AUTONOVEL_LANGUAGE=vi`  
2. Run `uv run pytest test_evaluate.py::TestSlopScore::test_english_text_vi_language -v`
3. **Expected:** Test passes — all English-specific fields are empty/zero lists

### 3. Vietnamese text evaluation

1. Set `AUTONOVEL_LANGUAGE=vi`
2. Run `uv run pytest test_evaluate.py::TestSlopScore::test_vietnamese_text_vi_language -v`
3. **Expected:** Test passes — English patterns skipped, agnostic stats computed

### 4. Language-agnostic stats computed for both languages

1. Run `uv run pytest test_evaluate.py::TestSlopScore::test_em_dash_computed_both_languages test_evaluate.py::TestSlopScore::test_sentence_cv_computed_both_languages -v`
2. **Expected:** Both pass — `em_dash_density` and `sentence_length_cv` computed regardless of language

### 5. Foundation prompt cross-checks language-adaptive

1. Run `uv run pytest test_evaluate.py::TestPromptAdaptation::test_foundation_prompt_english_cross_checks test_evaluate.py::TestPromptAdaptation::test_foundation_prompt_vietnamese_cross_checks -v`
2. **Expected:** EN cross-checks mention ANTI-SLOP/structural formulas; VI cross-checks mention Vietnamese AI clichés

### 6. Chapter prompt cross-checks language-adaptive

1. Run `uv run pytest test_evaluate.py::TestPromptAdaptation::test_chapter_prompt_english_cross_checks test_evaluate.py::TestPromptAdaptation::test_chapter_prompt_vietnamese_cross_checks -v`
2. **Expected:** EN checks mention English AI patterns; VI checks mention Vietnamese prose patterns

### 7. Full novel prompt unchanged by language

1. Run `uv run pytest test_evaluate.py::TestPromptAdaptation::test_full_novel_prompt_unchanged -v`
2. **Expected:** Pass — FULL_NOVEL_PROMPT content is identical regardless of language

### 8. Penalty computation correct for VI

1. Run `uv run pytest test_evaluate.py::TestSlopScore::test_penalty_agnostic_only_for_vi -v`
2. **Expected:** Pass — penalty only reflects em-dash density and sentence-length CV when language=vi

## Edge Cases

### Return shape consistency

1. Run `uv run pytest test_evaluate.py::TestSlopScore::test_return_shape_consistent -v`
2. **Expected:** Both EN and VI return dicts with identical keys

## Failure Signals

- Any test in test_evaluate.py fails
- `slop_score()` returns different dict keys depending on language
- Vietnamese text triggers English regex false positives

## Not Proven By This UAT

- Live LLM judge behavior with Vietnamese text (only prompt construction is tested, not API calls)
- End-to-end pipeline integration (deferred to S05)
- Vietnamese-specific regex patterns (not yet implemented — D003 notes this is revisable)

