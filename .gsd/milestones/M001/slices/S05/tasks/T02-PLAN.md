---
estimated_steps: 33
estimated_files: 9
skills_used: []
---

# T02: Create integration test with mocked API for full Vietnamese foundation chain

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

## Inputs

- `run_pipeline.py`
- `config.py`
- `evaluate.py`
- `gen_world.py`
- `gen_characters.py`
- `gen_outline.py`
- `gen_outline_part2.py`
- `gen_canon.py`
- `test_config.py`
- `test_evaluate.py`

## Expected Output

- `test_s05_e2e.py`

## Verification

uv run pytest test_s05_e2e.py -v
