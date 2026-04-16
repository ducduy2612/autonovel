---
id: T02
parent: S01
milestone: M001
key_files:
  - test_config.py
  - pyproject.toml
key_decisions:
  - (none)
duration: 
verification_result: passed
completed_at: 2026-04-16T16:10:02.802Z
blocker_discovered: false
---

# T02: Add pytest dev dependency and write test_config.py with 19 tests covering get_language(), all config exports, and env var wiring

**Add pytest dev dependency and write test_config.py with 19 tests covering get_language(), all config exports, and env var wiring**

## What Happened

Added pytest as a dev dependency via `uv add --dev pytest`. Created test_config.py with 19 tests organized into three classes:

1. **TestGetLanguage** (4 tests): Verifies default 'en' return, explicit 'en', 'vi' support, and unsupported-value fallback to 'en' with a stderr WARNING message. Uses monkeypatch to isolate each test from the developer's environment.

2. **TestExports** (11 tests): Confirms all documented module-level names (API_KEY, WRITER_MODEL, JUDGE_MODEL, REVIEW_MODEL, API_BASE, FAL_KEY, ELEVENLABS_KEY, BASE_DIR, CHAPTERS_DIR) are importable with correct types (str or pathlib.Path). Also verifies CHAPTERS_DIR is inside BASE_DIR and BASE_DIR is an absolute resolved path.

3. **TestEnvWiring** (4 tests): Uses importlib.reload() after monkeypatching env vars to verify that WRITER_MODEL, JUDGE_MODEL, REVIEW_MODEL, and API_BASE actually read from their respective AUTONOVEL_* environment variables.

All 19 tests pass in 0.02s.

## Verification

Ran `uv run pytest test_config.py -v` — all 19 tests pass (exit code 0). Tests cover: default language 'en', 'vi' support, unsupported language fallback with stderr warning, all export types, path relationships, and env var wiring for model/base-url config.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `uv run pytest test_config.py -v` | 0 | ✅ pass | 500ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `test_config.py`
- `pyproject.toml`
