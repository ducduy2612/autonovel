---
estimated_steps: 10
estimated_files: 2
skills_used: []
---

# T01: Add language_instruction() and analysis_language_note() to config.py with tests

Add two new helper functions to config.py:

1. `language_instruction()` — returns a Vietnamese creative-writing instruction when get_language()=="vi", empty string otherwise. Text: tells LLM to write all prose, descriptions, dialogue, and narrative in natural, literary Vietnamese.

2. `analysis_language_note()` — returns a Vietnamese-awareness note when get_language()=="vi", empty string otherwise. Text: tells LLM the text is Vietnamese, may respond in English for analysis, but must preserve all quoted Vietnamese prose exactly.

Both functions should call get_language() internally (not read the env var directly) to stay DRY.

Add pytest tests to test_config.py in a new class TestLanguageInstruction covering:
- language_instruction() returns "" when lang="en"
- language_instruction() returns non-empty containing "Vietnamese" when lang="vi"
- analysis_language_note() returns "" when lang="en"
- analysis_language_note() returns non-empty containing "Vietnamese" when lang="vi"
- analysis_language_note() text differs from language_instruction() text

## Inputs

- `config.py`
- `test_config.py`

## Expected Output

- `config.py`
- `test_config.py`

## Verification

cd /home/converter/code/autonovel/.gsd/worktrees/M001 && uv run pytest test_config.py -v
