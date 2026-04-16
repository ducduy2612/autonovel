# S01: Language config + shared loader — Research

**Date:** 2026-04-16

## Summary

This slice creates a shared config module (`config.py`) that reads `AUTONOVEL_LANGUAGE` from `.env` and provides it to all pipeline scripts. The codebase has an extremely consistent pattern: 17 scripts independently call `from dotenv import load_dotenv`, `load_dotenv(BASE_DIR / ".env")`, and read the same 3 env vars (`AUTONOVEL_WRITER_MODEL`, `ANTHROPIC_API_KEY`, `AUTONOVEL_API_BASE_URL`). There is no existing shared module — every script duplicates this boilerplate.

The work is straightforward: create `config.py` with the language getter, add `AUTONOVEL_LANGUAGE` to `.env.example`, and update scripts to import from it. Downstream slices (S02–S04) will consume `get_language()` but do not need changes in this slice.

## Recommendation

Create a single `config.py` module at project root that:
1. Calls `load_dotenv()` once
2. Exports all existing config values (API keys, model names, base URLs)
3. Adds a `get_language()` function that reads `AUTONOVEL_LANGUAGE`, defaults to `"en"`, and warns on unsupported values

This module becomes the single source of truth. Future slices import from `config` instead of reading env vars directly. **Do NOT update all 17 scripts in this slice** — that's S02's job. This slice only creates the module and documents `.env.example`.

## Implementation Landscape

### Key Files

- **NEW: `config.py`** — Shared config module. Contains `load_dotenv()` call, exports `API_KEY`, `WRITER_MODEL`, `JUDGE_MODEL`, `REVIEW_MODEL`, `API_BASE`, `BASE_DIR`, `CHAPTERS_DIR`, and `get_language()`.
- `.env.example` — Add `AUTONOVEL_LANGUAGE=en` entry with documentation comment
- `state.json` — No changes needed now (S04 adds `language` field)

### Existing Pattern (repeated in 17 scripts)

Every script does:
```python
from dotenv import load_dotenv
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")
WRITER_MODEL = os.environ.get("AUTONOVEL_WRITER_MODEL", "claude-sonnet-4-6")
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
API_BASE = os.environ.get("AUTONOVEL_API_BASE_URL", "https://api.anthropic.com")
```

Some scripts use `JUDGE_MODEL` or `REVIEW_MODEL` instead of `WRITER_MODEL`, but the pattern is identical.

### `get_language()` Design

```python
SUPPORTED_LANGUAGES = {"en", "vi"}

def get_language() -> str:
    lang = os.environ.get("AUTONOVEL_LANGUAGE", "en").strip().lower()
    if lang not in SUPPORTED_LANGUAGES:
        print(f"WARNING: AUTONOVEL_LANGUAGE='{lang}' not supported, falling back to 'en'", file=sys.stderr)
        return "en"
    return lang
```

### `config.py` Should Also Export

- `API_KEY` (from `ANTHROPIC_API_KEY`)
- `WRITER_MODEL` (from `AUTONOVEL_WRITER_MODEL`, default `claude-sonnet-4-6`)
- `JUDGE_MODEL` (from `AUTONOVEL_JUDGE_MODEL`, default `claude-opus-4-6`)
- `REVIEW_MODEL` (from `AUTONOVEL_REVIEW_MODEL`, default `claude-opus-4-6`)
- `API_BASE` (from `AUTONOVEL_API_BASE_URL`, default `https://api.anthropic.com`)
- `BASE_DIR = Path(__file__).parent`
- `CHAPTERS_DIR = BASE_DIR / "chapters"`
- `FAL_KEY` (from `FAL_KEY`, used by art scripts)
- `ELEVENLABS_KEY` (from `ELEVENLABS_API_KEY`, used by audiobook scripts)

### Build Order

1. Create `config.py` with `get_language()` and all existing config exports
2. Add `AUTONOVEL_LANGUAGE` to `.env.example`
3. Write a quick verification script or test that confirms `get_language()` returns correct values

Scripts will be migrated to import from `config` in S02.

### Verification Approach

```bash
# Test default (no env var set)
uv run python -c "from config import get_language; assert get_language() == 'en'"

# Test Vietnamese
AUTONOVEL_LANGUAGE=vi uv run python -c "from config import get_language; assert get_language() == 'vi'"

# Test fallback with warning
AUTONOVEL_LANGUAGE=fr uv run python -c "from config import get_language; assert get_language() == 'en'" 2>&1 | grep WARNING

# Test config exports work
uv run python -c "from config import API_KEY, WRITER_MODEL, API_BASE; print('OK')"
```

## Constraints

- `config.py` must call `load_dotenv(BASE_DIR / ".env")` itself (not rely on callers having done it)
- Must not break any existing script — this slice does NOT modify existing scripts
- `python-dotenv` is already a dependency (no new packages needed)
- `BASE_DIR` in `config.py` resolves to project root since `config.py` lives at project root
