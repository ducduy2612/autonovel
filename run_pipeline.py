#!/usr/bin/env python3
"""
run_pipeline.py — Fully automated novel pipeline orchestrator.

Runs the complete autonovel pipeline from seed concept to finished novel.
Manages state, git commits, evaluation, and retry logic.

Usage:
  python run_pipeline.py                    # run from current state
  python run_pipeline.py --from-scratch     # start fresh from seed.txt
  python run_pipeline.py --phase foundation # run only foundation
  python run_pipeline.py --phase drafting   # run only drafting
  python run_pipeline.py --phase revision   # run only revision
  python run_pipeline.py --phase export     # run only export
  python run_pipeline.py --max-cycles 4     # limit revision cycles
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from config import get_language, API_TIMEOUT, SUBPROCESS_TIMEOUT

# When thinking mode is on, LLM calls take much longer (reasoning tokens).
# Scale the subprocess timeout to give the inner httpx call enough room.
_THINKING_ON = os.environ.get("AUTONOVEL_THINKING", "off").lower() == "on"
_THINKING_TIMEOUT_SCALE = 3 if _THINKING_ON else 1

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent
STATE_FILE = BASE_DIR / "state.json"
RESULTS_FILE = BASE_DIR / "results.tsv"
CHAPTERS_DIR = BASE_DIR / "chapters"
BRIEFS_DIR = BASE_DIR / "briefs"
EDIT_LOGS_DIR = BASE_DIR / "edit_logs"
EVAL_LOGS_DIR = BASE_DIR / "eval_logs"
SUMMARIES_DIR = BASE_DIR / "summaries"

FOUNDATION_THRESHOLD = 7.5
CHAPTER_THRESHOLD = 6.0
MAX_FOUNDATION_ITERS = 20
MAX_CHAPTER_ATTEMPTS = 5
MIN_REVISION_CYCLES = 3
MAX_REVISION_CYCLES = 6
PLATEAU_DELTA = 0.3

PHASE_ORDER = ["foundation", "drafting", "revision", "export"]


# ---------------------------------------------------------------------------
# Helpers: canon growth
# ---------------------------------------------------------------------------

def append_new_canon_entries(eval_stdout: str, chapter_num: int):
    """Parse new_canon_entries from evaluate output and append to canon.md."""
    # Try JSON-style: "new_canon_entries": ["fact1", "fact2"]
    entries_block = re.findall(
        r'"new_canon_entries"\s*:\s*\[(.*?)\]', eval_stdout, re.DOTALL)
    facts = []
    if entries_block:
        facts = re.findall(r'"(.*?)"', entries_block[0])
    
    # Try YAML-style: new_canon_entries:
    #   - fact1
    #   - fact2
    if not facts:
        in_block = False
        for line in eval_stdout.splitlines():
            stripped = line.strip()
            if stripped.startswith("new_canon_entries"):
                in_block = True
                continue
            if in_block:
                if stripped.startswith("- "):
                    fact = stripped[2:].strip().strip('"').strip("'")
                    if fact:
                        facts.append(fact)
                elif stripped and not stripped.startswith("#"):
                    break
    
    if not facts:
        return 0
    
    canon_path = BASE_DIR / "canon.md"
    existing = canon_path.read_text() if canon_path.exists() else ""
    new_section = f"\n\n## From Chapter {chapter_num}\n"
    for fact in facts:
        new_section += f"- {fact} (ch_{chapter_num:02d})\n"
    
    canon_path.write_text(existing + new_section)
    return len(facts)


def generate_chapter_summary(chapter_num: int) -> bool:
    """Generate a ~200 word summary of a chapter and save to summaries/."""
    ch_file = CHAPTERS_DIR / f"ch_{chapter_num:02d}.md"
    if not ch_file.exists():
        return False

    chapter_text = ch_file.read_text()
    if len(chapter_text.strip()) < 100:
        return False

    SUMMARIES_DIR.mkdir(exist_ok=True)

    # Use a lightweight LLM call to summarize
    from writer import call_writer
    from config import WRITER_MODEL, get_language, language_instruction

    if not API_KEY:
        # Fallback: use first 200 words
        summary = " ".join(chapter_text.split()[:200])
        out_path = SUMMARIES_DIR / f"summary_{chapter_num:02d}.md"
        out_path.write_text(summary)
        return True

    lang_note = ""
    if get_language() != "en":
        lang_note = " If the chapter is in Vietnamese, write the summary in Vietnamese."

    prompt = (
        f"Summarize this novel chapter in ~200 words. "
        f"Include: key events, character developments, emotional beats, "
        f"any important facts or reveals, and how the chapter ends."
        f"{lang_note}\n\n"
        f"CHAPTER:\n{chapter_text}"
    )

    system_prompt = (
        "You summarize novel chapters concisely for use as context "
        "when writing subsequent chapters. Focus on plot, character "
        "changes, and established facts."
        + language_instruction()
    )

    try:
        summary = call_writer(
            prompt, system=system_prompt, max_tokens=600,
            temperature=0.3, timeout=API_TIMEOUT)
    except Exception as e:
        step(f"Summary generation failed: {e}, using first 200 words")
        summary = " ".join(chapter_text.split()[:200])

    out_path = SUMMARIES_DIR / f"summary_{chapter_num:02d}.md"
    out_path.write_text(summary)
    return True


# ---------------------------------------------------------------------------
# Helpers: state management
# ---------------------------------------------------------------------------

def load_state() -> dict:
    """Load pipeline state from state.json, creating defaults if missing."""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return default_state()


def default_state() -> dict:
    return {
        "phase": "foundation",
        "current_focus": "planning",
        "iteration": 0,
        "foundation_score": 0.0,
        "lore_score": 0.0,
        "chapters_drafted": 0,
        "chapters_total": 0,
        "novel_score": 0.0,
        "revision_cycle": 0,
        "debts": [],
        "language": get_language(),
    }


def save_state(state: dict):
    """Write state to state.json."""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


# ---------------------------------------------------------------------------
# Helpers: logging
# ---------------------------------------------------------------------------

def log_result(commit: str, phase: str, score, word_count: int,
               status: str, description: str):
    """Append a row to results.tsv."""
    header = "commit\tphase\tscore\tword_count\tstatus\tdescription\n"
    if not RESULTS_FILE.exists():
        RESULTS_FILE.write_text(header)
    elif RESULTS_FILE.stat().st_size == 0:
        RESULTS_FILE.write_text(header)
    with open(RESULTS_FILE, "a") as f:
        f.write(f"{commit}\t{phase}\t{score}\t{word_count}\t{status}\t{description}\n")


def banner(text: str, char: str = "=", width: int = 60):
    """Print a visible phase/step banner."""
    print(f"\n{char * width}")
    print(f"  {text}")
    print(f"{char * width}")


def step(text: str):
    """Print a step indicator."""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"  [{ts}] {text}")


# ---------------------------------------------------------------------------
# Helpers: subprocess execution
# ---------------------------------------------------------------------------

def run_tool(cmd: str, timeout: int | None = None, check: bool = False) -> subprocess.CompletedProcess:
    """
    Run a tool as a subprocess, capturing output.
    Uses shell=True so callers can pass full command strings.
    Returns CompletedProcess; never raises unless check=True.
    
    Timeout defaults to SUBPROCESS_TIMEOUT * thinking scale factor,
    so LLM-heavy subprocesses get enough room when thinking mode is on.
    """
    effective_timeout = (timeout if timeout is not None
                         else SUBPROCESS_TIMEOUT * _THINKING_TIMEOUT_SCALE)
    step(f"RUN: {cmd}")
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=effective_timeout, cwd=str(BASE_DIR),
        )
        if result.returncode != 0:
            print(f"    WARN: exit code {result.returncode}")
            stderr_preview = (result.stderr or "")[:300]
            if stderr_preview:
                print(f"    stderr: {stderr_preview}")
        if check and result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode, cmd, result.stdout, result.stderr)
        return result
    except subprocess.TimeoutExpired:
        print(f"    ERROR: timed out after {timeout}s")
        # Return a fake CompletedProcess for graceful handling
        fake = subprocess.CompletedProcess(cmd, returncode=-1, stdout="", stderr="TIMEOUT")
        return fake


def uv_run(script: str, timeout: int = 600) -> subprocess.CompletedProcess:
    """Shorthand for 'uv run python <script>' from project root."""
    return run_tool(f"uv run python {script}", timeout=timeout)


# ---------------------------------------------------------------------------
# Helpers: git operations
# ---------------------------------------------------------------------------

def git_add_commit(message: str) -> str:
    """Stage all changes and commit. Returns short hash or empty string."""
    run_tool("git add -A")
    result = run_tool(f'git commit -m "{message}" --allow-empty')
    if result.returncode == 0:
        hash_result = run_tool("git rev-parse --short HEAD")
        commit_hash = hash_result.stdout.strip()
        step(f"GIT COMMIT: {commit_hash} — {message}")
        return commit_hash
    else:
        step("GIT: nothing to commit or commit failed")
        return ""


def git_reset_hard(ref: str = "HEAD~1"):
    """Hard reset to discard bad changes."""
    step(f"GIT RESET: {ref}")
    run_tool(f"git reset --hard {ref}")


def git_short_hash() -> str:
    """Get current HEAD short hash."""
    r = run_tool("git rev-parse --short HEAD")
    return r.stdout.strip() if r.returncode == 0 else "unknown"


# ---------------------------------------------------------------------------
# Helpers: score parsing
# ---------------------------------------------------------------------------

def parse_score(stdout: str, key: str = "overall_score") -> float:
    """
    Parse a score from evaluate.py YAML-like stdout output.
    Looks for lines like 'overall_score: 8.0' or 'novel_score: 7.5'.
    """
    for line in stdout.splitlines():
        line = line.strip()
        if line.startswith(f"{key}:"):
            val = line.split(":", 1)[1].strip()
            try:
                return float(val)
            except ValueError:
                continue
    return -1.0


def parse_lore_score(stdout: str) -> float:
    """Parse lore_score from foundation evaluation output."""
    return parse_score(stdout, "lore_score")


def parse_weakest_dimension(stdout: str) -> tuple:
    """Parse weakest dimension name and score from foundation eval output.
    Returns (dimension_name, score) or ("", -1) if not found."""
    # Look for "weakest_dimension: ..." in the eval output
    for line in stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("weakest_dimension:"):
            dim = stripped.split(":", 1)[1].strip().strip('"').strip("'")
            # Try to find the score for this dimension
            for l2 in stdout.splitlines():
                s2 = l2.strip()
                if s2.startswith(f"{dim}:") or s2.startswith(f'"{dim}"'):
                    score_match = re.search(r'(\d+\.?\d*)', s2)
                    if score_match:
                        return (dim, float(score_match.group(1)))
            return (dim, -1)
    return ("", -1)


def refine_foundation_doc(doc_name: str, doc_path: Path, weakest_info: str,
                          eval_stdout: str) -> bool:
    """Refine a single foundation document based on evaluation feedback.
    Uses the LLM to improve the weakest aspect while preserving the rest."""
    if not doc_path.exists():
        return False

    existing = doc_path.read_text()
    if not existing.strip():
        return False

    from writer import call_writer
    from config import API_KEY, get_language, language_instruction

    if not API_KEY:
        return False

    lang_note = ""
    if get_language() != "en":
        lang_note = " The document is in Vietnamese. Keep all Vietnamese text, only revise the content."

    prompt = (
        f"You are refining a {doc_name} for a fantasy novel. "
        f"The foundation evaluation scored it and found the weakest point:\n\n"
        f"{weakest_info}\n\n"
        f"Here is the evaluator's full feedback:\n"
        f"{eval_stdout[:3000]}\n\n"
        f"Here is the current {doc_name}:\n"
        f"---\n{existing}\n---\n\n"
        f"IMPROVE the weakest aspect while preserving everything else that works. "
        f"Do NOT regress on other dimensions. Output the COMPLETE revised document."
        f"{lang_note}"
    )

    system_prompt = (
        "You refine fantasy novel planning documents. You improve the "
        "weakest aspect identified by the evaluator while keeping "
        "everything that already works. You never use AI slop words. "
        "You output the complete revised document, not patches."
        + language_instruction()
    )

    try:
        revised = call_writer(
            prompt, system=system_prompt, max_tokens=16000,
            temperature=0.6, timeout=API_TIMEOUT)
        if revised.strip():
            doc_path.write_text(revised)
            return True
    except Exception as e:
        step(f"Refinement failed for {doc_name}: {e}")
    return False


def count_words_in_chapters() -> int:
    """Sum word count across all chapter files."""
    total = 0
    if CHAPTERS_DIR.exists():
        for f in CHAPTERS_DIR.glob("ch_*.md"):
            total += len(f.read_text().split())
    return total


def count_chapter_files() -> int:
    """Count the number of chapter files."""
    if not CHAPTERS_DIR.exists():
        return 0
    return len(list(CHAPTERS_DIR.glob("ch_*.md")))


def get_total_chapters(state: dict) -> int:
    """Determine total chapter count from state or outline."""
    if state.get("chapters_total", 0) > 0:
        return state["chapters_total"]
    # Try to infer from outline.md
    outline = BASE_DIR / "outline.md"
    if outline.exists():
        text = outline.read_text()
        matches = re.findall(r'###\s*Ch(?:apter)?\s*(\d+)', text)
        if matches:
            return max(int(m) for m in matches)
    return 24  # sensible default


# ---------------------------------------------------------------------------
# Helpers: mystery and voice generation
# ---------------------------------------------------------------------------

def _generate_mystery() -> str | None:
    """Generate MYSTERY.md content from seed + world + characters."""
    from writer import call_writer
    from config import API_KEY, get_language, language_instruction

    if not API_KEY:
        return None

    seed = (BASE_DIR / "seed.txt").read_text() if (BASE_DIR / "seed.txt").exists() else ""
    world = (BASE_DIR / "world.md").read_text() if (BASE_DIR / "world.md").exists() else ""
    characters = (BASE_DIR / "characters.md").read_text() if (BASE_DIR / "characters.md").exists() else ""

    prompt = f"""Define the CENTRAL MYSTERY for this fantasy novel. This is the secret
the reader discovers at the climax — the recontextualization that makes
everything before it mean something different.

SEED CONCEPT:
{seed}

WORLD BIBLE:
{world}

CHARACTER REGISTRY:
{characters}

The mystery MUST have:
- A question that can be asked in one sentence
- An answer that recontextualizes the entire story
- No simple right answer (moral ambiguity)
- A physical manifestation in the world (not just information)
- A choice the protagonist must make that has real cost

Format:
# THE CENTRAL MYSTERY
### Author's Eyes Only

## The Question
[One sentence question]

## The Answer
[What's really going on — the truth the reader discovers]

## The Recontextualization
[How knowing the answer changes everything before it]

## The Choice
[The impossible decision the protagonist faces at the climax]

## Clues to Plant
[List 5-8 specific clues that should be planted across the novel]

## Red Herrings
[2-3 misleading clues that point away from the truth]
"""

    system_prompt = (
        "You are a mystery architect for fantasy novels. You create central "
        "mysteries that are surprising, thematically resonant, and have real "
        "costs for the protagonist. The answer should recontextualize the "
        "entire story, not just add a twist."
        + language_instruction()
    )

    try:
        return call_writer(
            prompt, system=system_prompt, max_tokens=4000,
            temperature=0.7, timeout=API_TIMEOUT)
    except Exception as e:
        step(f"Mystery generation failed: {e}")
        return None


def _generate_voice_part2() -> str | None:
    """Generate voice.md Part 2 content from seed + world + characters."""
    from writer import call_writer
    from config import API_KEY, get_language, language_instruction

    if not API_KEY:
        return None

    seed = (BASE_DIR / "seed.txt").read_text() if (BASE_DIR / "seed.txt").exists() else ""
    world = (BASE_DIR / "world.md").read_text() if (BASE_DIR / "world.md").exists() else ""

    prompt = f"""Define the VOICE IDENTITY for this fantasy novel. This is Part 2 of voice.md —
the specific prose style for THIS story.

SEED CONCEPT:
{seed}

WORLD BIBLE:
{world}

Define the voice with these sections:

## Part 2: Voice Identity (novel-specific)

### Tone
[2-3 sentences on the overall tonal register — e.g., "spare and observational,
letting dread accumulate through what's not said"]

### Sentence Rhythm
[Describe the dominant rhythm — e.g., "Short declarative sentences for action.
Longer, perception-heavy sentences for stillness. Fragments for pain."]

### Vocabulary Wells
[Where does the metaphor language come from? List 2-3 domains specific to
this world — e.g., "music/sound", "metalwork", "botanical decay"]

### Body Before Emotion
[Rule: emotions arrive as physical sensation first. Give 3 examples of how
this novel's characters manifest feelings physically.]

### Dialogue Register
[How do people speak in this world? Register, formality, subtext level.
Give 2 example lines that demonstrate the voice.]

### What This Voice Does NOT Do
[3-5 anti-exemplars — things this specific voice avoids]

### Exemplar Passage
[Write a 100-150 word passage in this voice — a moment of the protagonist
noticing something wrong. This is the benchmark passage.]
"""

    system_prompt = (
        "You are a prose stylist defining a novel's voice. You write voice "
        "definitions that are specific, actionable, and emerge from the "
        "story's world and themes. The voice should be distinctive enough "
        "that a writer could reproduce it from this document alone."
        + language_instruction()
    )

    try:
        return call_writer(
            prompt, system=system_prompt, max_tokens=4000,
            temperature=0.7, timeout=API_TIMEOUT)
    except Exception as e:
        step(f"Voice Part 2 generation failed: {e}")
        return None


# ---------------------------------------------------------------------------
# PHASE 1 — FOUNDATION
# ---------------------------------------------------------------------------

def run_foundation(state: dict) -> dict:
    """
    Build planning documents (world, characters, outline, voice, canon).
    Iteration 1: generate from scratch. Iterations 2+: refine weakest.
    Loop until foundation_score > threshold or max iterations reached.
    """
    banner("PHASE 1: FOUNDATION", "=")

    best_score = state.get("foundation_score", 0.0)
    best_eval = ""
    iteration = state.get("iteration", 0)
    consecutive_eval_failures = 0

    for i in range(iteration + 1, MAX_FOUNDATION_ITERS + 1):
        banner(f"Foundation Iteration {i}", "-")
        state["iteration"] = i

        if i == 1 or (best_score == 0 and i <= 2):
            # First iteration (or second if first scored 0): generate from scratch

            # Generate voice.md Part 2 FIRST — other scripts consume it
            voice_path = BASE_DIR / "voice.md"
            voice_text = voice_path.read_text() if voice_path.exists() else ""
            if "Part 2" in voice_text:
                lines = voice_text.split('\n')
                part2_start = next(
                    (i for i, l in enumerate(lines) if 'Part 2' in l),
                    None,
                )
                if part2_start is not None:
                    part2 = '\n'.join(lines[part2_start:])
                    stripped = re.sub(
                        r'<!--.*?-->', '', part2, flags=re.DOTALL
                    ).strip()
                    if len(stripped) < 500:
                        step("Generating voice identity (voice.md Part 2)...")
                        r = _generate_voice_part2()
                        if r:
                            new_voice = (
                                '\n'.join(lines[:part2_start]) + '\n\n' + r
                            )
                            voice_path.write_text(new_voice)
                            step(
                                f"Updated voice.md Part 2 ({len(r)} chars)"
                            )
                        else:
                            step("WARNING: voice Part 2 generation failed — "
                                 "downstream scripts will run with incomplete voice identity")

            step("Generating world bible...")
            r = uv_run("gen_world.py", timeout=SUBPROCESS_TIMEOUT)
            if r.returncode == 0 and r.stdout.strip():
                path = BASE_DIR / "world.md"
                path.write_text(r.stdout)
                step(f"Saved {path.name} ({len(r.stdout)} chars)")
            else:
                step("WARNING: world bible generation failed or empty")

            step("Generating characters...")
            r = uv_run("gen_characters.py", timeout=SUBPROCESS_TIMEOUT)
            if r.returncode == 0 and r.stdout.strip():
                path = BASE_DIR / "characters.md"
                path.write_text(r.stdout)
                step(f"Saved {path.name} ({len(r.stdout)} chars)")
            else:
                step("WARNING: characters generation failed or empty")

            # Generate MYSTERY.md BEFORE outline — gen_outline.py reads it
            mystery_path = BASE_DIR / "MYSTERY.md"
            mystery_text = mystery_path.read_text() if mystery_path.exists() else ""
            if "<!--" in mystery_text or len(mystery_text.strip()) < 100:
                step("Generating central mystery (MYSTERY.md)...")
                r = _generate_mystery()
                if r:
                    mystery_path.write_text(r)
                    step(f"Saved MYSTERY.md ({len(r)} chars)")

            step("Generating outline (part 1)...")
            r = uv_run("gen_outline.py", timeout=SUBPROCESS_TIMEOUT)
            outline_ok = False
            if r.returncode == 0 and r.stdout.strip():
                path = BASE_DIR / "outline.md"
                path.write_text(r.stdout)
                Path("/tmp/outline_output.md").write_text(r.stdout)
                step(f"Saved {path.name} ({len(r.stdout)} chars)")
                outline_ok = True
            else:
                step("WARNING: outline part 1 generation failed or empty")

            if outline_ok:
                step("Generating outline (part 2 — foreshadowing)...")
                r = uv_run("gen_outline_part2.py", timeout=SUBPROCESS_TIMEOUT)
                if r.returncode == 0 and r.stdout.strip():
                    path = BASE_DIR / "outline.md"
                    existing = path.read_text() if path.exists() else ""
                    path.write_text(existing + "\n\n" + r.stdout)
                    step(f"Appended to {path.name} (+{len(r.stdout)} chars)")
                else:
                    step("WARNING: outline part 2 generation failed or empty")

            step("Generating canon...")
            r = uv_run("gen_canon.py", timeout=SUBPROCESS_TIMEOUT)
            if r.returncode == 0 and r.stdout.strip():
                path = BASE_DIR / "canon.md"
                path.write_text(r.stdout)
                step(f"Saved {path.name} ({len(r.stdout)} chars)")
            else:
                step("WARNING: canon generation failed or empty")

        else:
            # Iterations 2+: refine the weakest dimension instead of regenerating
            weakest_dim, weakest_score = parse_weakest_dimension(best_eval)
            if weakest_dim:
                step(f"Refining weakest dimension: {weakest_dim} (score: {weakest_score})")
                # Map dimension to the most relevant document
                dim_to_doc = {
                    "world_depth": "world.md",
                    "magic_system": "world.md",
                    "lore_integration": "world.md",
                    "geography": "world.md",
                    "history": "world.md",
                    "character_depth": "characters.md",
                    "character_voice": "characters.md",
                    "character_arcs": "characters.md",
                    "outline_completeness": "outline.md",
                    "beat_structure": "outline.md",
                    "foreshadowing_balance": "outline.md",
                    "pacing_plan": "outline.md",
                    "voice_definition": "voice.md",
                    "voice_clarity": "voice.md",
                    "internal_consistency": "canon.md",
                    "canon_coverage": "canon.md",
                }
                target_file = dim_to_doc.get(weakest_dim, "world.md")
                target_path = BASE_DIR / target_file
                step(f"Refining {target_file} to improve {weakest_dim}...")
                refined = refine_foundation_doc(
                    target_file, target_path,
                    f"Weakest dimension: {weakest_dim} (score: {weakest_score})",
                    best_eval)
                if refined:
                    step(f"Refined {target_file}")
                    # Regenerate canon if world or characters changed
                    if target_file in ("world.md", "characters.md"):
                        step("Regenerating canon after changes...")
                        rc = uv_run("gen_canon.py", timeout=SUBPROCESS_TIMEOUT)
                        if rc.returncode == 0 and rc.stdout.strip():
                            (BASE_DIR / "canon.md").write_text(rc.stdout)
                else:
                    step(f"Refinement failed, falling back to full regeneration")
                    # Fall back to regenerating just the weakest doc's source
                    if target_file == "world.md":
                        r = uv_run("gen_world.py", timeout=SUBPROCESS_TIMEOUT)
                        if r.returncode == 0 and r.stdout.strip():
                            (BASE_DIR / "world.md").write_text(r.stdout)
                    elif target_file == "characters.md":
                        r = uv_run("gen_characters.py", timeout=SUBPROCESS_TIMEOUT)
                        if r.returncode == 0 and r.stdout.strip():
                            (BASE_DIR / "characters.md").write_text(r.stdout)
            else:
                step("No weakest dimension found, running full regeneration")
                r = uv_run("gen_world.py", timeout=SUBPROCESS_TIMEOUT)
                if r.returncode == 0 and r.stdout.strip():
                    (BASE_DIR / "world.md").write_text(r.stdout)
                r = uv_run("gen_characters.py", timeout=SUBPROCESS_TIMEOUT)
                if r.returncode == 0 and r.stdout.strip():
                    (BASE_DIR / "characters.md").write_text(r.stdout)
                r = uv_run("gen_outline.py", timeout=SUBPROCESS_TIMEOUT)
                outline_ok = False
                if r.returncode == 0 and r.stdout.strip():
                    (BASE_DIR / "outline.md").write_text(r.stdout)
                    Path("/tmp/outline_output.md").write_text(r.stdout)
                    outline_ok = True
                if outline_ok:
                    r = uv_run("gen_outline_part2.py", timeout=SUBPROCESS_TIMEOUT)
                    if r.returncode == 0 and r.stdout.strip():
                        path = BASE_DIR / "outline.md"
                        existing = path.read_text() if path.exists() else ""
                        path.write_text(existing + "\n\n" + r.stdout)
                r = uv_run("gen_canon.py", timeout=SUBPROCESS_TIMEOUT)
                if r.returncode == 0 and r.stdout.strip():
                    (BASE_DIR / "canon.md").write_text(r.stdout)

        # 2. Evaluate
        step("Evaluating foundation...")
        eval_result = uv_run("evaluate.py --phase=foundation", timeout=SUBPROCESS_TIMEOUT)
        score = parse_score(eval_result.stdout, "overall_score")
        lore = parse_lore_score(eval_result.stdout)

        step(f"Foundation score: {score}  (lore: {lore}, prev best: {best_score})")

        # Handle unparseable eval scores (API errors, malformed responses)
        if score < 0:
            consecutive_eval_failures += 1
            step(f"WARNING: eval returned unparseable score "
                 f"({consecutive_eval_failures} consecutive failures)")
            if consecutive_eval_failures >= 3:
                step("ERROR: 3 consecutive eval failures — "
                     "keeping generated docs and moving on")
                if best_score == 0:
                    best_score = 0.1  # Set minimal score to allow progress
                    state["foundation_score"] = best_score
                    save_state(state)
                break
            # Still commit the generated docs so we don't lose them
            commit_hash = git_add_commit(
                f"foundation iter {i}: eval parse failure, keeping docs")
            continue

        consecutive_eval_failures = 0  # Reset on successful parse

        # 3. Keep or discard
        if score > best_score:
            best_eval = eval_result.stdout  # save for refinement next iter
            commit_hash = git_add_commit(
                f"foundation iter {i}: score {score} (lore {lore})")
            log_result(commit_hash, "foundation", score, 0, "keep",
                       f"Iteration {i}: score improved {best_score} -> {score}")
            best_score = score
            state["foundation_score"] = score
            state["lore_score"] = lore
            save_state(state)
        else:
            step(f"Score did not improve ({score} <= {best_score}), discarding")
            # Keep best_eval from previous iteration for refinement context
            git_reset_hard("HEAD")
            log_result("discarded", "foundation", score, 0, "discard",
                       f"Iteration {i}: no improvement ({score} <= {best_score})")

        # 4. Check exit condition
        if best_score >= FOUNDATION_THRESHOLD:
            step(f"Foundation score {best_score} >= {FOUNDATION_THRESHOLD} — PASSED")
            break
    else:
        step(f"WARNING: max iterations ({MAX_FOUNDATION_ITERS}) reached "
             f"with score {best_score}")

    # Determine total chapters from outline
    total = get_total_chapters(state)
    state["chapters_total"] = total
    state["phase"] = "drafting"
    state["current_focus"] = "chapter_drafting"
    save_state(state)

    banner(f"FOUNDATION COMPLETE — score {best_score}, {total} chapters planned")
    return state


# ---------------------------------------------------------------------------
# PHASE 2 — DRAFTING
# ---------------------------------------------------------------------------

def run_drafting(state: dict) -> dict:
    """
    Draft each chapter sequentially, evaluating and retrying as needed.
    """
    banner("PHASE 2: DRAFTING", "=")

    total = get_total_chapters(state)
    start_chapter = state.get("chapters_drafted", 0) + 1

    CHAPTERS_DIR.mkdir(exist_ok=True)

    for ch in range(start_chapter, total + 1):
        banner(f"Drafting Chapter {ch}/{total}", "-")
        drafted = False
        eval_result = None  # track last eval for force-keep path

        for attempt in range(1, MAX_CHAPTER_ATTEMPTS + 1):
            step(f"Attempt {attempt}/{MAX_CHAPTER_ATTEMPTS}")

            # Draft
            draft_result = uv_run(f"draft_chapter.py {ch}", timeout=SUBPROCESS_TIMEOUT)
            if draft_result.returncode != 0:
                step(f"Draft failed (exit {draft_result.returncode}), retrying...")
                continue

            # Check the chapter file exists and has content
            ch_file = CHAPTERS_DIR / f"ch_{ch:02d}.md"
            if not ch_file.exists() or ch_file.stat().st_size < 100:
                step("Chapter file missing or too short, retrying...")
                continue

            word_count = len(ch_file.read_text().split())
            step(f"Drafted {word_count} words")

            # Evaluate
            eval_result = uv_run(f"evaluate.py --chapter={ch}", timeout=SUBPROCESS_TIMEOUT)
            score = parse_score(eval_result.stdout, "overall_score")
            step(f"Chapter {ch} score: {score}")

            if score >= CHAPTER_THRESHOLD:
                # Grow canon with new facts from this chapter
                n_facts = append_new_canon_entries(eval_result.stdout, ch)
                if n_facts:
                    step(f"Added {n_facts} new facts to canon.md")
                # Generate chapter summary for future context
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
                log_result("discarded", f"ch{ch:02d}", score, word_count,
                           "discard", f"Chapter {ch} attempt {attempt}")
                # Remove the bad chapter file so next attempt starts fresh
                if ch_file.exists():
                    run_tool(f"git checkout -- chapters/ch_{ch:02d}.md 2>/dev/null || true")

        if not drafted:
            step(f"WARNING: Chapter {ch} failed all {MAX_CHAPTER_ATTEMPTS} attempts, "
                 f"keeping last attempt and moving on")
            # Keep whatever we have and commit it
            ch_file = CHAPTERS_DIR / f"ch_{ch:02d}.md"
            if ch_file.exists():
                # Try to grow canon even from force-kept chapters
                if eval_result is not None:
                    n_facts = append_new_canon_entries(eval_result.stdout, ch)
                    if n_facts:
                        step(f"Added {n_facts} new facts to canon.md (force-kept chapter)")
                generate_chapter_summary(ch)
                word_count = len(ch_file.read_text().split())
                commit_hash = git_add_commit(
                    f"ch{ch:02d}: best-effort after {MAX_CHAPTER_ATTEMPTS} attempts")
                log_result(commit_hash, f"ch{ch:02d}", "?", word_count,
                           "forced", f"Chapter {ch}: kept after max attempts")
                state["chapters_drafted"] = ch
                save_state(state)

    # All chapters drafted
    state["phase"] = "revision"
    state["current_focus"] = "full_novel"
    state["chapters_drafted"] = total
    state["revision_cycle"] = 0
    save_state(state)

    total_words = count_words_in_chapters()
    step("Running voice fingerprint across all chapters...")
    uv_run("voice_fingerprint.py", timeout=SUBPROCESS_TIMEOUT)
    banner(f"DRAFTING COMPLETE — {total} chapters, {total_words} words")
    return state


# ---------------------------------------------------------------------------
# PHASE 3 — REVISION
# ---------------------------------------------------------------------------

def parse_panel_consensus(panel_path: Path) -> list[dict]:
    """
    Parse reader_panel.json to find chapters with consensus issues.
    Returns list of dicts: {chapter, question, flagged_by, details}
    sorted by number of readers who flagged (descending).
    """
    if not panel_path.exists():
        return []
    with open(panel_path) as f:
        data = json.load(f)

    items = []

    # Look at disagreements — these are flagged by some but not all readers
    for d in data.get("disagreements", []):
        items.append({
            "chapter": d.get("chapter", 0),
            "question": d.get("question", ""),
            "flagged_by": d.get("flagged_by", []),
            "count": len(d.get("flagged_by", [])),
        })

    # Also scan readers for direct chapter mentions in key questions
    readers = data.get("readers", {})
    chapter_mentions = {}  # ch_num -> count of readers mentioning it

    for reader_key, answers in readers.items():
        for question in ["momentum_loss", "cut_candidate", "worst_scene",
                         "thinnest_character", "missing_scene"]:
            answer = answers.get(question, "")
            if not isinstance(answer, str):
                continue
            chs = re.findall(r'Ch(?:apter)?\s*(\d+)', answer, re.IGNORECASE)
            for ch_str in chs:
                ch_num = int(ch_str)
                key = (ch_num, question)
                if key not in chapter_mentions:
                    chapter_mentions[key] = {"chapter": ch_num, "question": question,
                                             "flagged_by": [], "count": 0}
                chapter_mentions[key]["flagged_by"].append(reader_key)
                chapter_mentions[key]["count"] += 1

    # Merge and deduplicate
    seen = set()
    for item in items:
        seen.add((item["chapter"], item["question"]))
    for key, item in chapter_mentions.items():
        if key not in seen:
            items.append(item)

    # Sort by count descending, take unique chapters
    items.sort(key=lambda x: -x["count"])

    # Deduplicate by chapter (keep highest-count issue per chapter)
    seen_chapters = set()
    unique = []
    for item in items:
        if item["chapter"] not in seen_chapters and item["chapter"] > 0:
            seen_chapters.add(item["chapter"])
            unique.append(item)

    return unique[:5]  # top 3-5 consensus items


def run_revision(state: dict, max_cycles: int = MAX_REVISION_CYCLES) -> dict:
    """
    Revision phase: reader panel → targeted adversarial edit → revise flagged
    chapters → full novel eval. Merges the old Phase 3 + Phase 3b into one
    loop. A single Opus review.py call runs at the end as a final quality check.
    """
    banner("PHASE 3: REVISION", "=")

    BRIEFS_DIR.mkdir(exist_ok=True)
    EDIT_LOGS_DIR.mkdir(exist_ok=True)

    prev_score = state.get("novel_score", 0.0)
    start_cycle = state.get("revision_cycle", 0) + 1
    max_cycles = min(max_cycles, MAX_REVISION_CYCLES)

    for cycle in range(start_cycle, max_cycles + 1):
        banner(f"Revision Cycle {cycle}/{max_cycles}", "-")

        # -- Step 1: Build arc summary (required by reader panel) --
        arc_summary_path = BASE_DIR / "arc_summary.md"
        build_arc = BASE_DIR / "build_arc_summary.py"
        if build_arc.exists() and not arc_summary_path.exists():
            step("Building arc summary for reader panel...")
            uv_run("build_arc_summary.py", timeout=SUBPROCESS_TIMEOUT)

        # -- Step 2: Reader panel --
        reader_panel_py = BASE_DIR / "reader_panel.py"
        if not arc_summary_path.exists() or not reader_panel_py.exists():
            step("WARNING: arc_summary.md or reader_panel.py missing, "
                 "skipping reader panel")
            consensus_items = []
        else:
            step("Running reader panel evaluation...")
            uv_run("reader_panel.py", timeout=SUBPROCESS_TIMEOUT)

            # -- Step 3: Parse panel consensus --
            panel_path = EDIT_LOGS_DIR / "reader_panel.json"
            consensus_items = parse_panel_consensus(panel_path)

            if consensus_items:
                step(f"Found {len(consensus_items)} consensus items:")
                for item in consensus_items:
                    print(f"    Ch {item['chapter']}: {item['question']} "
                          f"(flagged by {item['count']} readers)")
            else:
                step("No strong consensus items found from panel")

        # -- Step 4: Targeted adversarial edit (flagged chapters only) --
        for item in consensus_items:
            ch_num = item["chapter"]
            step(f"Running adversarial edit on Ch {ch_num}...")
            uv_run(f"adversarial_edit.py {ch_num}", timeout=SUBPROCESS_TIMEOUT)

        # -- Step 5: Revise flagged chapters (brief → rewrite → eval → keep/revert) --
        for idx, item in enumerate(consensus_items):
            ch_num = item["chapter"]
            question = item["question"]
            banner(f"  Revising Ch {ch_num} ({question}) [{idx+1}/{len(consensus_items)}]", ".")

            # Snapshot the current chapter score for comparison
            pre_eval = uv_run(f"evaluate.py --chapter={ch_num}", timeout=SUBPROCESS_TIMEOUT)
            pre_score = parse_score(pre_eval.stdout, "overall_score")

            # Generate revision brief
            brief_file = BRIEFS_DIR / f"ch{ch_num:02d}_cycle{cycle}_{question}.md"
            gen_brief = BASE_DIR / "gen_brief.py"
            if gen_brief.exists():
                step(f"Generating brief for Ch {ch_num}...")
                run_tool(f"uv run python gen_brief.py --panel {ch_num}", timeout=SUBPROCESS_TIMEOUT)
                # gen_brief.py may write to briefs/ — find the most recent brief
                brief_candidates = sorted(
                    BRIEFS_DIR.glob(f"ch{ch_num:02d}*.md"),
                    key=lambda p: p.stat().st_mtime, reverse=True)
                if brief_candidates:
                    brief_file = brief_candidates[0]
            else:
                # Create a minimal brief from the panel data
                step(f"gen_brief.py not found, creating minimal brief for Ch {ch_num}...")
                brief_content = (
                    f"# Revision Brief: Chapter {ch_num}\n\n"
                    f"## Issue: {question}\n\n"
                    f"Panel consensus identified this chapter for revision.\n"
                    f"Focus: address the {question.replace('_', ' ')} issue.\n"
                    f"Preserve existing voice, character work, and essential beats.\n"
                )
                brief_file.write_text(brief_content)

            if not brief_file.exists():
                step(f"No brief file found for Ch {ch_num}, skipping")
                continue

            # Run revision
            step(f"Revising Ch {ch_num} with brief {brief_file.name}...")
            uv_run(f"gen_revision.py {ch_num} {brief_file}", timeout=SUBPROCESS_TIMEOUT)

            # Evaluate revised chapter
            post_eval = uv_run(f"evaluate.py --chapter={ch_num}", timeout=SUBPROCESS_TIMEOUT)
            post_score = parse_score(post_eval.stdout, "overall_score")

            ch_file = CHAPTERS_DIR / f"ch_{ch_num:02d}.md"
            word_count = len(ch_file.read_text().split()) if ch_file.exists() else 0

            step(f"Ch {ch_num}: {pre_score} -> {post_score}")

            if post_score >= pre_score:
                commit_hash = git_add_commit(
                    f"revision cycle {cycle}: ch{ch_num:02d} "
                    f"{question} {pre_score}->{post_score}")
                log_result(commit_hash, f"rev-ch{ch_num:02d}", post_score,
                           word_count, "keep",
                           f"Cycle {cycle}: {question} improved {pre_score}->{post_score}")
            else:
                step(f"Revision made it worse ({post_score} < {pre_score}), reverting")
                git_reset_hard("HEAD")
                log_result("reverted", f"rev-ch{ch_num:02d}", post_score,
                           word_count, "discard",
                           f"Cycle {cycle}: {question} regressed {pre_score}->{post_score}")

        # -- Step 6: Full novel evaluation --
        step("Running full novel evaluation...")
        full_eval = uv_run("evaluate.py --full", timeout=SUBPROCESS_TIMEOUT)
        novel_score = parse_score(full_eval.stdout, "novel_score")

        if novel_score < 0:
            # Fallback: try overall_score
            novel_score = parse_score(full_eval.stdout, "overall_score")

        total_words = count_words_in_chapters()
        step(f"Novel score: {novel_score}  (prev: {prev_score}, words: {total_words})")

        # Commit cycle results
        commit_hash = git_add_commit(
            f"revision cycle {cycle} complete: novel_score {novel_score}")
        log_result(commit_hash, f"revision-cycle-{cycle}", novel_score,
                   total_words, "cycle",
                   f"Cycle {cycle}: novel_score {prev_score}->{novel_score}")

        state["novel_score"] = novel_score
        state["revision_cycle"] = cycle
        save_state(state)

        # -- Step 7: Plateau detection --
        if cycle >= MIN_REVISION_CYCLES and abs(novel_score - prev_score) < PLATEAU_DELTA:
            step(f"Plateau detected (delta {abs(novel_score - prev_score):.2f} "
                 f"< {PLATEAU_DELTA}) after {cycle} cycles — stopping")
            break

        prev_score = novel_score

    # =========================================================
    # FINAL QUALITY CHECK: single Opus review
    # =========================================================
    review_py = BASE_DIR / "review.py"
    if review_py.exists():
        banner("FINAL QUALITY CHECK: Opus Review", "=")

        step("Sending manuscript to Opus for final review...")
        review_result = uv_run("review.py --output reviews.md", timeout=SUBPROCESS_TIMEOUT)

        # Parse the review
        step("Parsing review...")
        parse_result = run_tool("uv run python review.py --parse", timeout=SUBPROCESS_TIMEOUT)
        print(parse_result.stdout if parse_result else "")

        # Check star rating and flag for user if needed
        review_logs = sorted(
            (EDIT_LOGS_DIR).glob("*_review.json"), reverse=True)
        if review_logs:
            review_data = json.loads(review_logs[0].read_text())
            stars = review_data.get("stars", 0) or 0
            total_items = review_data.get("total_items", 0)
            major_items = review_data.get("major_items", 0)

            step(f"Final review: {stars} stars, {total_items} items "
                 f"({major_items} major)")

            if stars < 4 or major_items > 0:
                step("NOTE: Final review flags issues. "
                     "Check reviews.md for details — manual review recommended.")

        git_add_commit("final quality check: Opus review")

    state["phase"] = "export"
    state["current_focus"] = "export"
    save_state(state)

    banner(f"REVISION COMPLETE — {state.get('revision_cycle', 0)} cycles, "
           f"novel_score {state.get('novel_score', 0)}")
    return state


# ---------------------------------------------------------------------------
# PHASE 4 — EXPORT
# ---------------------------------------------------------------------------

def run_export(state: dict) -> dict:
    """
    Build final deliverables: outline, arc summary, manuscript, PDF.
    """
    banner("PHASE 4: EXPORT", "=")

    # 1. Rebuild outline from chapters
    build_outline = BASE_DIR / "build_outline.py"
    if build_outline.exists():
        step("Rebuilding outline from chapters...")
        uv_run("build_outline.py", timeout=SUBPROCESS_TIMEOUT)

    # 2. Build arc summary
    build_arc = BASE_DIR / "build_arc_summary.py"
    if build_arc.exists():
        step("Building arc summary...")
        uv_run("build_arc_summary.py", timeout=SUBPROCESS_TIMEOUT)

    # 3. Concatenate chapters into manuscript.md
    step("Building manuscript.md...")
    manuscript = BASE_DIR / "manuscript.md"
    chapter_files = sorted(CHAPTERS_DIR.glob("ch_*.md"))

    parts = []
    for ch_file in chapter_files:
        text = ch_file.read_text().strip()
        if text:
            parts.append(text)

    if parts:
        manuscript.write_text("\n\n---\n\n".join(parts) + "\n")
        word_count = sum(len(p.split()) for p in parts)
        step(f"Manuscript: {len(parts)} chapters, {word_count} words")
    else:
        step("WARNING: no chapter files found for manuscript")

    # 4. Build LaTeX
    build_tex = BASE_DIR / "typeset" / "build_tex.py"
    if build_tex.exists():
        step("Building LaTeX content...")
        run_tool(f"uv run python typeset/build_tex.py", timeout=SUBPROCESS_TIMEOUT)

        # 5. Typeset with tectonic (if available)
        novel_tex = BASE_DIR / "typeset" / "novel.tex"
        if novel_tex.exists():
            tectonic_check = run_tool("which tectonic", timeout=10)
            if tectonic_check.returncode == 0:
                step("Typesetting PDF with tectonic...")
                result = run_tool("tectonic typeset/novel.tex", timeout=SUBPROCESS_TIMEOUT)
                if result.returncode == 0:
                    step("PDF generated: typeset/novel.pdf")
                else:
                    step("WARNING: tectonic typesetting failed")
            else:
                step("tectonic not found, skipping PDF generation")
    else:
        step("typeset/build_tex.py not found, skipping LaTeX")

    # 6. Final commit
    commit_hash = git_add_commit("export: manuscript, outline, arc summary, PDF")
    total_words = count_words_in_chapters()
    log_result(commit_hash, "export", state.get("novel_score", "?"),
               total_words, "export", "Final export")

    state["phase"] = "complete"
    state["current_focus"] = "done"
    save_state(state)

    banner(f"EXPORT COMPLETE — {len(chapter_files)} chapters, {total_words} words")
    return state


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def run_pipeline(args):
    """Run the full pipeline or a specific phase."""

    # Load or initialize state
    if args.from_scratch:
        banner("STARTING FROM SCRATCH")
        seed_file = BASE_DIR / "seed.txt"
        if not seed_file.exists():
            print("ERROR: seed.txt not found. Cannot start from scratch without a seed.")
            sys.exit(1)
        # Clean old generated artifacts so the pipeline starts truly fresh
        for artifact in [
            "world.md", "characters.md", "outline.md", "canon.md",
            "manuscript.md", "arc_summary.md", "MYSTERY.md",
        ]:
            p = BASE_DIR / artifact
            if p.exists() or p.is_symlink():
                p.unlink()
                step(f"Removed old {artifact}")
        # Clean chapter files
        if CHAPTERS_DIR.exists():
            for ch in CHAPTERS_DIR.glob("ch_*.md"):
                ch.unlink()
        # Clean generated logs and briefs
        for dir_path in [BRIEFS_DIR, EDIT_LOGS_DIR, EVAL_LOGS_DIR, SUMMARIES_DIR]:
            if dir_path.exists():
                for f in dir_path.iterdir():
                    if f.is_file():
                        f.unlink()
        # Clean temp outline
        tmp_outline = Path("/tmp/outline_output.md")
        if tmp_outline.exists():
            tmp_outline.unlink()
        state = default_state()
        save_state(state)
    else:
        state = load_state()

    # Ensure directories exist
    CHAPTERS_DIR.mkdir(exist_ok=True)
    BRIEFS_DIR.mkdir(exist_ok=True)
    EDIT_LOGS_DIR.mkdir(exist_ok=True)
    EVAL_LOGS_DIR.mkdir(exist_ok=True)

    # Apply max_cycles override
    max_cycles = args.max_cycles if args.max_cycles else MAX_REVISION_CYCLES

    # Determine which phases to run
    if args.phase:
        # Single phase mode
        phases = [args.phase]
    else:
        # Run from current state onward
        current = state.get("phase", "foundation")
        if current == "complete":
            print("Pipeline already complete. Use --from-scratch to restart "
                  "or --phase to run a specific phase.")
            return
        try:
            start_idx = PHASE_ORDER.index(current)
        except ValueError:
            start_idx = 0
        phases = PHASE_ORDER[start_idx:]

    banner(f"AUTONOVEL PIPELINE — phases: {', '.join(phases)}")
    print(f"  State: phase={state.get('phase')}, "
          f"foundation_score={state.get('foundation_score', 0)}, "
          f"chapters={state.get('chapters_drafted', 0)}/{state.get('chapters_total', '?')}, "
          f"novel_score={state.get('novel_score', 0)}")

    start_time = datetime.now()

    for phase in phases:
        try:
            if phase == "foundation":
                state = run_foundation(state)
            elif phase == "drafting":
                state = run_drafting(state)
            elif phase == "revision":
                state = run_revision(state, max_cycles=max_cycles)
            elif phase == "export":
                state = run_export(state)
            else:
                print(f"Unknown phase: {phase}")
                sys.exit(1)
        except KeyboardInterrupt:
            banner("INTERRUPTED — state saved")
            save_state(state)
            sys.exit(130)
        except Exception as e:
            print(f"\n  FATAL ERROR in {phase}: {e}")
            save_state(state)
            raise

    elapsed = datetime.now() - start_time
    hours = elapsed.total_seconds() / 3600

    banner("PIPELINE COMPLETE")
    print(f"  Time:       {hours:.1f} hours")
    print(f"  Phase:      {state.get('phase')}")
    print(f"  Foundation: {state.get('foundation_score', 0)}")
    print(f"  Chapters:   {state.get('chapters_drafted', 0)}/{state.get('chapters_total', '?')}")
    print(f"  Words:      {count_words_in_chapters()}")
    print(f"  Novel:      {state.get('novel_score', 0)}")
    print(f"  Cycles:     {state.get('revision_cycle', 0)}")


def main():
    parser = argparse.ArgumentParser(
        description="Autonovel pipeline orchestrator — seed to finished novel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python run_pipeline.py                     # resume from current state
  python run_pipeline.py --from-scratch      # start fresh from seed.txt
  python run_pipeline.py --phase foundation  # run only foundation
  python run_pipeline.py --phase drafting    # run only drafting
  python run_pipeline.py --phase revision    # run only revision
  python run_pipeline.py --phase export      # run only export
  python run_pipeline.py --max-cycles 4      # limit revision to 4 cycles
""")

    parser.add_argument(
        "--from-scratch", action="store_true",
        help="Reset state and start from seed.txt")
    parser.add_argument(
        "--phase", choices=PHASE_ORDER,
        help="Run only a specific phase")
    parser.add_argument(
        "--max-cycles", type=int, default=None,
        help=f"Maximum revision cycles (default: {MAX_REVISION_CYCLES})")

    args = parser.parse_args()
    run_pipeline(args)


if __name__ == "__main__":
    main()
