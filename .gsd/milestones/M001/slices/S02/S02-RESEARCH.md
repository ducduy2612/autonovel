# S02: Vietnamese prompts in all LLM-calling scripts — Research

**Date:** 2026-04-16

## Summary

There are **17 Python scripts** that call the Anthropic LLM API via raw `httpx.post`. Every script follows the same pattern: a thin `call_writer`/`call_judge`/`call_opus`/`call_model`/`call_claude` wrapper that constructs an httpx payload with a `system` string and a `messages` array. None of them import from `config.py` yet — each duplicates env var reads for `API_KEY`, `API_BASE`, and model names.

To add Vietnamese language support, each script needs two changes: (1) import `get_language` from `config`, and (2) append a language instruction to the `system` prompt (and optionally the user prompt) when `lang == "vi"`. The system prompt is the ideal injection point because it consistently frames the LLM's persona and output language.

Additionally, `seed.py` and `gen_art_directions.py` have **no system prompt** — they pass only `messages`. These need a system prompt added (or a user-message prefix) to receive the language instruction.

## Recommendation

**Add a shared `language_instruction()` helper to `config.py`** that returns a language-aware suffix string. Each script imports it and appends it to its `system` prompt. This avoids duplicating the language instruction text across 17 files and keeps the behavior centrally defined.

For content-generating scripts (gen_world, gen_characters, gen_outline, draft_chapter, gen_canon, gen_revision, seed), the instruction should be: "Write all output in Vietnamese (tiếng Việt). All prose, descriptions, dialogue, and narrative must be in natural, literary Vietnamese."

For evaluation/judging scripts (evaluate, review, reader_panel, compare_chapters, adversarial_edit, build_outline, build_arc_summary), the instruction should be: "You may respond in English for your analysis, but all quoted prose from the novel must be preserved exactly as written." These scripts analyze text — they don't generate novel content — so they don't need to switch languages.

Art-related scripts (gen_art, gen_art_directions, gen_audiobook_script) are borderline: art prompts are in English for the image model, but audiobook scripts may need Vietnamese text preservation. Leave them in English unless specifically requested.

## Implementation Landscape

### Key Files

**Scripts that GENERATE novel content (need full Vietnamese output):**
- `gen_world.py` — `call_writer()` with system prompt about worldbuilder persona. Lines 18-37. Prompt is a large f-string in module scope.
- `gen_characters.py` — `call_writer()` with system prompt about character designer. Lines 18-37. Same pattern.
- `gen_outline.py` — `call_writer()` with system prompt about novel architect. Lines 14-37. Has `anthropic-beta` header.
- `gen_outline_part2.py` — `call_writer()` with system prompt about continuing outline. Lines 15-30. Simpler system prompt.
- `draft_chapter.py` — `call_writer()` with system prompt about literary fiction writer. Lines 17-38. Core drafting script.
- `gen_canon.py` — `call_writer()` with system prompt about continuity editor. Lines 14-32. Low temperature (0.2).
- `gen_revision.py` — `call_writer()` with system prompt about rewriting chapters. Lines 14-33.
- `seed.py` — `call_writer()` with system prompt about fantasy novelist. Lines 27-50. High temperature (1.0).

**Scripts that EVALUATE/JUDGE content (preserve original text, English analysis):**
- `review.py` — `call_opus()` with no system prompt, just user message with `REVIEW_PROMPT`. Line 39-67. Need to add system prompt for language context.
- `evaluate.py` — `call_judge()` with system prompt about literary critic. Lines 275-295.
- `reader_panel.py` — `call_reader()` per-reader system prompts in `READERS` dict. Lines 113+. Four distinct reader personas, each with their own system prompt.
- `compare_chapters.py` — `call_judge()` with system prompt about literary editor. Lines 27-43.
- `adversarial_edit.py` — `call_judge()` with system prompt about ruthless editor. Lines 26-44.
- `build_outline.py` — `call_model()` with system prompt about structured outline entries. Lines 22-39.
- `build_arc_summary.py` — `call_writer()` with system prompt about chapter summarizer. Lines 20-33.

**Art/media scripts (likely leave in English):**
- `gen_art.py` — `call_claude()` with no system prompt, only messages. Lines 115-130.
- `gen_art_directions.py` — `call_claude()` with no system prompt. Lines 20-37.
- `gen_audiobook_script.py` — `call_claude()` with no system prompt. Lines 68-85.

**Scripts that do NOT call LLMs (no changes needed):**
- `voice_fingerprint.py` — pure text analysis, no API calls
- `gen_brief.py` — text processing only, no API calls
- `config.py` — shared config module (already complete from S01)

### Current Prompt Construction Pattern

Every LLM-calling script follows this structure:
1. Module-level env var reads: `API_KEY`, `API_BASE`, model name
2. A `call_*` function that builds an httpx payload with `system` (string) and `messages` (list)
3. The user prompt is a large f-string at module scope or inline in `main()`

The insertion point is always the `system` string in the `call_*` function payload dict. For scripts without a system prompt (gen_art.py, gen_art_directions.py, gen_audiobook_script.py, review.py), a system prompt needs to be added.

### config.py Already Provides

```python
from config import get_language

def get_language() -> str:
    """Return 'en' or 'vi'. Defaults to 'en'."""
```

### Proposed Addition to config.py

```python
def language_instruction() -> str:
    """Return a language instruction to append to LLM system prompts."""
    if get_language() == "vi":
        return (
            "\n\nIMPORTANT: Write all creative output in Vietnamese (tiếng Việt). "
            "All prose, descriptions, dialogue, and narrative must be in natural, "
            "literary Vietnamese. Preserve the literary quality and voice."
        )
    return ""
```

### Per-Script Change Pattern

For each content-generating script:
```python
# Replace:
from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
API_BASE = os.environ.get("AUTONOVEL_API_BASE_URL", "https://api.anthropic.com")

# With:
from config import get_language, language_instruction, API_KEY, API_BASE
```

Then in the `call_*` function:
```python
"system": (
    "You are a fantasy worldbuilder..."
    + language_instruction()
),
```

### Build Order

1. **Add `language_instruction()` to `config.py`** — single source of truth
2. **Foundation scripts first** (gen_world, gen_characters, gen_outline, gen_outline_part2, gen_canon, seed) — these produce the building blocks
3. **Drafting scripts** (draft_chapter, gen_revision) — depend on foundation being Vietnamese
4. **Evaluation scripts** (review, evaluate, reader_panel, compare_chapters, adversarial_edit, build_outline, build_arc_summary) — need to understand they're analyzing Vietnamese text
5. **Art/media scripts** — defer unless needed

### Verification Approach

1. Unit test: `language_instruction()` returns empty string for `en`, returns Vietnamese instruction for `vi`
2. Integration: Set `AUTONOVEL_LANGUAGE=vi`, run `seed.py --count=1`, verify output contains Vietnamese text
3. Integration: Run `gen_world.py` with a Vietnamese seed, verify `world.md` content is in Vietnamese
4. Check that evaluation scripts still produce valid English analysis when reviewing Vietnamese chapters
