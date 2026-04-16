# S02: Vietnamese prompts in all LLM-calling scripts

**Goal:** Add language-aware prompt instructions to all 15 LLM-calling scripts so that when AUTONOVEL_LANGUAGE=vi, content-generating scripts produce Vietnamese output and evaluation scripts preserve Vietnamese text while responding in English.
**Demo:** Run gen_world.py with AUTONOVEL_LANGUAGE=vi and a Vietnamese seed — produces Vietnamese world bible. Run gen_characters.py — produces Vietnamese characters. Same for gen_outline, draft_chapter, gen_canon, voice_fingerprint, gen_brief, gen_revision, seed, review, reader_panel, compare_chapters, adversarial_edit.

## Must-Haves

- `language_instruction()` returns Vietnamese content instruction when lang=vi, empty string when lang=en
- `analysis_language_note()` returns Vietnamese-aware note when lang=vi, empty string when lang=en
- All 8 content-generating scripts import from config and append `language_instruction()` to system prompt
- All 7 evaluation/judging scripts import from config and append `analysis_language_note()` to system prompt
- All existing tests still pass; new tests for both helpers pass

## Proof Level

- This slice proves: contract — unit tests prove helpers return correct strings; grep checks prove every script imports and appends the right helper

## Integration Closure

Upstream: config.py (get_language, API_KEY, WRITER_MODEL, JUDGE_MODEL, REVIEW_MODEL, API_BASE, CHAPTERS_DIR) consumed by all 15 scripts. New wiring: each script's call_* function appends language helper to system prompt. What remains: S05 end-to-end pipeline run with AUTONOVEL_LANGUAGE=vi to verify actual Vietnamese output at runtime.

## Verification

- Not provided.

## Tasks

- [x] **T01: Add language_instruction() and analysis_language_note() to config.py with tests** `est:20m`
  Add two new helper functions to config.py:

1. `language_instruction()` — returns a Vietnamese creative-writing instruction when get_language()=="vi", empty string otherwise. Text: tells LLM to write all prose, descriptions, dialogue, and narrative in natural, literary Vietnamese.

2. `analysis_language_note()` — returns a Vietnamese-awareness note when get_language()=="vi", empty string otherwise. Text: tells LLM the text is Vietnamese, may respond in English for analysis, but must preserve all quoted Vietnamese prose exactly.

Both functions should call get_language() internally (not read the env var directly) to stay DRY.

Add pytest tests to test_config.py in a new class TestLanguageInstruction covering:
- language_instruction() returns "" when lang="en"
- language_instruction() returns non-empty containing "Vietnamese" when lang="vi"
- analysis_language_note() returns "" when lang="en"
- analysis_language_note() returns non-empty containing "Vietnamese" when lang="vi"
- analysis_language_note() text differs from language_instruction() text
  - Files: `config.py`, `test_config.py`
  - Verify: cd /home/converter/code/autonovel/.gsd/worktrees/M001 && uv run pytest test_config.py -v

- [x] **T02: Migrate 8 content-generating scripts to config imports + language_instruction()** `est:30m`
  Migrate these 8 scripts that GENERATE novel content to import from config.py and append language_instruction() to their system prompts:

- gen_world.py (call_writer, system prompt about worldbuilder)
- gen_characters.py (call_writer, system prompt about character designer)
- gen_outline.py (call_writer, system prompt about novel architect)
- gen_outline_part2.py (call_writer, system prompt about continuing outline)
- draft_chapter.py (call_writer, system prompt about literary fiction writer)
- gen_canon.py (call_writer, system prompt about continuity editor)
- gen_revision.py (call_writer, system prompt about rewriting chapters)
- seed.py (call_writer, system prompt about fantasy novelist)

For EACH script, make these exact changes:

1. **Replace imports**: Remove `from dotenv import load_dotenv` and the `load_dotenv(BASE_DIR / '.env')` call. Remove `import os` if no longer needed. Replace `from pathlib import Path` only if it was only used for BASE_DIR (check first — some scripts use Path elsewhere).

2. **Replace config vars**: Replace the manual `os.environ.get(...)` lines with imports from config. The exact imports depend on what the script uses:
   - Scripts using WRITER_MODEL: `from config import get_language, language_instruction, API_KEY, API_BASE, WRITER_MODEL, BASE_DIR`
   - Add any other needed imports (CHAPTERS_DIR if the script uses it)
   - Remove the now-redundant BASE_DIR, WRITER_MODEL, API_KEY, API_BASE local definitions

3. **Append to system prompt**: In the `call_*` function's payload dict, change the `"system"` value from a plain string to a concatenation with `+ language_instruction()`. Example:
   ```python
   "system": (
       "You are a fantasy worldbuilder..."
       + language_instruction()
   ),
   ```

4. **Preserve special headers**: Some scripts have extra headers like `"anthropic-beta": "context-1m-2025-08-07"` in call_writer. Keep these exactly as-is.

5. **Handle seed.py's different var names**: seed.py uses `ANTHROPIC_API_KEY` and `API_BASE_URL` instead of `API_KEY` and `API_BASE`. After migration, use the config names (`API_KEY`, `API_BASE`) consistently. Also has `ANTHROPIC_BETA` — keep as a local constant.

Do NOT change any user prompts, temperatures, or other payload fields. Only touch imports, config var definitions, and the system prompt string.
  - Files: `gen_world.py`, `gen_characters.py`, `gen_outline.py`, `gen_outline_part2.py`, `draft_chapter.py`, `gen_canon.py`, `gen_revision.py`, `seed.py`
  - Verify: cd /home/converter/code/autonovel/.gsd/worktrees/M001 && for f in gen_world.py gen_characters.py gen_outline.py gen_outline_part2.py draft_chapter.py gen_canon.py gen_revision.py seed.py; do echo "=== $f ===" && grep -c 'from config import' "$f" && grep -c 'language_instruction' "$f" && grep -c 'load_dotenv' "$f"; done

- [x] **T03: Migrate 7 evaluation/judging scripts to config imports + analysis_language_note()** `est:30m`
  Migrate these 7 scripts that EVALUATE/JUDGE novel content to import from config.py and append analysis_language_note() to their system prompts:

- evaluate.py (call_judge, system prompt about literary critic/JSON)
- review.py (call_opus, NO system prompt currently — needs one added)
- reader_panel.py (call_reader, 4 reader personas each with own system prompt in READERS dict)
- compare_chapters.py (call_judge, system prompt about literary editor comparing chapters)
- adversarial_edit.py (call_judge, system prompt about ruthless editor)
- build_outline.py (call_model, system prompt about structured outline entries)
- build_arc_summary.py (call_writer, system prompt about chapter summarizer)

For EACH script, make these exact changes:

1. **Replace imports**: Same pattern as T02 — remove dotenv/load_dotenv, remove os if no longer needed, import from config instead.

2. **Replace config vars**: Replace manual os.environ.get with config imports. Scripts use different models:
   - evaluate.py: JUDGE_MODEL (uses JUDGE_MODEL + ANTHROPIC_BETA header)
   - review.py: REVIEW_MODEL
   - reader_panel.py: JUDGE_MODEL
   - compare_chapters.py: JUDGE_MODEL
   - adversarial_edit.py: JUDGE_MODEL
   - build_outline.py: JUDGE_MODEL
   - build_arc_summary.py: WRITER_MODEL
   Import the appropriate model constant from config.

3. **Append analysis_language_note() to system prompt**: Same concatenation pattern as T02 but using `analysis_language_note()` instead of `language_instruction()`.

4. **Special: review.py** — This script has NO system prompt in call_opus. The payload has only `"messages"` and no `"system"` key. Add a `"system"` key to the payload:
   ```python
   "system": (
       "You are a literary reviewer providing dual-perspective manuscript analysis."
       + analysis_language_note()
   ),
   ```

5. **Special: reader_panel.py** — This script has 4 reader personas in the READERS dict, each with their own `"system"` string. Append `analysis_language_note()` to EACH reader's system prompt:
   ```python
   READERS = {
       "editor": {
           "name": "The Editor",
           "system": (
               "You are a senior fiction editor..."
               + analysis_language_note()
           ),
       },
       # ... same for genre_reader, writer, first_reader
   }
   ```
   Also append to the call_reader function's system usage if needed.

6. **Special: evaluate.py** — This script uses `ANTHROPIC_API_KEY` and `API_BASE_URL` (different names). After migration, use config names. Keep the local ANTHROPIC_BETA constant. Also, the env loading in evaluate.py uses a different pattern (`from dotenv import load_dotenv` at line 23, not top-level). Replace it the same way.

Do NOT change any user prompts, temperatures, JSON schemas, or other payload fields.
  - Files: `evaluate.py`, `review.py`, `reader_panel.py`, `compare_chapters.py`, `adversarial_edit.py`, `build_outline.py`, `build_arc_summary.py`
  - Verify: cd /home/converter/code/autonovel/.gsd/worktrees/M001 && for f in evaluate.py review.py reader_panel.py compare_chapters.py adversarial_edit.py build_outline.py build_arc_summary.py; do echo "=== $f ===" && grep -c 'from config import' "$f" && grep -c 'analysis_language_note' "$f" && grep -c 'load_dotenv' "$f"; done

## Files Likely Touched

- config.py
- test_config.py
- gen_world.py
- gen_characters.py
- gen_outline.py
- gen_outline_part2.py
- draft_chapter.py
- gen_canon.py
- gen_revision.py
- seed.py
- evaluate.py
- review.py
- reader_panel.py
- compare_chapters.py
- adversarial_edit.py
- build_outline.py
- build_arc_summary.py
