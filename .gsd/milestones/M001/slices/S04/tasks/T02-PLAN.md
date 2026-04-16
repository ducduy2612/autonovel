---
estimated_steps: 1
estimated_files: 2
skills_used: []
---

# T02: Add conditional Vietnamese babel support to LaTeX template generation

Update build_tex.py to inject \usepackage[vietnamese]{babel} into the generated chapters_content.tex header when get_language() returns 'vi'. EB Garamond already supports Vietnamese glyphs natively — only babel is needed for proper hyphenation and localization. Also update build_tex.py to use config.py constants (BASE_DIR, CHAPTERS_DIR) instead of hardcoded paths.

## Inputs

- ``typeset/build_tex.py` — modified in T01, further updated for LaTeX babel injection`
- ``config.py` — provides get_language(), BASE_DIR, CHAPTERS_DIR`

## Expected Output

- ``typeset/build_tex.py` — final version with config imports, dynamic paths, babel injection`
- ``test_s04_export.py` — updated with babel injection tests`

## Verification

uv run pytest test_s04_export.py -v
