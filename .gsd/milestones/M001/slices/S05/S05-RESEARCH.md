# S05: End-to-end Vietnamese pipeline verification — Research

**Date:** 2026-04-16

## Summary

S05 validates that all prior slices (S02–S04) work together as an integrated whole when `AUTONOVEL_LANGUAGE=vi`. The foundation phase must produce Vietnamese world bible, characters, outline, voice, canon, and honest evaluation scores from a Vietnamese seed concept. Each prior slice has been unit-tested in isolation — 53 tests pass — but no test exercises the full chain of scripts reading language config, constructing Vietnamese-aware prompts, processing LLM responses, and evaluating the results.

The core verification has two dimensions: (1) **wiring correctness** — proving each script in the foundation chain sends the right language-aware prompt to the API, and (2) **runtime correctness** — proving the LLM actually returns Vietnamese and evaluation handles it properly. A mocked integration test covers dimension 1 thoroughly without API costs. A live run (requiring `ANTHROPIC_API_KEY`) covers dimension 2.

A critical pipeline gap exists: `run_pipeline.py` runs foundation scripts via `subprocess.run(capture_output=True)` but never writes their stdout to the corresponding output files (world.md, characters.md, etc.). The scripts print to stdout; they don't write to files themselves (unlike `draft_chapter.py` which calls `write_text`). This means `run_pipeline.py --phase foundation` will generate LLM output but discard it. This gap must be fixed before end-to-end verification can work through the orchestrator.

## Recommendation

Three-task approach: (1) fix `run_pipeline.py` to save foundation script output to files, (2) create a comprehensive integration test with mocked API calls that verifies the full Vietnamese foundation chain, and (3) prepare a Vietnamese seed and document the live verification procedure. The integration test is the primary deliverable — it proves wiring correctness without API costs and can run in CI. The live run is the final validation step that requires manual execution with an API key.

## Implementation Landscape

### Key Files

- `run_pipeline.py` — Pipeline orchestrator. Runs foundation scripts sequentially in `run_foundation()` (lines 245–306). **Gap:** calls `uv_run("gen_world.py")` etc. but captures stdout without writing to files. Needs `Path("world.md").write_text(result.stdout)` for each foundation script.
- `gen_world.py` — Reads `seed.txt`, `voice.md`, `CRAFT.md`. Prints world bible to stdout. System prompt includes `+ language_instruction()`.
- `gen_characters.py` — Reads `seed.txt`, `world.md`, `voice.md`, `CRAFT.md`. Prints characters to stdout. System prompt includes `+ language_instruction()`.
- `gen_outline.py` — Reads `seed.txt`, `world.md`, `characters.md`, `MYSTERY.md`, `CRAFT.md`, `voice.md`. Prints outline to stdout. System prompt includes `+ language_instruction()`. **Also reads `MYSTERY.md`** which must exist (currently a stub file).
- `gen_outline_part2.py` — Reads existing `outline.md` plus world/characters. Prints remaining outline to stdout. System prompt includes `+ language_instruction()`.
- `gen_canon.py` — Reads `world.md`, `characters.md`, `seed.txt`. Prints canon to stdout. System prompt includes `+ language_instruction()`.
- `voice_fingerprint.py` — Purely statistical (word counts, sentence lengths, vocabulary wells). No LLM calls, no language imports needed. Reads from `chapters/` which is empty during foundation. Runs without errors but produces empty/minimal output during foundation phase.
- `evaluate.py` — Foundation evaluation reads `voice.md`, `world.md`, `characters.md`, `outline.md`, `canon.md`. Calls LLM judge with `analysis_language_note()` and language-selected cross-checks. `slop_score()` gates English regex behind `is_en` check.
- `config.py` — `get_language()`, `language_instruction()`, `analysis_language_note()` — all tested in S01/S02.
- `typeset/epub_metadata.yaml` — Currently has `lang: vi` (left from S04 testing). Will be dynamically patched by `build_tex.py`.
- `seed.txt` — **Does not exist yet.** Must be created with Vietnamese content.
- `voice.md` — Exists as English template stub with Part 1 (guardrails) and Part 2 (voice identity placeholder).
- `MYSTERY.md` — Exists as stub with header only. Read by `gen_outline.py`.
- `.env` — **Does not exist yet.** Must be created with `AUTONOVEL_LANGUAGE=vi` and `ANTHROPIC_API_KEY`.
- `test_s05_e2e.py` — New test file for integration tests.

### Pipeline Script Execution Order (Foundation Phase)

```
1. gen_world.py          → stdout → world.md        (reads: seed.txt, voice.md, CRAFT.md)
2. gen_characters.py     → stdout → characters.md   (reads: seed.txt, world.md, voice.md, CRAFT.md)
3. gen_outline.py        → stdout → outline.md      (reads: seed.txt, world.md, characters.md, MYSTERY.md, CRAFT.md, voice.md)
4. gen_outline_part2.py  → stdout → outline.md append (reads: seed.txt, outline.md, world.md, characters.md)
5. gen_canon.py          → stdout → canon.md        (reads: world.md, characters.md, seed.txt)
6. voice_fingerprint.py  → no output files          (reads: chapters/ — empty during foundation)
7. evaluate.py --phase=foundation → eval_logs/*.json (reads: all planning docs, calls LLM judge)
```

### Build Order

**T01 first:** Fix `run_pipeline.py` to redirect foundation output to files. This unblocks the actual pipeline run and is a prerequisite for any end-to-end verification through the orchestrator.

**T02 second:** Create integration test with mocked httpx that simulates the full foundation chain with `AUTONOVEL_LANGUAGE=vi`. This proves wiring correctness without API costs and can run in CI.

**T03 last:** Prepare Vietnamese seed.txt, .env template, and run the live foundation loop. This is the final validation that the LLM actually produces Vietnamese content. Requires `ANTHROPIC_API_KEY`.

### Verification Approach

**T01 verification:** Run `run_pipeline.py --phase foundation` with a mocked API and check that world.md, characters.md, outline.md, canon.md are created with content.

**T02 verification:** Integration test with mocked httpx verifies:
- Each foundation script's API payload includes Vietnamese language instruction in system prompt
- Vietnamese text detection works (checks for ă, â, đ, ê, ô, ơ, ư characters)
- `evaluate.py` with `AUTONOVEL_LANGUAGE=vi` skips English regex, uses VI cross-checks
- `default_state()` returns `language: "vi"`
- Full chain: seed → world → characters → outline → canon → evaluation works without errors

**T03 verification:** Manual run with real API key:
```bash
# Set up environment
echo 'AUTONOVEL_LANGUAGE=vi' > .env
echo 'ANTHROPIC_API_KEY=sk-ant-...' >> .env

# Create Vietnamese seed
cat > seed.txt << 'EOF'
[Vietnamese seed concept — see test_s05_e2e.py for example]
EOF

# Run foundation phase
uv run python run_pipeline.py --from-scratch --phase foundation

# Verify outputs contain Vietnamese
python3 -c "
import re
for f in ['world.md', 'characters.md', 'outline.md', 'canon.md']:
    text = open(f).read()
    vi_chars = set('ăâđêôơưĂÂĐÊÔƠƯ')
    has_vi = any(c in vi_chars for c in text)
    print(f'{f}: Vietnamese={has_vi}, length={len(text)}')
"

# Verify state
python3 -c "import json; s=json.load(open('state.json')); print(f'language={s[\"language\"]}')"
```

### Vietnamese Text Detection

Vietnamese text can be reliably distinguished from English by checking for Vietnamese-specific characters: `ă â đ ê ô ơ ư` (and their uppercase equivalents). These characters appear in virtually all Vietnamese prose of any length but never in English. This provides a simple, reliable heuristic for output verification without needing NLP libraries.

```python
VI_CHARS = set('ăâđêôơưĂÂĐÊÔƠƯ')
def contains_vietnamese(text: str) -> bool:
    return any(c in VI_CHARS for c in text)
```

## Constraints

- **API key required for live run:** The pipeline calls the Anthropic API for every foundation script. A live end-to-end test requires `ANTHROPIC_API_KEY` in `.env`. Mocked tests can run without it.
- **No file writing by foundation scripts:** `gen_world.py`, `gen_characters.py`, `gen_outline.py`, `gen_outline_part2.py`, `gen_canon.py` all `print()` to stdout — they do NOT call `write_text()`. Only `draft_chapter.py` writes to files directly. This is the gap in `run_pipeline.py`.
- **Sequential dependencies:** Foundation scripts must run in order — each reads the output of the previous script. No parallelism possible.
- **voice_fingerprint.py is a no-op during foundation:** It reads from `chapters/` which is empty during the foundation phase. It runs without error but produces no meaningful output. No changes needed.
- **MYSTERY.md must exist:** `gen_outline.py` reads `MYSTERY.md`. Currently a stub with header only. Should work as-is (the LLM will generate appropriate mystery content from the other inputs).

## Common Pitfalls

- **Forgetting file redirection in run_pipeline.py:** The current `uv_run()` calls capture stdout but never write to the planning doc files. Without fixing this, `run_pipeline.py --phase foundation` silently discards all LLM output. Every script after the first would read empty/stub input files.
- **epub_metadata.yaml has stale lang:vi:** S04 testing left `lang: vi` in the YAML. The pipeline should reset this or use the dynamic patching from `build_tex.py`. For verification, check that `patch_epub_metadata()` correctly sets the lang based on `get_language()`.
- **state.json missing language field:** The existing `state.json` in the worktree was created before S04 and lacks the `language` key. Running `run_pipeline.py --from-scratch` calls `default_state()` which now includes `language: get_language()`, so this self-corrects.
- **Vietnamese seed must be authentically Vietnamese:** A machine-translated English seed will produce lower-quality results. The seed should be written as natural Vietnamese.
