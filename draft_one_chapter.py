#!/usr/bin/env python3
"""Run the full pipeline steps for a single chapter manually.

Does: draft → evaluate → grow canon → summarize → commit → update state.
Retries up to MAX_CHAPTER_ATTEMPTS if score < CHAPTER_THRESHOLD.

Usage: uv run python draft_one_chapter.py 1
"""
import sys

from run_pipeline import (
    uv_run, parse_score, append_new_canon_entries,
    generate_chapter_summary, git_add_commit, log_result,
    step, banner, CHAPTER_THRESHOLD, MAX_CHAPTER_ATTEMPTS,
    CHAPTERS_DIR, save_state,
)
from config import SUBPROCESS_TIMEOUT
import json

ch = int(sys.argv[1])

state = json.load(open("state.json"))
total = state.get("chapters_total", 24)

banner(f"Drafting Chapter {ch}/{total}", "-")

drafted = False
eval_result = None

for attempt in range(1, MAX_CHAPTER_ATTEMPTS + 1):
    step(f"Attempt {attempt}/{MAX_CHAPTER_ATTEMPTS}")

    _DRAFT_ENV = {"AUTONOVEL_THINKING": "off"}
    _EVAL_ENV = {"AUTONOVEL_THINKING": "on"}

    draft_result = uv_run(f"draft_chapter.py {ch}", timeout=SUBPROCESS_TIMEOUT,
                          extra_env=_DRAFT_ENV)
    if draft_result.returncode != 0:
        step(f"Draft failed (exit {draft_result.returncode}), retrying...")
        continue

    ch_file = CHAPTERS_DIR / f"ch_{ch:02d}.md"
    if not ch_file.exists() or ch_file.stat().st_size < 100:
        step("Chapter file missing or too short, retrying...")
        continue

    word_count = len(ch_file.read_text().split())
    step(f"Drafted {word_count} words")

    eval_result = uv_run(f"evaluate.py --chapter={ch}", timeout=SUBPROCESS_TIMEOUT,
                         extra_env=_EVAL_ENV)
    score = parse_score(eval_result.stdout, "overall_score")
    step(f"Chapter {ch} score: {score}")

    if score >= CHAPTER_THRESHOLD:
        n_facts = append_new_canon_entries(eval_result.stdout, ch)
        if n_facts:
            step(f"Added {n_facts} new facts to canon.md")
        generate_chapter_summary(ch)
        commit_hash = git_add_commit(
            f"ch{ch:02d}: score {score}, {word_count}w, +{n_facts} canon")
        log_result(commit_hash, f"ch{ch:02d}", score, word_count,
                   "keep", f"Chapter {ch} (attempt {attempt})")
        state["chapters_drafted"] = ch
        save_state(state)
        drafted = True
        break
    else:
        step(f"Score {score} < {CHAPTER_THRESHOLD}, discarding attempt")
        # Revert the bad chapter file
        import subprocess
        subprocess.run(
            f"git checkout -- chapters/ch_{ch:02d}.md 2>/dev/null || true",
            shell=True)

if not drafted:
    step(f"WARNING: Chapter {ch} failed all {MAX_CHAPTER_ATTEMPTS} attempts, "
         f"keeping last draft")
    ch_file = CHAPTERS_DIR / f"ch_{ch:02d}.md"
    if ch_file.exists() and eval_result is not None:
        n_facts = append_new_canon_entries(eval_result.stdout, ch)
        if n_facts:
            step(f"Added {n_facts} new facts to canon.md")
    generate_chapter_summary(ch)
    word_count = len(ch_file.read_text().split()) if ch_file.exists() else 0
    commit_hash = git_add_commit(
        f"ch{ch:02d}: best-effort after {MAX_CHAPTER_ATTEMPTS} attempts")
    state["chapters_drafted"] = ch
    save_state(state)
