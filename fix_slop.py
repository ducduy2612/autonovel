#!/usr/bin/env python3
"""
Surgical slop fixer — reads the latest eval log for a chapter,
sends only the flagged problems to the LLM, patches the chapter in-place.

Does NOT rewrite the whole chapter. Only replaces specific sentences.

Usage: uv run python fix_slop.py 1
"""
import json
import re
import sys
from pathlib import Path

from writer import call_writer
from config import language_instruction, BASE_DIR, CHAPTERS_DIR

CHAPTER_NUM = int(sys.argv[1])
CHAPTER_FILE = CHAPTERS_DIR / f"ch_{CHAPTER_NUM:02d}.md"

# --- Find latest eval log for this chapter ---
eval_logs = sorted(
    Path(BASE_DIR / "eval_logs").glob(f"*_ch{CHAPTER_NUM:02d}.json"),
    key=lambda p: p.stat().st_mtime,
)
if not eval_logs:
    print(f"No eval log found for chapter {CHAPTER_NUM}")
    sys.exit(1)

eval_log = json.loads(eval_logs[-1].read_text())
score = eval_log.get("overall_score", 0)
slop = eval_log.get("slop", {})
penalty = slop.get("slop_penalty", 0)

print(f"Chapter {CHAPTER_NUM}: score {score}, slop penalty {penalty}")

if penalty == 0:
    print("No slop to fix.")
    sys.exit(0)

# --- Collect all flagged problems from the eval ---
problems = []

# Weakest sentences
for s in eval_log.get("three_weakest_sentences", []):
    if s.strip():
        problems.append({"sentence": s.strip(), "context": "weakest sentence"})

# Dimension-level fixes
for dim in ["voice_adherence", "prose_quality", "character_voice",
            "engagement", "lore_integration", "plants_seeded"]:
    entry = eval_log.get(dim, {})
    if not isinstance(entry, dict):
        continue
    weakest = entry.get("weakest_moment", "").strip()
    fix = entry.get("fix", "").strip()
    if weakest and len(weakest) > 20:
        problems.append({
            "sentence": weakest,
            "suggested_fix": fix,
            "context": dim,
        })

# Canon violations
for v in eval_log.get("canon_compliance", {}).get("violations", []):
    if isinstance(v, str) and len(v) > 10:
        problems.append({"violation": v, "context": "canon_compliance"})

if not problems:
    print("No specific problems found to fix.")
    sys.exit(0)

print(f"Found {len(problems)} flagged issues to fix.")

# --- Read current chapter ---
chapter_text = CHAPTER_FILE.read_text()

# --- Build fix prompt ---
problem_list = ""
for i, p in enumerate(problems, 1):
    problem_list += f"\n{i}. "
    if "sentence" in p:
        problem_list += f"Sentence: \"{p['sentence']}\"\n"
        if p.get("suggested_fix"):
            problem_list += f"   Suggested fix: {p['suggested_fix']}\n"
        problem_list += f"   Context: {p.get('context', '')}\n"
    elif "violation" in p:
        problem_list += f"Violation: {p['violation']}\n"

system = (
    "You are a surgical prose editor. You fix specific problems in Vietnamese "
    "literary fiction. You output ONLY a JSON list of replacements. Each entry "
    "has 'old' (exact text to find) and 'new' (replacement text). "
    "No explanation, no markdown, just the JSON array. "
    "Keep the same style, tone, and register. Do NOT change anything else."
    + language_instruction()
)

prompt = f"""Fix these specific problems in chapter {CHAPTER_NUM}. 
Output a JSON array of {{"old": "...", "new": "..."}} replacements.
The 'old' must be an EXACT substring from the original text.
The 'new' should fix the specific problem and nothing else.

PROBLEMS TO FIX:
{problem_list}

ORIGINAL CHAPTER (for context, do not rewrite it):
{chapter_text[:6000]}

Output ONLY the JSON array of replacements. Example:
[{{"old": "beside cô", "new": "cạnh cô"}}]
"""

print("Calling LLM for fixes...")
result = call_writer(prompt, system=system, max_tokens=2000, temperature=0.3)

# Parse the replacements
result = result.strip()
if result.startswith("```"):
    result = re.sub(r'^```\w*\n?', '', result)
    result = re.sub(r'\n?```$', '', result)
    result = result.strip()

try:
    replacements = json.loads(result)
except json.JSONDecodeError:
    # Try to extract JSON array from the response
    match = re.search(r'\[.*\]', result, re.DOTALL)
    if match:
        replacements = json.loads(match.group())
    else:
        print(f"Could not parse replacements. Raw output:\n{result}")
        sys.exit(1)

# --- Apply replacements ---
applied = 0
for r in replacements:
    old = r.get("old", "")
    new = r.get("new", "")
    if not old:
        continue
    if old in chapter_text:
        chapter_text = chapter_text.replace(old, new, 1)
        applied += 1
        print(f"  Fixed: \"{old[:60]}...\" → \"{new[:60]}...\"")
    else:
        print(f"  SKIP (not found): \"{old[:60]}...\"")

if applied > 0:
    CHAPTER_FILE.write_text(chapter_text)
    print(f"\nApplied {applied} fixes to {CHAPTER_FILE.name}")
else:
    print("\nNo fixes applied — old text not found in chapter")
