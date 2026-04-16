# S02: Vietnamese prompts in all LLM-calling scripts — UAT

**Milestone:** M001
**Written:** 2026-04-16T16:33:53.098Z

# S02: Vietnamese prompts in all LLM-calling scripts — UAT

**Milestone:** M001
**Written:** 2026-04-16

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: This slice adds prompt-wiring logic, not runtime behavior. Verification is that the correct strings are appended in the correct places, proven by unit tests and grep checks.

## Preconditions

- Working directory: `/home/converter/code/autonovel/.gsd/worktrees/M001`
- Python environment with uv installed
- `.env` file present with valid `ANTHROPIC_API_KEY`

## Smoke Test

```bash
uv run pytest test_config.py::TestLanguageInstruction -v
```
Expected: 7 tests pass.

## Test Cases

### 1. language_instruction() returns correct strings

1. Set `AUTONOVEL_LANGUAGE=en` (or leave unset)
2. Run: `uv run python -c "from config import language_instruction; assert language_instruction() == ''"`
3. **Expected:** Pass — empty string for English

1. Set `AUTONOVEL_LANGUAGE=vi`
2. Run: `uv run python -c "from config import language_instruction; result = language_instruction(); assert result != '' and 'Vietnamese' in result"`
3. **Expected:** Pass — non-empty string containing "Vietnamese"

### 2. analysis_language_note() returns correct strings

1. Set `AUTONOVEL_LANGUAGE=en`
2. Run: `uv run python -c "from config import analysis_language_note; assert analysis_language_note() == ''"`
3. **Expected:** Pass — empty string for English

1. Set `AUTONOVEL_LANGUAGE=vi`
2. Run: `uv run python -c "from config import analysis_language_note; result = analysis_language_note(); assert result != '' and 'Vietnamese' in result"`
3. **Expected:** Pass — non-empty string containing "Vietnamese"

### 3. All 8 content scripts have language_instruction() wired

1. Run: `for f in gen_world.py gen_characters.py gen_outline.py gen_outline_part2.py draft_chapter.py gen_canon.py gen_revision.py seed.py; do grep -q 'language_instruction()' "$f" && echo "$f: OK" || echo "$f: MISSING"; done`
2. **Expected:** All 8 files show "OK"

### 4. All 7 evaluation scripts have analysis_language_note() wired

1. Run: `for f in evaluate.py review.py reader_panel.py compare_chapters.py adversarial_edit.py build_outline.py build_arc_summary.py; do grep -q 'analysis_language_note()' "$f" && echo "$f: OK" || echo "$f: MISSING"; done`
2. **Expected:** All 7 files show "OK"

### 5. No scripts still use load_dotenv

1. Run: `grep -rl 'load_dotenv' *.py | grep -v config.py || echo "CLEAN"`
2. **Expected:** "CLEAN" — no scripts except config.py reference load_dotenv

### 6. All scripts compile without error

1. Run: `for f in gen_world.py gen_characters.py gen_outline.py gen_outline_part2.py draft_chapter.py gen_canon.py gen_revision.py seed.py evaluate.py review.py reader_panel.py compare_chapters.py adversarial_edit.py build_outline.py build_arc_summary.py; do python3 -m py_compile "$f" && echo "$f: OK" || echo "$f: FAIL"; done`
2. **Expected:** All 15 files show "OK"

### 7. reader_panel.py has language note in all 4 personas

1. Run: `grep -c 'analysis_language_note()' reader_panel.py`
2. **Expected:** 4 (one per reader persona: editor, genre_reader, writer, first_reader) — plus the import makes 5 total grep matches

## Edge Cases

### review.py had no system prompt before

1. Check that review.py now has a `"system"` key in call_opus: `grep -A2 '"system"' review.py | grep analysis_language_note`
2. **Expected:** Match found — system prompt was added with language note

## Failure Signals

- Any test in TestLanguageInstruction fails
- Any script still has `load_dotenv` import
- Any script missing the appropriate language helper call
- Syntax errors in any migrated script

## Not Proven By This UAT

- End-to-end Vietnamese output from actual LLM calls (deferred to S05)
- That LLM actually follows the Vietnamese instruction (runtime behavior, not wiring)
- Evaluation regex adaptation for Vietnamese (deferred to S03)

## Notes for Tester

- reader_panel.py showing 5 `analysis_language_note` matches is correct: 1 import + 4 persona system prompts.
- review.py gaining a system prompt is intentional — it previously had none, so a minimal one was added alongside the language note.
- All tests run with `uv run` — do not call `pytest` directly as it may not be on PATH.
