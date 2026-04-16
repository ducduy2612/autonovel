---
id: T03
parent: S02
milestone: M001
key_files:
  - evaluate.py
  - review.py
  - reader_panel.py
  - compare_chapters.py
  - adversarial_edit.py
  - build_outline.py
  - build_arc_summary.py
key_decisions:
  - (none)
duration: 
verification_result: passed
completed_at: 2026-04-16T16:31:41.379Z
blocker_discovered: false
---

# T03: Migrate 7 evaluation/judging scripts to config imports and append analysis_language_note() to system prompts

**Migrate 7 evaluation/judging scripts to config imports and append analysis_language_note() to system prompts**

## What Happened

Migrated all 7 evaluation/judging scripts to use centralized config imports and appended `analysis_language_note()` to their system prompts. For each script:

1. **evaluate.py**: Replaced dotenv/load_dotenv and os.environ.get with config imports (API_KEY aliased as ANTHROPIC_API_KEY, API_BASE as API_BASE_URL, JUDGE_MODEL, CHAPTERS_DIR). Removed redundant CHAPTERS_DIR local definition. Appended `analysis_language_note()` to the literary critic system prompt in `call_judge`.

2. **review.py**: Replaced dotenv/load_dotenv and os.environ.get with config imports (API_KEY, API_BASE, REVIEW_MODEL). Added a new `"system"` key to the `call_opus` payload (previously had no system prompt) with "You are a literary reviewer providing dual-perspective manuscript analysis." + analysis_language_note().

3. **reader_panel.py**: Replaced dotenv/load_dotenv and os.environ.get with config imports (API_KEY, API_BASE, JUDGE_MODEL). Appended `analysis_language_note()` to all 4 reader persona system prompts in the READERS dict (editor, genre_reader, writer, first_reader).

4. **compare_chapters.py**: Replaced dotenv/load_dotenv and os.environ.get with config imports (API_KEY, API_BASE, JUDGE_MODEL, CHAPTERS_DIR). Appended `analysis_language_note()` to the literary editor system prompt in `call_judge`.

5. **adversarial_edit.py**: Replaced dotenv/load_dotenv and os.environ.get with config imports (API_KEY, API_BASE, JUDGE_MODEL, CHAPTERS_DIR). Appended `analysis_language_note()` to the ruthless editor system prompt in `call_judge`.

6. **build_outline.py**: Replaced dotenv/load_dotenv and os.environ.get with config imports (API_KEY, API_BASE, JUDGE_MODEL, CHAPTERS_DIR). Appended `analysis_language_note()` to the structured outline system prompt in `call_model`.

7. **build_arc_summary.py**: Replaced dotenv/load_dotenv and os.environ.get with config imports (API_KEY, API_BASE, WRITER_MODEL, CHAPTERS_DIR). Appended `analysis_language_note()` to the chapter summarizer system prompt in `call_writer`.

All files compile cleanly with py_compile. No remaining load_dotenv or os.environ.get references in any of the 7 scripts.

## Verification

Ran grep-based verification for all 7 files: each has exactly 1 `from config import` line, correct count of `analysis_language_note()` references (2 for most scripts, 5 for reader_panel.py which has 4 reader personas + the import), and 0 remaining `load_dotenv` references. All 7 files pass `python3 -m py_compile`. Config imports verified working at runtime — `analysis_language_note()` returns empty string when language is 'en' (default) and returns the Vietnamese preservation note when AUTONOVEL_LANGUAGE=vi.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `for f in evaluate.py review.py reader_panel.py compare_chapters.py adversarial_edit.py build_outline.py build_arc_summary.py; do echo "=== $f ===" && grep -c 'from config import' "$f" && grep -c 'analysis_language_note' "$f" && grep -c 'load_dotenv' "$f"; done` | 0 | ✅ pass | 500ms |
| 2 | `grep -n 'load_dotenv\|from dotenv' evaluate.py review.py reader_panel.py compare_chapters.py adversarial_edit.py build_outline.py build_arc_summary.py` | 0 | ✅ pass | 200ms |
| 3 | `grep -n 'os.environ.get' evaluate.py review.py reader_panel.py compare_chapters.py adversarial_edit.py build_outline.py build_arc_summary.py` | 0 | ✅ pass | 200ms |
| 4 | `python3 -m py_compile evaluate.py && python3 -m py_compile review.py && python3 -m py_compile reader_panel.py && python3 -m py_compile compare_chapters.py && python3 -m py_compile adversarial_edit.py && python3 -m py_compile build_outline.py && python3 -m py_compile build_arc_summary.py` | 0 | ✅ pass | 1000ms |
| 5 | `python3 -c "from config import analysis_language_note, language_instruction, JUDGE_MODEL, REVIEW_MODEL, WRITER_MODEL, API_KEY, API_BASE, CHAPTERS_DIR; print('All config imports OK')"` | 0 | ✅ pass | 300ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `evaluate.py`
- `review.py`
- `reader_panel.py`
- `compare_chapters.py`
- `adversarial_edit.py`
- `build_outline.py`
- `build_arc_summary.py`
