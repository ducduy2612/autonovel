# M001: Vietnamese Language Support

**Gathered:** 2026-04-16
**Status:** Ready for planning

## Project Description

Add Vietnamese language support to the autonovel pipeline. When a user sets `AUTONOVEL_LANGUAGE=vi` in `.env` and provides a Vietnamese seed concept, the entire pipeline — foundation, drafting, evaluation, revision, export — produces Vietnamese output.

## Why This Milestone

The pipeline is hardcoded English. Every LLM prompt, evaluation pattern, and export template assumes English prose. Vietnamese is the first target language — the changes should be Vietnamese-specific but not over-abstracted.

## User-Visible Outcome

### When this milestone is complete, the user can:

- Set `AUTONOVEL_LANGUAGE=vi` in `.env`
- Provide a Vietnamese seed concept
- Run `run_pipeline.py` and get Vietnamese output at every stage

### Entry point / environment

- Entry point: `uv run python run_pipeline.py` (same as English)
- Environment: local dev
- Live dependencies: Anthropic API (same as English)

## Completion Class

- Contract complete means: every script reads language config and adapts LLM prompts; evaluation handles Vietnamese correctly; export metadata reflects language
- Integration complete means: full foundation phase runs in Vietnamese end-to-end
- Operational complete means: none (same runtime environment as English)

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- Foundation loop produces Vietnamese world bible, characters, outline, voice, canon
- Evaluation scores Vietnamese prose honestly (no false passes from English regex)
- ePub metadata shows `lang: vi`

## Architectural Decisions

### Language config via .env

**Decision:** Use `AUTONOVEL_LANGUAGE` env var, read via existing `python-dotenv` pattern

**Rationale:** Consistent with existing model config pattern (`AUTONOVEL_WRITER_MODEL`, etc.). No new config files or CLI flags needed.

**Alternatives Considered:**
- `state.json` field — language is a config choice, not pipeline state
- CLI flag — would require passing it through `run_pipeline.py` to every subprocess

### Inline per-script prompt adaptation

**Decision:** Each script appends language instructions to its existing prompts inline

**Rationale:** Minimal structural change. Each script already constructs its own prompts — adding a conditional Vietnamese instruction is the lightest approach.

**Alternatives Considered:**
- Shared prompt system with per-language files — over-engineered for a single target language

### LLM judge only for Vietnamese evaluation

**Decision:** Disable English regex slop detection for Vietnamese. Keep language-agnostic stats (sentence variation, em-dash density). LLM judge evaluates Vietnamese prose quality directly.

**Rationale:** English regex patterns (banned words, AI tells, show-don't-tell) cannot match Vietnamese and would produce false perfect scores. Vietnamese-specific regex patterns are a research project for later.

**Alternatives Considered:**
- Vietnamese-specific regex patterns — significant research effort, out of scope
- Run both English + Vietnamese patterns — English patterns still can't match Vietnamese text

## Error Handling Strategy

If `AUTONOVEL_LANGUAGE` is set to an unsupported value, fall back to English with a warning to stderr. No crashes.

## Risks and Unknowns

- Vietnamese literary conventions may differ from English — the LLM should handle this naturally given a Vietnamese seed, but it's unproven until tested
- EB Garamond may have rendering gaps for some Vietnamese diacritical combinations — needs verification
- Voice discovery in Vietnamese may need different exemplar structure — unproven

## Existing Codebase / Prior Art

- `gen_world.py` — representative LLM-calling script with inline prompt
- `evaluate.py` — two-layer evaluation (regex + LLM judge)
- `draft_chapter.py` — chapter drafter with system prompt
- `typeset/novel.tex` — LaTeX template with EB Garamond
- `typeset/epub_metadata.yaml` — ePub config with `lang: en`

## Relevant Requirements

- R001 — Language config from .env
- R002 — LLM prompts language-aware
- R003 — Foundation and drafting in Vietnamese
- R004 — Evaluation adapts for Vietnamese
- R005 — Export and metadata language support
- R006 — End-to-end Vietnamese pipeline verification

## Scope

### In Scope

- Language config via `AUTONOVEL_LANGUAGE` env var
- Shared config loader accessible to all scripts
- Vietnamese prompt instructions in all LLM-calling scripts
- Evaluation adaptation (skip English regex for Vietnamese)
- Export metadata and font verification
- End-to-end foundation phase verification

### Out of Scope / Non-Goals

- Vietnamese-specific regex slop patterns (future work)
- Multi-language abstraction layer (just make Vietnamese work)
- Translation of English seeds (seed must match target language)
- Audiobook voice changes for Vietnamese
- UI/CLI for language selection

## Technical Constraints

- Must not break existing English pipeline (default behavior unchanged)
- All changes must work with existing `httpx` + `python-dotenv` deps
- Vietnamese diacritics must render in both LaTeX and ePub output

## Integration Points

- Anthropic API — same endpoint, different prompt language
- LaTeX (EB Garamond) — font must support Vietnamese diacritics
- ePub (Pandoc) — metadata `lang` field
- `run_pipeline.py` — subprocess calls to scripts must pass language through

## Testing Requirements

- Verify shared loader returns correct language
- Verify at least one foundation script produces Vietnamese output
- Verify evaluation skips English regex for Vietnamese
- Verify ePub metadata reflects configured language
- Verify English pipeline still works (backward compatibility)

## Acceptance Criteria

- `AUTONOVEL_LANGUAGE=vi` in `.env` causes all LLM output to be Vietnamese
- `evaluate.py --phase=foundation` scores Vietnamese prose honestly
- English pipeline unchanged when `AUTONOVEL_LANGUAGE=en` or unset
- Export metadata and typesetting handle Vietnamese correctly

## Open Questions

- None — all resolved during discussion
