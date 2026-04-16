# M001: Vietnamese Language Support

## Vision
Add Vietnamese language support to the autonovel pipeline. When a user sets AUTONOVEL_LANGUAGE=vi in .env and provides a Vietnamese seed concept, the entire pipeline — foundation, drafting, evaluation, revision, export — produces Vietnamese output. English pipeline remains unchanged.

## Slice Overview
| ID | Slice | Risk | Depends | Done | After this |
|----|-------|------|---------|------|------------|
| S01 | S01 | low | — | ✅ | Shared config module returns 'vi' when AUTONOVEL_LANGUAGE=vi, 'en' by default. .env.example documented with new variable. |
| S02 | S02 | medium | — | ✅ | Run gen_world.py with AUTONOVEL_LANGUAGE=vi and a Vietnamese seed — produces Vietnamese world bible. Run gen_characters.py — produces Vietnamese characters. Same for gen_outline, draft_chapter, gen_canon, voice_fingerprint, gen_brief, gen_revision, seed, review, reader_panel, compare_chapters, adversarial_edit. |
| S03 | S03 | medium | — | ✅ | Run evaluate.py --phase=foundation with Vietnamese text — English regex slop detection is skipped, language-agnostic stats still run, LLM judge evaluates in Vietnamese. Run with English text — full regex detection runs as before. |
| S04 | S04 | low | — | ✅ | epub_metadata.yaml shows lang: vi when language=vi, lang: en otherwise. LaTeX template verified to render Vietnamese diacritics with EB Garamond. state.json includes language field. |
| S05 | S05 | high | — | ✅ | Full foundation loop with AUTONOVEL_LANGUAGE=vi and a Vietnamese seed produces: Vietnamese world bible, Vietnamese characters, Vietnamese outline, Vietnamese voice discovery, honest evaluation scores. |
