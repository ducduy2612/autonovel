---
estimated_steps: 43
estimated_files: 7
skills_used: []
---

# T03: Migrate 7 evaluation/judging scripts to config imports + analysis_language_note()

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

## Inputs

- `config.py`
- `evaluate.py`
- `review.py`
- `reader_panel.py`
- `compare_chapters.py`
- `adversarial_edit.py`
- `build_outline.py`
- `build_arc_summary.py`

## Expected Output

- `evaluate.py`
- `review.py`
- `reader_panel.py`
- `compare_chapters.py`
- `adversarial_edit.py`
- `build_outline.py`
- `build_arc_summary.py`

## Verification

cd /home/converter/code/autonovel/.gsd/worktrees/M001 && for f in evaluate.py review.py reader_panel.py compare_chapters.py adversarial_edit.py build_outline.py build_arc_summary.py; do echo "=== $f ===" && grep -c 'from config import' "$f" && grep -c 'analysis_language_note' "$f" && grep -c 'load_dotenv' "$f"; done
