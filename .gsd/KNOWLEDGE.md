# Knowledge Base

<!-- Append-only. Add entries that would save future agents from repeating investigation.
     Do NOT add obvious observations. -->

## evaluate.py

- **slop_score() language gating**: Uses a local `is_en = (get_language() == "en")` boolean at the top of the function. All English-specific pattern lists (TIER1_BANNED, TIER2_SUSPICIOUS, etc.) are gated behind this check. When adding a new language, just extend the conditional — no structural changes needed.
- **Cross-check selection**: Uses `_get_cross_checks(prefix)` helper with `globals()` lookup pattern (`_{LANG}_{PREFIX}_CROSS_CHECKS`). To add a new language, just define `_XX_FOUNDATION_CROSS_CHECKS` and `_XX_CHAPTER_CROSS_CHECKS` variables — the helper picks them up automatically.
- **FULL_NOVEL_PROMPT is language-agnostic**: Its dimensions (arc completion, pacing, etc.) don't need language-specific cross-checks. Don't add language gating there.
- **Test reload pattern**: Tests that change AUTONOVEL_LANGUAGE must `importlib.reload(evaluate)` after setting the env var, because `get_language()` is called at function invocation time but module-level constants may be cached.

## build_tex.py

- **Module-level code wrapped in main()**: The chapter-processing loop was originally at module level and would execute on import. T01 wrapped it in a `main()` function with `if __name__ == "__main__"` guard. Future changes to build_tex.py should keep logic inside functions.
- **Regex YAML patching for epub_metadata.yaml**: `patch_epub_metadata()` uses regex to swap the `lang:` line instead of PyYAML, to avoid adding a dependency. The YAML is simple (flat key-value), so regex is reliable here.
- **Paths use config.py constants**: `BASE_DIR` and `CHAPTERS_DIR` from config.py replaced the old hardcoded `/home/jeffq/autonovel/` paths. Don't re-introduce hardcoded paths.

## run_pipeline.py

- **default_state() includes language field**: The `language` key is populated from `config.get_language()` at state creation time. This means if the env var changes mid-pipeline, state.json retains the original value. This is by design — the pipeline language should be consistent from start to finish.
- **run_foundation() writes foundation script stdout to .md files**: Each foundation script (gen_world, gen_characters, gen_outline, gen_outline_part2, gen_canon) prints to stdout but doesn't write files. run_foundation() captures uv_run() stdout and writes to world.md, characters.md, outline.md (append for part2), canon.md. Writes are guarded by returncode==0 and stdout.strip() to avoid overwriting good output with failures.
- **gen_outline_part2.py reads from /tmp/outline_output.md**: run_foundation() must also write gen_outline.py output to /tmp/outline_output.md for gen_outline_part2.py to read. This is a hardcoded path in gen_outline_part2.py.

## Foundation scripts (gen_world, gen_characters, gen_outline, gen_outline_part2, gen_canon)

- **File reads at module import time**: Several scripts read files (seed.txt, voice.md, world.md, characters.md, outline.md) at module import time using config.BASE_DIR. Tests that import these scripts must patch config.BASE_DIR and create the required input files before import/reload.
- **All use call_writer() → httpx.post pattern**: Each script calls a `call_writer()` helper that sends the prompt to the Anthropic API via httpx.post. Language instruction from config.language_instruction() is injected into the system prompt.

## Vietnamese pipeline testing

- **contains_vietnamese() helper in test_s05_e2e.py**: Detects Vietnamese-specific diacritical characters (ă, â, đ, ê, ô, ơ, ư). Used in integration tests to verify Vietnamese output. These characters are unique to Vietnamese and don't appear in other Latin-script languages.
- **Vietnamese seed concept (seed_vi.txt)**: Uses a fragrance-magic theme in Trường Sơn mountains setting with Vietnamese cultural elements. ~723 words of natural Vietnamese prose.
