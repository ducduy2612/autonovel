# S05: End-to-end Vietnamese pipeline verification

**Goal:** Validate that all prior slices (S02–S04) work together when AUTONOVEL_LANGUAGE=vi: the foundation phase produces Vietnamese world bible, characters, outline, canon, and honest evaluation scores from a Vietnamese seed concept.
**Demo:** Full foundation loop with AUTONOVEL_LANGUAGE=vi and a Vietnamese seed produces: Vietnamese world bible, Vietnamese characters, Vietnamese outline, Vietnamese voice discovery, honest evaluation scores.

## Must-Haves

- run_pipeline.py correctly saves each foundation script's stdout to the corresponding .md file (world.md, characters.md, outline.md, canon.md)
- Integration test with mocked API confirms every foundation script sends Vietnamese language_instruction() in its system prompt
- Integration test confirms evaluate.py --phase=foundation uses Vietnamese-aware evaluation (skips English regex, uses VI cross-checks)
- Integration test confirms run_pipeline.py --phase foundation writes Vietnamese content to all planning doc files when AUTONOVEL_LANGUAGE=vi
- Vietnamese seed.txt exists with authentic Vietnamese content
- Live verification procedure documented and verification script created
- All existing tests continue to pass (no regressions)

## Proof Level

- This slice proves: integration — proves all prior slices compose correctly at runtime with mocked API; live run provides operational proof

## Integration Closure

Upstream surfaces consumed: config.py (get_language, language_instruction, analysis_language_note), evaluate.py (slop_score, _get_cross_checks, evaluate_foundation), run_pipeline.py (run_foundation, default_state), all 5 foundation gen scripts (gen_world, gen_characters, gen_outline, gen_outline_part2, gen_canon), typeset/build_tex.py (patch_epub_metadata, generate_latex_header). New wiring: run_pipeline.py now redirects foundation stdout to .md files, completing the orchestration loop. What remains: live run with real API key confirms LLM produces actual Vietnamese text.

## Verification

- Integration test logs which script is being tested and whether Vietnamese language instruction was found in the API payload. run_pipeline.py step() calls already log each foundation script execution. New file-writing step will log the output file path and size for diagnosis.

## Tasks

- [x] **T01: Fix run_pipeline.py to save foundation script output to files** `est:30m`
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
  - Files: `run_pipeline.py`
  - Verify: uv run pytest test_s05_e2e.py -v -k 'test_pipeline_saves' 2>/dev/null || echo 'T02 tests not yet created'; grep -q 'write_text' run_pipeline.py && grep -q 'world.md' run_pipeline.py && echo 'File writing code present'

- [x] **T02: Create integration test with mocked API for full Vietnamese foundation chain** `est:1h`
  Create `test_s05_e2e.py` with comprehensive integration tests that verify the entire Vietnamese foundation pipeline works without making real API calls. This is the primary deliverable proving wiring correctness.

Test categories:

1. **Pipeline file-writing tests** (validates T01 fix):
   - Test that `run_foundation()` with mocked uv_run results writes stdout to world.md, characters.md, outline.md, canon.md
   - Test that gen_outline_part2.py output is appended (not overwritten) to outline.md
   - Test that voice_fingerprint.py is called but doesn't write any planning doc file

2. **Language instruction wiring tests** (validates S02):
   - For each of the 5 foundation scripts (gen_world, gen_characters, gen_outline, gen_outline_part2, gen_canon), mock httpx.post to capture the API payload
   - Assert the system prompt contains the Vietnamese creative-writing instruction when AUTONOVEL_LANGUAGE=vi
   - Assert the system prompt does NOT contain the Vietnamese instruction when AUTONOVEL_LANGUAGE=en

3. **Vietnamese text detection tests**:
   - Test helper `contains_vietnamese()` detects ă, â, đ, ê, ô, ơ, ư in text
   - Test it returns False for English-only text

4. **Evaluation adaptation tests** (validates S03 in context):
   - Test that slop_score() with AUTONOVEL_LANGUAGE=vi returns empty English pattern lists
   - Test that _get_cross_checks('FOUNDATION') returns Vietnamese cross-checks when lang=vi

5. **State language field test** (validates S04 in context):
   - Test that default_state() with AUTONOVEL_LANGUAGE=vi returns language='vi'

6. **End-to-end chain test** (the main integration test):
   - Mock httpx.post to return fake Vietnamese content for each script
   - Call run_foundation() with AUTONOVEL_LANGUAGE=vi
   - Verify all output files exist, are non-empty, and contain Vietnamese characters
   - Verify state.json has language='vi'

Approach:
- Use unittest.mock.patch to mock httpx.post in each script's call_writer function
- Use monkeypatch or os.environ to set AUTONOVEL_LANGUAGE=vi
- Use tmp_path fixture for file output to avoid polluting the repo
- Import scripts directly and call their functions where possible
- For the full chain test, mock subprocess.run instead of individual script functions

Constraints:
- No real API calls — all httpx interactions mocked
- Tests must pass without ANTHROPIC_API_KEY
- Existing 53 tests must continue to pass
  - Files: `test_s05_e2e.py`, `run_pipeline.py`, `config.py`, `evaluate.py`, `gen_world.py`, `gen_characters.py`, `gen_outline.py`, `gen_outline_part2.py`, `gen_canon.py`
  - Verify: uv run pytest test_s05_e2e.py -v

- [x] **T03: Prepare Vietnamese seed and live verification script** `est:30m`
  Prepare the Vietnamese seed concept and create a verification script for the live foundation run.

1. **Create `seed_vi.txt`** — an authentic Vietnamese fantasy novel seed concept. Write it as natural Vietnamese (not machine-translated English). The seed should describe a compelling fantasy world with:
   - A unique magic system concept
   - A protagonist with internal conflict
   - A central tension/mystery
   - Cultural elements that feel Vietnamese-inspired
   Keep it to ~300-500 words. This file is a reference — users copy it to seed.txt when running the Vietnamese pipeline.

2. **Create `scripts/verify_vi_pipeline.sh`** — a shell script that:
   - Sets AUTONOVEL_LANGUAGE=vi in environment
   - Creates seed.txt from seed_vi.txt if it doesn't exist
   - Runs `uv run python run_pipeline.py --from-scratch --phase foundation`
   - After completion, checks:
     - world.md exists and contains Vietnamese characters (ă, â, đ, ê, ô, ơ, ư)
     - characters.md exists and contains Vietnamese characters
     - outline.md exists and contains Vietnamese characters
     - canon.md exists and contains Vietnamese characters
     - state.json contains `"language": "vi"`
   - Reports pass/fail for each check
   - Requires ANTHROPIC_API_KEY in environment (fails gracefully if missing)

3. **Document the live verification procedure** in a comment block at the top of the verification script, explaining:
   - Prerequisites (ANTHROPIC_API_KEY, uv installed)
   - How to run the verification
   - What constitutes success
   - Expected cost (5-6 API calls to Claude)
   - How to interpret the output

Constraints:
- seed_vi.txt must be natural Vietnamese prose, not machine-translated
- The verification script must be self-contained (no external dependencies beyond uv and the pipeline)
- The script should not require manual intervention — fully automated
  - Files: `seed_vi.txt`, `scripts/verify_vi_pipeline.sh`
  - Verify: test -f seed_vi.txt && test -f scripts/verify_vi_pipeline.sh && grep -q 'AUTONOVEL_LANGUAGE=vi' scripts/verify_vi_pipeline.sh && python3 -c "t=open('seed_vi.txt').read(); assert any(c in t for c in 'ăâđêôơư'), 'No Vietnamese chars in seed'"

## Files Likely Touched

- run_pipeline.py
- test_s05_e2e.py
- config.py
- evaluate.py
- gen_world.py
- gen_characters.py
- gen_outline.py
- gen_outline_part2.py
- gen_canon.py
- seed_vi.txt
- scripts/verify_vi_pipeline.sh
