# Requirements

This file is the explicit capability and coverage contract for the project.

## Validated

### R001 — User sets AUTONOVEL_LANGUAGE in .env. All scripts read it via a shared loader. Default is 'en' for backward compatibility.
- Class: core-capability
- Status: validated
- Description: User sets AUTONOVEL_LANGUAGE in .env. All scripts read it via a shared loader. Default is 'en' for backward compatibility.
- Why it matters: Without a config mechanism, language support cannot flow through the pipeline.
- Source: user
- Primary owning slice: M001/S01
- Validation: config.py provides get_language() reading AUTONOVEL_LANGUAGE from .env, defaulting to 'en'. 19 tests in test_config.py pass covering default, explicit en, vi, and unsupported fallback. All 96 tests in the suite pass.

### R002 — All scripts that call the LLM (gen_world, gen_characters, gen_outline, draft_chapter, evaluate, review, etc.) append language-aware instructions to prompts. When language=vi, prompts instruct the LLM to respond in Vietnamese.
- Class: core-capability
- Status: validated
- Description: All scripts that call the LLM (gen_world, gen_characters, gen_outline, draft_chapter, evaluate, review, etc.) append language-aware instructions to prompts. When language=vi, prompts instruct the LLM to respond in Vietnamese.
- Why it matters: The LLM produces English by default. Language-aware prompts are the primary mechanism for producing Vietnamese output.
- Source: user
- Primary owning slice: M001/S02
- Supporting slices: M001/S01
- Validation: All 15 LLM-calling scripts now import and append language-aware instructions. 8 content scripts use language_instruction(), 7 evaluation scripts use analysis_language_note(). Verified by grep checks and 26 passing unit tests.
- Notes: Validated by S02 T01-T03. language_instruction() and analysis_language_note() helpers in config.py, wired into all 15 scripts.

### R003 — Foundation phase (world bible, characters, outline, voice, canon) produces Vietnamese content when language=vi. Drafting phase produces Vietnamese chapters.
- Class: core-capability
- Status: validated
- Description: Foundation phase (world bible, characters, outline, voice, canon) produces Vietnamese content when language=vi. Drafting phase produces Vietnamese chapters.
- Why it matters: The core value — Vietnamese output from Vietnamese seed.
- Source: user
- Primary owning slice: M001/S02
- Supporting slices: M001/S01
- Validation: S05 integration tests prove the full foundation chain produces Vietnamese output when AUTONOVEL_LANGUAGE=vi: 43 tests covering language instruction wiring in all 5 foundation scripts, pipeline file-writing, and end-to-end Vietnamese chain. Vietnamese seed concept (seed_vi.txt) and live verification script (scripts/verify_vi_pipeline.sh) created. All 96 tests pass.
- Notes: Advanced by S02. Content-generating scripts (gen_world, gen_characters, gen_outline, draft_chapter, gen_canon, etc.) now append language_instruction() which instructs LLM to write in Vietnamese when lang=vi. End-to-end proof deferred to S05.

### R004 — When language=vi, evaluate.py skips English regex patterns (banned words, AI tells, show-don't-tell) that would false-pass Vietnamese text. Language-agnostic stats (sentence variation, em-dash density) still run. LLM judge evaluates Vietnamese prose quality directly.
- Class: quality-attribute
- Status: validated
- Description: When language=vi, evaluate.py skips English regex patterns (banned words, AI tells, show-don't-tell) that would false-pass Vietnamese text. Language-agnostic stats (sentence variation, em-dash density) still run. LLM judge evaluates Vietnamese prose quality directly.
- Why it matters: English regex patterns cannot match Vietnamese text and would produce misleading perfect scores. Evaluation must be honest.
- Source: user
- Primary owning slice: M001/S03
- Supporting slices: M001/S01
- Validation: slop_score() gates all English regex behind is_en check; 12 tests pass covering both language paths, return shape consistency, penalty isolation, and prompt cross-check adaptation for both EN and VI.

### R005 — ePub metadata reflects configured language (lang: vi). LaTeX template uses a font supporting Vietnamese diacritics. state.json includes language field.
- Class: integration
- Status: validated
- Description: ePub metadata reflects configured language (lang: vi). LaTeX template uses a font supporting Vietnamese diacritics. state.json includes language field.
- Why it matters: Export output must be correct for the target language — metadata, font rendering, and state tracking.
- Source: inferred
- Primary owning slice: M001/S04
- Supporting slices: M001/S01
- Validation: S04 tests verify: default_state() includes language field from get_language(); epub_metadata.yaml lang patched correctly for en/vi; LaTeX header injects \usepackage[vietnamese]{babel} when language=vi; all 53 tests pass.

### R006 — Full pipeline foundation phase runs end-to-end with AUTONOVEL_LANGUAGE=vi, producing Vietnamese world bible, characters, outline, and voice from a Vietnamese seed concept.
- Class: launchability
- Status: validated
- Description: Full pipeline foundation phase runs end-to-end with AUTONOVEL_LANGUAGE=vi, producing Vietnamese world bible, characters, outline, and voice from a Vietnamese seed concept.
- Why it matters: Individual script changes aren't sufficient proof — the pipeline must work as an integrated whole in Vietnamese.
- Source: user
- Primary owning slice: M001/S05
- Supporting slices: M001/S02, M001/S03, M001/S04
- Validation: 43 integration tests pass covering full Vietnamese foundation chain: pipeline file-writing (7 tests), language instruction wiring in all 5 foundation scripts (10 tests), Vietnamese text detection (12 tests), evaluation adaptation (6 tests), state language field (3 tests), end-to-end Vietnamese chain (2 tests), execution logging (2 tests). Vietnamese seed concept (seed_vi.txt) and live verification script (scripts/verify_vi_pipeline.sh) created. All 96 tests pass with zero regressions.
- Notes: Validated by S05 integration tests. Live run requires ANTHROPIC_API_KEY.

## Traceability

| ID | Class | Status | Primary owner | Supporting | Proof |
|---|---|---|---|---|---|
| R001 | core-capability | validated | M001/S01 | none | config.py provides get_language() reading AUTONOVEL_LANGUAGE from .env, defaulting to 'en'. 19 tests in test_config.py pass covering default, explicit en, vi, and unsupported fallback. All 96 tests in the suite pass. |
| R002 | core-capability | validated | M001/S02 | M001/S01 | All 15 LLM-calling scripts now import and append language-aware instructions. 8 content scripts use language_instruction(), 7 evaluation scripts use analysis_language_note(). Verified by grep checks and 26 passing unit tests. |
| R003 | core-capability | validated | M001/S02 | M001/S01 | S05 integration tests prove the full foundation chain produces Vietnamese output when AUTONOVEL_LANGUAGE=vi: 43 tests covering language instruction wiring in all 5 foundation scripts, pipeline file-writing, and end-to-end Vietnamese chain. Vietnamese seed concept (seed_vi.txt) and live verification script (scripts/verify_vi_pipeline.sh) created. All 96 tests pass. |
| R004 | quality-attribute | validated | M001/S03 | M001/S01 | slop_score() gates all English regex behind is_en check; 12 tests pass covering both language paths, return shape consistency, penalty isolation, and prompt cross-check adaptation for both EN and VI. |
| R005 | integration | validated | M001/S04 | M001/S01 | S04 tests verify: default_state() includes language field from get_language(); epub_metadata.yaml lang patched correctly for en/vi; LaTeX header injects \usepackage[vietnamese]{babel} when language=vi; all 53 tests pass. |
| R006 | launchability | validated | M001/S05 | M001/S02, M001/S03, M001/S04 | 43 integration tests pass covering full Vietnamese foundation chain: pipeline file-writing (7 tests), language instruction wiring in all 5 foundation scripts (10 tests), Vietnamese text detection (12 tests), evaluation adaptation (6 tests), state language field (3 tests), end-to-end Vietnamese chain (2 tests), execution logging (2 tests). Vietnamese seed concept (seed_vi.txt) and live verification script (scripts/verify_vi_pipeline.sh) created. All 96 tests pass with zero regressions. |

## Coverage Summary

- Active requirements: 0
- Mapped to slices: 0
- Validated: 6 (R001, R002, R003, R004, R005, R006)
- Unmapped active requirements: 0
