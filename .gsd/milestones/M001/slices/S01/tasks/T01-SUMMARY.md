---
id: T01
parent: S01
milestone: M001
key_files:
  - config.py
  - .env.example
key_decisions:
  - (none)
duration: 
verification_result: passed
completed_at: 2026-04-16T16:08:41.489Z
blocker_discovered: false
---

# T01: Create shared config.py with get_language() and all pipeline env var exports; document AUTONOVEL_LANGUAGE in .env.example

**Create shared config.py with get_language() and all pipeline env var exports; document AUTONOVEL_LANGUAGE in .env.example**

## What Happened

Created config.py at project root that centralizes all environment variable reading previously duplicated across pipeline scripts. The module calls load_dotenv() at import time, exports API_KEY, WRITER_MODEL, JUDGE_MODEL, REVIEW_MODEL, API_BASE, BASE_DIR, CHAPTERS_DIR, FAL_KEY, and ELEVENLABS_KEY as module-level constants with the same defaults scripts currently use, and provides get_language() that reads AUTONOVEL_LANGUAGE (default 'en'). Unsupported language values print a WARNING to stderr and fall back to 'en'. Updated .env.example with the new AUTONOVEL_LANGUAGE variable and its supported values.

## Verification

Ran the task-plan verification command confirming all exports are importable and get_language() returns 'en' by default. Additional tests confirmed: AUTONOVEL_LANGUAGE=vi returns 'vi', and AUTONOVEL_LANGUAGE=xx emits WARNING to stderr and falls back to 'en'.

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `uv run python -c "from config import get_language, API_KEY, WRITER_MODEL, JUDGE_MODEL, REVIEW_MODEL, API_BASE, BASE_DIR, CHAPTERS_DIR, FAL_KEY, ELEVENLABS_KEY; assert get_language() == 'en'; print('ALL EXPORTS OK')"` | 0 | ✅ pass | 4500ms |
| 2 | `AUTONOVEL_LANGUAGE=vi uv run python -c "from config import get_language; assert get_language() == 'vi'; print('VI OK')"` | 0 | ✅ pass | 1200ms |
| 3 | `AUTONOVEL_LANGUAGE=xx uv run python -c "from config import get_language; assert get_language() == 'en'; print('FALLBACK OK')" 2>&1` | 0 | ✅ pass | 1200ms |

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- `config.py`
- `.env.example`
