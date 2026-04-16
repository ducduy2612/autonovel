---
id: S01
parent: M001
milestone: M001
provides:
  - ["config.py module with get_language() and all shared config exports", ".env.example with AUTONOVEL_LANGUAGE documented", "19 passing tests covering all config behaviors"]
requires:
  []
affects:
  - ["S02", "S03", "S04", "S05"]
key_files:
  - ["config.py", "test_config.py", ".env.example", "pyproject.toml"]
key_decisions:
  - (none)
patterns_established:
  - ["config.py as single import point for all env vars — downstream scripts should `from config import ...` instead of calling load_dotenv() and os.environ.get() directly", "get_language() as the canonical way to determine pipeline language — all scripts should call this rather than reading AUTONOVEL_LANGUAGE directly"]
observability_surfaces:
  - none
drill_down_paths:
  []
duration: ""
verification_result: passed
completed_at: 2026-04-16T16:11:40.678Z
blocker_discovered: false
---

# S01: Language config + shared loader

**Shared config.py module centralizes all env var reading and provides get_language() returning 'en' or 'vi' from AUTONOVEL_LANGUAGE, with 19 passing tests and documented .env.example.**

## What Happened

Created config.py at project root as the single import point for all pipeline configuration. The module calls load_dotenv() at import time, exports all existing config values (API_KEY, WRITER_MODEL, JUDGE_MODEL, REVIEW_MODEL, API_BASE, BASE_DIR, CHAPTERS_DIR, FAL_KEY, ELEVENLABS_KEY) as module-level constants with backward-compatible defaults, and provides get_language() that reads AUTONOVEL_LANGUAGE (default 'en'). Unsupported language values print a WARNING to stderr and fall back to 'en'. Updated .env.example with the new AUTONOVEL_LANGUAGE variable and its supported values.

Added pytest as a dev dependency and created test_config.py with 19 tests in three classes: TestGetLanguage (4 tests for default, explicit, vi, and unsupported fallback), TestExports (11 tests for all export types and path relationships), and TestEnvWiring (4 tests verifying env var → module constant wiring via importlib.reload). All 19 tests pass in 0.01s.

## Verification

All 19 pytest tests pass (`uv run pytest test_config.py -v`, exit 0, 0.01s). Manual verification confirmed: all 9 config exports importable, get_language() returns 'en' by default, 'vi' when AUTONOVEL_LANGUAGE=vi, and 'en' with stderr WARNING on unsupported values. .env.example contains AUTONOVEL_LANGUAGE with documentation.

## Requirements Advanced

- R001 — Created config.py with get_language() that reads AUTONOVEL_LANGUAGE from .env, defaults to 'en', and is the shared loader for all pipeline scripts.

## Requirements Validated

None.

## New Requirements Surfaced

- []

## Requirements Invalidated or Re-scoped

None.

## Deviations

None.

## Known Limitations

The supported language set is hardcoded as {'en', 'vi'}. Adding a new language requires editing config.py's _SUPPORTED_LANGUAGES set. This is acceptable for the current single-target-language scope but would need refactoring if many languages are added.

## Follow-ups

S02 will migrate 17 existing scripts from direct os.environ.get() / load_dotenv() calls to importing from config.py. This will validate that the config module's defaults match what each script currently uses.

## Files Created/Modified

- `config.py` — New shared config module — get_language(), all env var exports, load_dotenv() at import time
- `test_config.py` — 19 tests covering get_language() behaviors, all exports, and env var wiring
- `.env.example` — Added AUTONOVEL_LANGUAGE with supported values documentation
- `pyproject.toml` — Added pytest as dev dependency
