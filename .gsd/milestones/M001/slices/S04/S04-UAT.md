# S04: Export and metadata language support — UAT

**Milestone:** M001
**Written:** 2026-04-16T17:04:46.965Z

# S04: Export and metadata language support — UAT

**Milestone:** M001
**Written:** 2026-04-16

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: All deliverables are code outputs (YAML patching, LaTeX header generation, state dict construction) verifiable via automated tests and file inspection. No live server or runtime needed.

## Preconditions

- Working directory is the autonovel project root
- Python environment available via `uv`
- No chapter files need to exist for these tests (build_tex.py main() is guarded)

## Smoke Test

Run `uv run pytest test_s04_export.py -v` — all 15 tests pass.

## Test Cases

### 1. state.json includes language field (English default)

1. Call `default_state()` from `run_pipeline.py` with `AUTONOVEL_LANGUAGE` unset
2. **Expected:** Result dict contains `"language": "en"`

### 2. state.json includes language field (Vietnamese)

1. Set `AUTONOVEL_LANGUAGE=vi`
2. Call `default_state()` from `run_pipeline.py`
3. **Expected:** Result dict contains `"language": "vi"`

### 3. epub_metadata.yaml patched to lang: vi

1. Create a temp `epub_metadata.yaml` with `lang: en`
2. Call `patch_epub_metadata(path, lang='vi')`
3. **Expected:** File now contains `lang: vi`, all other fields preserved

### 4. epub_metadata.yaml patched to lang: en

1. Create a temp `epub_metadata.yaml` with `lang: vi`
2. Call `patch_epub_metadata(path, lang='en')`
3. **Expected:** File now contains `lang: en`, all other fields preserved

### 5. LaTeX header for Vietnamese includes babel

1. Call `generate_latex_header(lang='vi')`
2. **Expected:** Output contains `\usepackage[vietnamese]{babel}`

### 6. LaTeX header for English has no babel

1. Call `generate_latex_header(lang='en')`
2. **Expected:** Output does NOT contain `babel`

### 7. LaTeX header includes auto-generated comment

1. Call `generate_latex_header(lang='en')`
2. **Expected:** Output starts with a comment indicating it is auto-generated

### 8. epub metadata patch skips write when lang already matches

1. Create a temp `epub_metadata.yaml` with `lang: vi`
2. Call `patch_epub_metadata(path, lang='vi')`
3. **Expected:** File modification time is unchanged (no-op write)

## Edge Cases

### Missing epub_metadata.yaml

1. Call `patch_epub_metadata('/nonexistent/path.yaml', lang='vi')`
2. **Expected:** No error raised, function returns gracefully

### Missing file handling

1. Verify test `test_missing_file_does_not_error` passes
2. **Expected:** No exception when target file doesn't exist

## Failure Signals

- `uv run pytest test_s04_export.py` returns non-zero exit code
- epub_metadata.yaml contains wrong lang value after patching
- LaTeX header missing babel when language=vi
- state.json missing language field

## Not Proven By This UAT

- End-to-end pipeline execution with Vietnamese (that's S05)
- Actual LaTeX compilation of Vietnamese text (requires a LaTeX installation)
- Visual verification of Vietnamese diacritics in rendered PDF
