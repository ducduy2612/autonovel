# S01: Language config + shared loader — UAT

**Milestone:** M001
**Written:** 2026-04-16T16:11:40.678Z


# S01: Language config + shared loader — UAT

**Milestone:** M001
**Written:** 2026-04-16

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: This slice produces a config module and tests — no runtime server or UI to test interactively.

## Preconditions

- Project dependencies installed (`uv sync`)
- No AUTONOVEL_LANGUAGE set in shell environment (or tests use monkeypatch isolation)

## Smoke Test

Run `uv run pytest test_config.py -v` — all 19 tests should pass.

## Test Cases

### 1. get_language() returns 'en' by default

1. Ensure AUTONOVEL_LANGUAGE is not set in environment
2. Run: `uv run python -c "from config import get_language; assert get_language() == 'en'"`
3. **Expected:** Exit code 0, no output

### 2. get_language() returns 'vi' when configured

1. Run: `AUTONOVEL_LANGUAGE=vi uv run python -c "from config import get_language; assert get_language() == 'vi'"`
2. **Expected:** Exit code 0, no output

### 3. get_language() warns and falls back on unsupported value

1. Run: `AUTONOVEL_LANGUAGE=xx uv run python -c "from config import get_language; assert get_language() == 'en'" 2>&1`
2. **Expected:** Exit code 0, stderr contains "WARNING: AUTONOVEL_LANGUAGE='xx'"

### 4. All config exports are importable

1. Run: `uv run python -c "from config import get_language, API_KEY, WRITER_MODEL, JUDGE_MODEL, REVIEW_MODEL, API_BASE, BASE_DIR, CHAPTERS_DIR, FAL_KEY, ELEVENLABS_KEY; print('ALL EXPORTS OK')"`
2. **Expected:** Exit code 0, prints "ALL EXPORTS OK"

### 5. .env.example documents AUTONOVEL_LANGUAGE

1. Check: `grep AUTONOVEL_LANGUAGE .env.example`
2. **Expected:** Line exists with the variable name and comment explaining supported values

### 6. pytest suite runs with full coverage

1. Run: `uv run pytest test_config.py -v`
2. **Expected:** 19 passed, 0 failed, 0 errors

## Edge Cases

### Environment already has AUTONOVEL_LANGUAGE set to unsupported value

1. Run: `AUTONOVEL_LANGUAGE=fr uv run python -c "from config import get_language; print(get_language())" 2>&1`
2. **Expected:** Prints 'en' to stdout, WARNING to stderr — graceful fallback, no crash

## Failure Signals

- ImportError when importing from config — module is missing or has syntax errors
- get_language() returns None or raises — env var handling is broken
- Tests fail after env var changes — test isolation via monkeypatch is insufficient

## Not Proven By This UAT

- That downstream scripts (gen_world.py, etc.) correctly import from config — that is S02's scope
- That the config module works correctly inside the full pipeline runtime
- Performance or concurrency behavior under load (N/A for a config module)

