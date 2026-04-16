---
estimated_steps: 25
estimated_files: 8
skills_used: []
---

# T02: Migrate 8 content-generating scripts to config imports + language_instruction()

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

## Inputs

- `config.py`
- `gen_world.py`
- `gen_characters.py`
- `gen_outline.py`
- `gen_outline_part2.py`
- `draft_chapter.py`
- `gen_canon.py`
- `gen_revision.py`
- `seed.py`

## Expected Output

- `gen_world.py`
- `gen_characters.py`
- `gen_outline.py`
- `gen_outline_part2.py`
- `draft_chapter.py`
- `gen_canon.py`
- `gen_revision.py`
- `seed.py`

## Verification

cd /home/converter/code/autonovel/.gsd/worktrees/M001 && for f in gen_world.py gen_characters.py gen_outline.py gen_outline_part2.py draft_chapter.py gen_canon.py gen_revision.py seed.py; do echo "=== $f ===" && grep -c 'from config import' "$f" && grep -c 'language_instruction' "$f" && grep -c 'load_dotenv' "$f"; done
