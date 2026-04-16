# S01: Language config + shared loader

**Goal:** Create a shared config module (config.py) that reads AUTONOVEL_LANGUAGE from .env and provides get_language() to all pipeline scripts. Export all existing config vars (API_KEY, WRITER_MODEL, JUDGE_MODEL, REVIEW_MODEL, API_BASE, BASE_DIR, CHAPTERS_DIR, FAL_KEY, ELEVENLABS_KEY) from a single source of truth. Default language is 'en' for backward compatibility.
**Demo:** Shared config module returns 'vi' when AUTONOVEL_LANGUAGE=vi, 'en' by default. .env.example documented with new variable.

## Must-Haves

- config.py exists at project root and imports cleanly
- get_language() returns "en" when AUTONOVEL_LANGUAGE is not set
- get_language() returns "vi" when AUTONOVEL_LANGUAGE=vi
- get_language() returns "en" with stderr warning when AUTONOVEL_LANGUAGE is unsupported
- All config exports (API_KEY, WRITER_MODEL, etc.) are accessible from config module
- .env.example includes AUTONOVEL_LANGUAGE with documentation comment
- pytest test suite passes with full coverage of config behaviors

## Proof Level

- This slice proves: contract

## Integration Closure

Upstream surfaces consumed: .env file (via python-dotenv), os.environ. New wiring: config.py becomes the single import point for all config. What remains: S02 migrates 17 scripts to import from config instead of reading env vars directly.

## Verification

- get_language() prints WARNING to stderr on unsupported language values, making misconfiguration visible in logs.

## Tasks

- [x] **T01: Create config.py with get_language() and shared config exports, update .env.example** `est:20m`
  Create a shared config module at project root that centralizes all environment variable reading. The module must call load_dotenv() itself (not rely on callers), export all existing config values as module-level constants, and provide get_language() for the new AUTONOVEL_LANGUAGE setting. Also update .env.example to document the new variable.
  - Files: `config.py`, `.env.example`
  - Verify: uv run python -c "from config import get_language, API_KEY, WRITER_MODEL, JUDGE_MODEL, REVIEW_MODEL, API_BASE, BASE_DIR, CHAPTERS_DIR, FAL_KEY, ELEVENLABS_KEY; assert get_language() == 'en'; print('ALL EXPORTS OK')"

- [x] **T02: Add pytest and write test_config.py covering all config behaviors** `est:15m`
  Add pytest as a dev dependency and create test_config.py with tests covering: (1) get_language() returns 'en' by default, (2) returns 'vi' when AUTONOVEL_LANGUAGE=vi, (3) returns 'en' with warning on unsupported values, (4) all config module exports are importable, (5) BASE_DIR and CHAPTERS_DIR are correct pathlib.Path objects. Tests must use monkeypatch or os.environ manipulation to avoid depending on the developer's .env file.
  - Files: `test_config.py`, `pyproject.toml`
  - Verify: uv run pytest test_config.py -v

## Files Likely Touched

- config.py
- .env.example
- test_config.py
- pyproject.toml
