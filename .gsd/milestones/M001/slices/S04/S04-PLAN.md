# S04: Export and metadata language support

**Goal:** Export and metadata outputs reflect the configured language: epub_metadata.yaml shows lang: vi when language=vi, lang: en otherwise. LaTeX template renders Vietnamese diacritics correctly with EB Garamond and conditional babel support. state.json includes a language field propagated on load/save.
**Demo:** epub_metadata.yaml shows lang: vi when language=vi, lang: en otherwise. LaTeX template verified to render Vietnamese diacritics with EB Garamond. state.json includes language field.

## Must-Haves

- default_state() returns a dict containing "language" key with value from get_language()
- epub_metadata.yaml shows lang: vi when AUTONOVEL_LANGUAGE=vi, lang: en otherwise
- build_tex.py injects \usepackage[vietnamese]{babel} when language is vi
- All existing tests still pass
- New tests cover state.json language field, epub metadata generation, and LaTeX babel injection

## Proof Level

- This slice proves: contract

## Integration Closure

Upstream surfaces consumed: config.py get_language(), config.py BASE_DIR/CHAPTERS_DIR constants. New wiring: run_pipeline.py reads get_language() for state initialization; build_tex.py reads get_language() and conditionally patches YAML + injects LaTeX babel headers. What remains: S05 validates end-to-end pipeline with language=vi.

## Verification

- none

## Tasks

- [x] **T01: Add language field to state.json and make epub_metadata.yaml dynamic** `est:30m`
  Add a "language" field to default_state() in run_pipeline.py that reads get_language() from config.py. Create a helper function that reads epub_metadata.yaml and patches the lang field based on get_language() before export. Wire the helper into build_tex.py (the only script that currently touches the typeset/ directory). Write tests covering: (1) default_state includes language='en', (2) default_state with AUTONOVEL_LANGUAGE=vi includes language='vi', (3) epub metadata helper patches lang correctly for both en and vi.
  - Files: `run_pipeline.py`, `typeset/build_tex.py`, `typeset/epub_metadata.yaml`, `test_s04_export.py`
  - Verify: uv run pytest test_s04_export.py test_config.py -v

- [x] **T02: Add conditional Vietnamese babel support to LaTeX template generation** `est:20m`
  Update build_tex.py to inject \usepackage[vietnamese]{babel} into the generated chapters_content.tex header when get_language() returns 'vi'. EB Garamond already supports Vietnamese glyphs natively — only babel is needed for proper hyphenation and localization. Also update build_tex.py to use config.py constants (BASE_DIR, CHAPTERS_DIR) instead of hardcoded paths.
  - Files: `typeset/build_tex.py`, `test_s04_export.py`
  - Verify: uv run pytest test_s04_export.py -v

## Files Likely Touched

- run_pipeline.py
- typeset/build_tex.py
- typeset/epub_metadata.yaml
- test_s04_export.py
