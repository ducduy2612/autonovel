---
id: T02
parent: S02
milestone: M001
key_files:
  - gen_world.py
  - gen_characters.py
  - gen_outline.py
  - gen_outline_part2.py
  - draft_chapter.py
  - gen_canon.py
  - gen_revision.py
  - seed.py
key_decisions:
  - (none)
duration: 
verification_result: passed
completed_at: 2026-04-16T16:27:06.253Z
blocker_discovered: false
---

# T02: Migrate 8 content-generating scripts to use config imports and append language_instruction() to system prompts

**Migrate 8 content-generating scripts to use config imports and append language_instruction() to system prompts**

## What Happened

Migrated all 8 content-generating scripts (gen_world.py, gen_characters.py, gen_outline.py, gen_outline_part2.py, draft_chapter.py, gen_canon.py, gen_revision.py, seed.py) from manual dotenv/os.environ configuration to centralized config imports. For each script:

1. Replaced `from dotenv import load_dotenv` + `load_dotenv()` + `import os` with targeted imports from config.py (API_KEY, API_BASE, WRITER_MODEL, BASE_DIR, language_instruction, and CHAPTERS_DIR where needed).
2. Removed redundant local variable definitions for WRITER_MODEL, API_KEY, API_BASE.
3. Appended `+ language_instruction()` to each script's system prompt string in the call_writer() payload, so when AUTONOVEL_LANGUAGE=vi the LLM receives a Vietnamese creative-writing instruction.

Special handling for seed.py: unified its different variable names (ANTHROPIC_API_KEY→API_KEY, API_BASE_URL→API_BASE) to use config names consistently. Preserved the local ANTHROPIC_BETA constant and kept Path import where scripts use it for file operations (draft_chapter.py, gen_revision.py).

All 26 existing tests continue to pass. All 8 scripts compile cleanly.

## Verification

Ran the task plan verification command: for each of the 8 scripts, confirmed 1 `from config import` line, 2 `language_instruction` references (import + call), and 0 `load_dotenv` references. All 8 scripts pass py_compile syntax checks. All 26 pytest tests pass. No leftover `import os` or `from dotenv` imports remain.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `cd /home/converter/code/autonovel/.gsd/worktrees/M001 && for f in gen_world.py gen_characters.py gen_outline.py gen_outline_part2.py draft_chapter.py gen_canon.py gen_revision.py seed.py; do echo "=== $f ===" && grep -c 'from config import' "$f" && grep -c 'language_instruction' "$f" && grep -c 'load_dotenv' "$f"; done` | 0 | ✅ pass | 500ms |
| 2 | `cd /home/converter/code/autonovel/.gsd/worktrees/M001 && uv run pytest test_config.py -v` | 0 | ✅ pass | 3000ms |
| 3 | `cd /home/converter/code/autonovel/.gsd/worktrees/M001 && for f in gen_world.py gen_characters.py gen_outline.py gen_outline_part2.py draft_chapter.py gen_canon.py gen_revision.py seed.py; do python3 -c "import py_compile; py_compile.compile('$f', doraise=True)"; done` | 0 | ✅ pass | 1000ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `gen_world.py`
- `gen_characters.py`
- `gen_outline.py`
- `gen_outline_part2.py`
- `draft_chapter.py`
- `gen_canon.py`
- `gen_revision.py`
- `seed.py`
