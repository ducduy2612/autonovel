---
id: T01
parent: S05
milestone: M001
key_files:
  - run_pipeline.py
key_decisions:
  - Write gen_outline.py output to both outline.md and /tmp/outline_output.md because gen_outline_part2.py hardcodes a read from /tmp
  - Guard each file write with returncode==0 and stdout.strip() to avoid overwriting good prior output with failures
duration: 
verification_result: passed
completed_at: 2026-04-16T17:14:38.920Z
blocker_discovered: false
---

# T01: Fix run_foundation() to save each foundation script's stdout to the corresponding .md file

**Fix run_foundation() to save each foundation script's stdout to the corresponding .md file**

## What Happened

The pipeline orchestrator's `run_foundation()` called each foundation script via `uv_run()` which captures stdout, but never wrote the captured output to the corresponding `.md` files. This meant the entire foundation phase silently discarded all LLM-generated content.

Fixed by capturing each `uv_run()` result and writing its stdout to the correct file:
- `gen_world.py` → `world.md` (write)
- `gen_characters.py` → `characters.md` (write)
- `gen_outline.py` → `outline.md` (write) + `/tmp/outline_output.md` (needed by gen_outline_part2.py)
- `gen_outline_part2.py` → appended to `outline.md`
- `gen_canon.py` → `canon.md` (write)

Each write is guarded by a check for success (`returncode == 0 and stdout.strip()`) and includes logging (path + char count) for diagnosis. Failed generations produce a warning but don't overwrite previous good output. The `/tmp/outline_output.md` write was necessary because `gen_outline_part2.py` hardcodes a read from that path.

## Verification

Verified with:
1. `grep -q 'write_text' run_pipeline.py && grep -q 'world.md' run_pipeline.py` — confirmed file-writing code present
2. `uv run python -c "import py_compile; py_compile.compile('run_pipeline.py', doraise=True)"` — syntax check passed
3. Manual review of the edited section confirmed correct write/append logic, proper guard conditions, and diagnostic logging

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `grep -q 'write_text' run_pipeline.py && grep -q 'world.md' run_pipeline.py` | 0 | ✅ pass | 200ms |
| 2 | `uv run python -c "import py_compile; py_compile.compile('run_pipeline.py', doraise=True)"` | 0 | ✅ pass | 2500ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `run_pipeline.py`
