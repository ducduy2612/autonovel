---
estimated_steps: 14
estimated_files: 1
skills_used: []
---

# T01: Fix run_pipeline.py to save foundation script output to files

The pipeline orchestrator runs foundation scripts (gen_world.py, gen_characters.py, gen_outline.py, gen_outline_part2.py, gen_canon.py) via uv_run() which captures stdout, but never writes the captured output to the corresponding .md files. The scripts print to stdout but don't write files themselves (unlike draft_chapter.py which calls write_text). This means the entire foundation phase silently discards LLM output.

Fix run_foundation() to capture each uv_run() result's stdout and write it to the correct file:
- gen_world.py stdout → world.md
- gen_characters.py stdout → characters.md
- gen_outline.py stdout → outline.md (overwrite)
- gen_outline_part2.py stdout → append to outline.md
- gen_canon.py stdout → canon.md

Also add logging for each file written (path + size) so failures are diagnosable.

Constraints:
- Only modify run_foundation() in run_pipeline.py — don't change the individual scripts
- voice_fingerprint.py doesn't write planning docs — skip it (reads from chapters/ which is empty during foundation)
- gen_outline_part2.py output should be APPENDED to outline.md (not overwrite the first part)
- Use the same file-writing pattern as the existing draft chapter flow (Path.write_text / Path.write_text with append)
- Don't change the evaluate.py call — it reads the files on disk and should work once they're populated

## Inputs

- `run_pipeline.py`
- `gen_world.py`
- `gen_characters.py`
- `gen_outline.py`
- `gen_outline_part2.py`
- `gen_canon.py`

## Expected Output

- `run_pipeline.py`

## Verification

uv run pytest test_s05_e2e.py -v -k 'test_pipeline_saves' 2>/dev/null || echo 'T02 tests not yet created'; grep -q 'write_text' run_pipeline.py && grep -q 'world.md' run_pipeline.py && echo 'File writing code present'
