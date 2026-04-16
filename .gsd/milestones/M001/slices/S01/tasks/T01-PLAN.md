---
estimated_steps: 1
estimated_files: 2
skills_used: []
---

# T01: Create config.py with get_language() and shared config exports, update .env.example

Create a shared config module at project root that centralizes all environment variable reading. The module must call load_dotenv() itself (not rely on callers), export all existing config values as module-level constants, and provide get_language() for the new AUTONOVEL_LANGUAGE setting. Also update .env.example to document the new variable.

## Inputs

- `.env.example`

## Expected Output

- `config.py`
- `.env.example`

## Verification

uv run python -c "from config import get_language, API_KEY, WRITER_MODEL, JUDGE_MODEL, REVIEW_MODEL, API_BASE, BASE_DIR, CHAPTERS_DIR, FAL_KEY, ELEVENLABS_KEY; assert get_language() == 'en'; print('ALL EXPORTS OK')"
