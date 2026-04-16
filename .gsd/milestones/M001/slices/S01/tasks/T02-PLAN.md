---
estimated_steps: 1
estimated_files: 2
skills_used: []
---

# T02: Add pytest and write test_config.py covering all config behaviors

Add pytest as a dev dependency and create test_config.py with tests covering: (1) get_language() returns 'en' by default, (2) returns 'vi' when AUTONOVEL_LANGUAGE=vi, (3) returns 'en' with warning on unsupported values, (4) all config module exports are importable, (5) BASE_DIR and CHAPTERS_DIR are correct pathlib.Path objects. Tests must use monkeypatch or os.environ manipulation to avoid depending on the developer's .env file.

## Inputs

- `config.py`

## Expected Output

- `test_config.py`

## Verification

uv run pytest test_config.py -v
