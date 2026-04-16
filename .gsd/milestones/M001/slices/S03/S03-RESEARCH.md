# S03: Evaluation adaptation for Vietnamese — Research

**Date:** 2026-04-16

## Summary

The evaluation system has two layers: (1) mechanical regex-based slop detection in `slop_score()`, and (2) LLM judge prompts (`FOUNDATION_PROMPT`, `CHAPTER_PROMPT`, `FULL_NOVEL_PROMPT`). For Vietnamese (`language=vi`), all English-specific regex patterns must be skipped — they would produce false negatives on Vietnamese text. The only truly language-agnostic mechanical checks are em-dash density and sentence-length coefficient of variation (CV). The LLM judge layer needs its system prompt and evaluation instructions adapted to evaluate Vietnamese prose quality directly.

Four additional evaluation scripts exist (`review.py`, `reader_panel.py`, `compare_chapters.py`, `adversarial_edit.py`) — these are LLM-driven (no regex slop detection) and conceptually language-agnostic, but their prompts are written assuming English text. They are NOT in scope for this slice per the roadmap (which only calls out `evaluate.py`), but the planner should note them for future work.

## Recommendation

Wrap all English-specific pattern lists and the `slop_score()` function body with a `get_language()` gate. When `language == 'vi'`, `slop_score()` returns only the two language-agnostic stats (em-dash density, sentence-length CV) with zero penalty from regex checks. Adapt the `call_judge()` system prompt to instruct evaluation in Vietnamese. The three judge prompts (`FOUNDATION_PROMPT`, `CHAPTER_PROMPT`, `FULL_NOVEL_PROMPT`) should remain in English as instructions to the LLM, but their anti-slop cross-check sections should be wrapped in language-conditional blocks — for Vietnamese, replace English-specific pattern checks with an instruction for the LLM to detect Vietnamese AI clichés natively.

This approach is minimal, testable, and keeps English behavior completely unchanged.

## Implementation Landscape

### Key Files

- **`evaluate.py`** — The primary target. Contains `slop_score()` (mechanical regex layer) and all LLM judge prompts. Needs `from config import get_language` and conditional logic in two places: the `slop_score()` function and the prompt construction/`call_judge()` system prompt.

- **`config.py`** — Already provides `get_language()` returning `'en'` or `'vi'`. No changes needed. Import pattern: `from config import get_language`.

### Detailed Analysis: `slop_score()` Breakdown

The function returns a dict with these keys. Here's what's English-specific vs language-agnostic:

| Component | English-specific? | Action for `vi` |
|---|---|---|
| `TIER1_BANNED` (word list) | Yes — English buzzwords | Skip entirely |
| `TIER2_SUSPICIOUS` (word list) | Yes — English suspicious words | Skip entirely |
| `TIER3_FILLER` (regex patterns) | Yes — English filler phrases | Skip entirely |
| `TRANSITION_OPENERS` (word list) | Yes — English transition words | Skip entirely |
| `FICTION_AI_TELLS` (regex patterns) | Yes — English prose clichés | Skip entirely |
| `STRUCTURAL_AI_TICS` (regex patterns) | Yes — English rhetorical formulas | Skip entirely |
| `TELLING_PATTERNS` (regex patterns) | Yes — English show-don't-tell | Skip entirely |
| `em_dash_density` | **No** — punctuation counting | Keep |
| `sentence_length_cv` | **No** — statistical measure | Keep |
| `transition_opener_ratio` | Yes — uses `TRANSITION_OPENERS` | Skip |
| Composite `slop_penalty` | Mixed — only em-dash + CV apply for `vi` | Recompute from agnostic stats only |

When `language == 'vi'`, `slop_score()` should return the same dict shape but with empty lists for all English-specific fields, and the penalty computed only from em-dash density and sentence-length CV.

### Detailed Analysis: LLM Judge Prompts

Three prompts in `evaluate.py`:

1. **`FOUNDATION_PROMPT`** (~200 lines) — Evaluates planning docs. Contains a "CROSS-CHECKS" section that instructs the LLM to check for "ANTI-SLOP patterns", "structural formulas", "AI rhetorical tics". These cross-check instructions reference English patterns. For Vietnamese, the cross-checks should instruct the LLM to look for Vietnamese AI clichés instead (or use a generic "look for AI-generated prose patterns in the target language" instruction).

2. **`CHAPTER_PROMPT`** (~180 lines) — Evaluates chapters. Contains "AI PATTERN CHECK" section with English-specific detection instructions (same-paragraph-length, observations in threes, emotional beats on schedule, etc.). These are partially language-agnostic (structural patterns) and partially English-specific (specific phrasing). For Vietnamese, adapt to "look for AI-generated prose patterns in Vietnamese text".

3. **`FULL_NOVEL_PROMPT`** (~30 lines) — Evaluates full novel. No English-specific regex references. Mostly language-agnostic dimensions (arc completion, pacing, etc.). Minimal changes needed — possibly just the system prompt.

4. **`call_judge()` system prompt** — Currently says "You are a literary critic and novel editor." Should be adapted to mention Vietnamese evaluation capability when `language == 'vi'`.

### Out-of-Scope Scripts (Note Only)

- **`review.py`** — LLM-driven dual-persona review. No regex slop detection. Prompts are English but conceptually language-agnostic. The `should_stop()` function parses English text from LLM responses (star ratings, severity words) which works regardless of input language since the LLM responds in English. **Not in scope for S03.**
- **`reader_panel.py`** — 4-reader panel. Pure LLM. Reader personas reference specific English-language fantasy authors (Sanderson, Le Guin, Jemisin, etc.). **Not in scope for S03.**
- **`compare_chapters.py`** — Head-to-head chapter comparison. Pure LLM. Comparison criteria are mostly language-agnostic. **Not in scope for S03.**
- **`adversarial_edit.py`** — Cut/revision identification. Pure LLM. Classification system (FAT, REDUNDANT, etc.) is language-agnostic. **Not in scope for S03.**

### Build Order

1. **First: Add `get_language()` import to `evaluate.py`** — foundation for all conditional logic.
2. **Second: Gate `slop_score()`** — wrap all English regex lists in `if get_language() == 'en':` blocks. Return empty lists for `vi` while preserving em-dash density and sentence-length CV. Recompute penalty from agnostic stats only.
3. **Third: Adapt `call_judge()` system prompt** — add Vietnamese-aware instruction when `language == 'vi'`.
4. **Fourth: Adapt prompt cross-checks** — wrap English-specific cross-check instructions in `FOUNDATION_PROMPT` and `CHAPTER_PROMPT` with language-conditional alternatives.
5. **Fifth: Verify** — run `evaluate.py --phase=foundation` with Vietnamese text and English text to confirm both paths work.

### Verification Approach

1. **English path unchanged**: Run `evaluate.py --phase=foundation` with `AUTONOVEL_LANGUAGE=en` (default). Compare slop_score output against baseline — should be identical to current behavior.
2. **Vietnamese path skips regex**: Run `evaluate.py --phase=foundation` with `AUTONOVEL_LANGUAGE=vi` on Vietnamese text. Confirm `slop_score()` returns empty lists for all English-specific fields, but still computes `em_dash_density` and `sentence_length_cv`.
3. **Vietnamese LLM judge**: Confirm the judge system prompt and cross-check sections are adapted when `language == 'vi'`. The LLM should evaluate Vietnamese prose quality without referencing English slop patterns.
4. **Edge case**: Run with Vietnamese text + `AUTONOVEL_LANGUAGE=en` — English regex runs (producing meaningless results on Vietnamese text, which is expected/correct behavior since the user set the wrong language).
