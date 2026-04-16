# S05: End-to-end Vietnamese pipeline verification — UAT

**Milestone:** M001
**Written:** 2026-04-16T17:26:35.973Z

# S05: End-to-end Vietnamese pipeline verification — UAT

**Milestone:** M001
**Written:** 2026-04-16

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: The slice's primary deliverable is an integration test suite that proves wiring correctness with mocked API calls. Live verification script is provided for operational use with a real API key.

## Preconditions

- uv installed and available in PATH
- No ANTHROPIC_API_KEY required for integration tests (all API calls mocked)

## Smoke Test

```bash
uv run pytest test_s05_e2e.py -v
```
Expected: 43 passed, 0 failed.

## Test Cases

### 1. Pipeline file-writing correctness

1. Run `uv run pytest test_s05_e2e.py::TestPipelineFileWriting -v`
2. **Expected:** 7 tests pass — world.md, characters.md, outline.md, canon.md written correctly; outline_part2 appended; failed/empty scripts don't overwrite good output.

### 2. Vietnamese language instruction in foundation script API payloads

1. Run `uv run pytest test_s05_e2e.py::TestLanguageInstructionWiring -v`
2. **Expected:** 10 tests pass — each of the 5 foundation scripts includes Vietnamese creative-writing instruction when AUTONOVEL_LANGUAGE=vi and excludes it when AUTONOVEL_LANGUAGE=en.

### 3. Vietnamese text detection

1. Run `uv run pytest test_s05_e2e.py::TestVietnameseDetection -v`
2. **Expected:** 12 tests pass — detects each Vietnamese diacritical char (ă, â, đ, ê, ô, ơ, ư), rejects English-only text, handles edge cases.

### 4. Evaluation adaptation for Vietnamese

1. Run `uv run pytest test_s05_e2e.py::TestEvaluationAdaptation -v`
2. **Expected:** 6 tests pass — slop_score returns empty English patterns for vi, cross-checks return Vietnamese variants for vi.

### 5. State language field

1. Run `uv run pytest test_s05_e2e.py::TestStateLanguageField -v`
2. **Expected:** 3 tests pass — default_state() returns language='vi' when env=vi, 'en' when env=en, always includes language key.

### 6. Full end-to-end Vietnamese foundation chain

1. Run `uv run pytest test_s05_e2e.py::TestEndToEndVietnameseFoundationChain -v`
2. **Expected:** 2 tests pass — full chain with mocked API produces Vietnamese output in all files; English chain produces no Vietnamese chars.

### 7. Execution logging

1. Run `uv run pytest test_s05_e2e.py::TestScriptExecutionLogging -v`
2. **Expected:** 2 tests pass — step logging captures script names, file size logging records path and char count.

### 8. No regressions in pre-existing tests

1. Run `uv run pytest test_config.py test_evaluate.py test_s04_export.py test_s05_e2e.py -v`
2. **Expected:** 96 passed, 0 failed.

### 9. Vietnamese seed file validity

1. Run `python3 -c "t=open('seed_vi.txt').read(); assert len(t) > 200; assert any(c in t for c in 'ăâđêôơư')"`
2. **Expected:** No assertion error — seed file is non-empty and contains Vietnamese characters.

### 10. Verification script validity

1. Run `bash -n scripts/verify_vi_pipeline.sh`
2. Run `grep -q 'AUTONOVEL_LANGUAGE=vi' scripts/verify_vi_pipeline.sh`
3. **Expected:** Both commands succeed (valid syntax, contains language setting).

## Edge Cases

### Failed script doesn't corrupt prior output

1. Verify with TestPipelineFileWriting::test_failed_script_does_not_overwrite — a script returning non-zero exit code leaves prior .md files intact.

### Empty stdout doesn't create empty files

1. Verify with TestPipelineFileWriting::test_empty_stdout_does_not_overwrite — a script returning empty stdout doesn't overwrite.

### Language change mid-pipeline doesn't affect state

1. state.json language field is set once by default_state() and preserved by run_foundation() — changing env var mid-run doesn't retroactively change it.

## Failure Signals

- Any of the 96 tests failing
- Missing seed_vi.txt or scripts/verify_vi_pipeline.sh
- run_pipeline.py missing write_text calls for foundation files

## Not Proven By This UAT

- Live LLM output quality — tests mock API responses; real Vietnamese quality depends on Claude's Vietnamese generation capability
- Drafting/revision/export phases beyond foundation — only foundation phase is covered
- Performance under real API latency and error conditions

## Notes for Tester

- The live verification script (scripts/verify_vi_pipeline.sh) requires ANTHROPIC_API_KEY and makes ~5-6 real API calls (~$0.05-$0.10 estimated cost). It is NOT required for this UAT — the integration test suite is the primary proof.
- The seed_vi.txt concept uses a Vietnamese fragrance-magic theme — this is intentional to elicit culturally-specific Vietnamese output rather than translated English.
