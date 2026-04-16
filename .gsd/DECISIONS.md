# Decisions Register

<!-- Append-only. Never edit or remove existing rows.
     To reverse a decision, add a new row that supersedes it.
     Read this file at the start of any planning or research phase. -->

| # | When | Scope | Decision | Choice | Rationale | Revisable? | Made By |
|---|------|-------|----------|--------|-----------|------------|---------|
| D001 |  | config | Language config mechanism | AUTONOVEL_LANGUAGE env var via .env | Consistent with existing model config pattern (AUTONOVEL_WRITER_MODEL, etc.). python-dotenv already loaded in all scripts. | No | collaborative |
| D002 |  | arch | Prompt adaptation strategy | Inline conditional instructions in each script | Minimal structural change. Each script already constructs its own prompts. Adding a conditional language instruction is the lightest approach for a single target language. | Yes — if adding more languages, refactor to shared prompt system | collaborative |
| D003 |  | quality | Vietnamese evaluation strategy | Skip English regex, keep language-agnostic stats, LLM judge evaluates Vietnamese directly | English regex (banned words, AI tells, show-don't-tell) cannot match Vietnamese and would false-pass. Language-agnostic stats (sentence variation, em-dash density) still provide value. LLM judge handles quality assessment natively in any language. | Yes — add Vietnamese-specific patterns when research is done | collaborative |
