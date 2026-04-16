# S04: Export and metadata language support — Research

**Date:** 2026-04-16

## Summary

The slice requires three discrete changes: (1) add a `language` field to `state.json` and propagate it on load/save, (2) make `typeset/epub_metadata.yaml` reflect the configured language (`lang: vi` when `AUTONOVEL_LANGUAGE=vi`, else `lang: en`), and (3) ensure the LaTeX template (`typeset/novel.tex`) renders Vietnamese diacritics correctly with EB Garamond.

EB Garamond **does support Vietnamese diacritics** — it ships Vietnamese-specific glyph variants and is listed as Vietnamese-compatible on Google Fonts and Font Squirrel. With XeLaTeX/LuaLaTeX and `fontspec`, Vietnamese text will render without additional font configuration. No font fallback chain is needed.

The `build_tex.py` script currently has no language awareness and does not import `config.py`. It also has a hardcoded chapter directory path (`/home/jeffq/autonovel/chapters`). This script needs updating to read `get_language()` and inject appropriate LaTeX directives when language is Vietnamese (e.g., `\usepackage[vietnamese]{babel}` or `\usepackage{polyglossia}` with language setting).

## Recommendation

**Three targeted changes, no architectural shifts:**

1. **state.json** — Add `"language"` field to `default_state()` in `run_pipeline.py`. Persist `get_language()` value at state creation time. The field is read-only for downstream consumers (e.g., export scripts).
2. **epub_metadata.yaml** — The YAML file is currently a static template. Since no Python code currently writes it, we need a small script or a modification to the export phase that reads `get_language()` and sets the `lang` field before building the ePub. Simplest approach: a Python helper that patches the YAML, or make `build_tex.py` also handle metadata generation.
3. **novel.tex** — Add conditional LaTeX package loading for Vietnamese support. With XeLaTeX + fontspec, EB Garamond handles Vietnamese glyphs. For proper hyphenation and localization, add `\usepackage[vietnamese]{babel}` conditionally when language is `vi`. The template itself should remain static; the conditional logic belongs in `build_tex.py` which generates `chapters_content.tex`.

No font changes needed — EB Garamond covers Vietnamese diacritics natively.

## Implementation Landscape

### Key Files

- `run_pipeline.py` (lines 54–79) — `load_state()` / `default_state()` / `save_state()`. Add `"language": get_language()` to `default_state()`.
- `config.py` — Already complete from S01. Provides `get_language()`. No changes needed.
- `typeset/epub_metadata.yaml` — Static YAML with `lang: en`. Needs a mechanism to set `lang: vi` when appropriate. Either: (a) make it a Jinja/template file processed at build time, or (b) a Python function that patches it before ePub build.
- `typeset/novel.tex` — LaTeX template with `\setmainfont{EB Garamond}`. For Vietnamese, may need `\usepackage[vietnamese]{babel}` added conditionally. EB Garamond font itself requires no change.
- `typeset/build_tex.py` — Chapter assembly script. Currently no language awareness. Needs to: import `get_language()`, conditionally inject babel/polyglossia header, and potentially update the YAML metadata. Also has a hardcoded path that should use `config.py` constants.

### Build Order

1. **First:** Add `language` to `state.json` via `run_pipeline.py` — this is the data foundation. Simple one-line addition to `default_state()`.
2. **Second:** Make `epub_metadata.yaml` dynamic — create a small helper (or extend an existing script) that reads `get_language()` and writes the correct `lang` value.
3. **Third:** Update `novel.tex` and/or `build_tex.py` for Vietnamese LaTeX support — conditional babel import and verify rendering.

### Verification Approach

- **state.json:** Run `python -c "from run_pipeline import default_state; print(default_state())"` — should include `"language": "en"` (or `"vi"` if env is set).
- **epub_metadata.yaml:** After generation, `grep 'lang:' typeset/epub_metadata.yaml` should show `vi` when `AUTONOVEL_LANGUAGE=vi`.
- **LaTeX rendering:** Build a small test `.tex` file with Vietnamese sample text (e.g., "Nguyễn Phú Trọng") using EB Garamond, compile with XeLaTeX, verify diacritics render correctly. Can be verified visually or by checking PDF output for expected glyph coverage.
- **Integration:** Set `AUTONOVEL_LANGUAGE=vi`, run the export pipeline, verify all three outputs reflect Vietnamese.
