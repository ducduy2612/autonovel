---
estimated_steps: 1
estimated_files: 4
skills_used: []
---

# T01: Add language field to state.json and make epub_metadata.yaml dynamic

Add a "language" field to default_state() in run_pipeline.py that reads get_language() from config.py. Create a helper function that reads epub_metadata.yaml and patches the lang field based on get_language() before export. Wire the helper into build_tex.py (the only script that currently touches the typeset/ directory). Write tests covering: (1) default_state includes language='en', (2) default_state with AUTONOVEL_LANGUAGE=vi includes language='vi', (3) epub metadata helper patches lang correctly for both en and vi.

## Inputs

- ``run_pipeline.py` — add language field to default_state()`
- ``typeset/build_tex.py` — add epub metadata update and config import`
- ``typeset/epub_metadata.yaml` — existing static template to be patched dynamically`
- ``config.py` — provides get_language() (no changes needed)`

## Expected Output

- ``run_pipeline.py` — modified with language field in default_state()`
- ``typeset/build_tex.py` — modified with epub metadata helper and config import`
- ``test_s04_export.py` — new test file covering state language and metadata generation`

## Verification

uv run pytest test_s04_export.py test_config.py -v
