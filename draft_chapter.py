#!/usr/bin/env python3
"""
Draft a single chapter using the writer model.
Usage: python draft_chapter.py 1
"""
import re
import sys
from pathlib import Path

from config import language_instruction, BASE_DIR, CHAPTERS_DIR
from writer import call_writer

_SYSTEM = (
    "You are a literary fiction writer drafting a fantasy novel chapter. "
    "You write in third-person limited past tense, locked to one POV character. "
    "You follow the voice definition exactly. You hit every beat in the outline. "
    "You never use words from the banned list. You show, never tell emotions. "
    "Your prose is specific, sensory, grounded. Metaphors come from the character's "
    "experience. You vary sentence length. You trust the reader. "
    "You write the FULL chapter -- do not truncate, summarize, or skip ahead."
    + language_instruction()
)

def _call_writer(prompt, max_tokens=16000):
    return call_writer(prompt, system=_SYSTEM, max_tokens=max_tokens,
                       temperature=0.8, timeout=None, use_beta=True)

def load_file(path):
    try:
        return Path(path).read_text()
    except FileNotFoundError:
        return ""

def extract_chapter_outline(outline_text, chapter_num):
    """Extract a specific chapter's outline entry."""
    pattern = rf'### Ch {chapter_num}:.*?(?=### Ch {chapter_num + 1}:|## Foreshadowing|$)'
    match = re.search(pattern, outline_text, re.DOTALL)
    return match.group(0).strip() if match else "(not found)"

def extract_next_chapter_outline(outline_text, chapter_num):
    """Extract the next chapter's outline (just first few lines for continuity)."""
    next_entry = extract_chapter_outline(outline_text, chapter_num + 1)
    if next_entry == "(not found)":
        return "(final chapter)"
    lines = next_entry.split('\n')[:10]
    return '\n'.join(lines)

def extract_title(outline_text):
    """Extract novel title from outline.md first line."""
    for line in outline_text.split('\n'):
        line = line.strip().lstrip('# ').strip()
        if line:
            return line
    return "Untitled"

def extract_pov_character(chapter_outline_text, characters_text):
    """Extract POV character name from chapter outline entry.
    Looks for 'POV: Name' or '(POV: Name)' in the chapter outline.
    Falls back to first character name found in characters.md."""
    # Try to find POV in chapter outline
    m = re.search(r'\(?\s*POV\s*:\s*([^,\)]+)', chapter_outline_text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    # Fallback: first ## Name in characters.md
    m = re.search(r'^##\s+(.+?)(?:\s*\()', characters_text, re.MULTILINE)
    if m:
        return m.group(1).strip()
    return "the protagonist"

def main():
    chapter_num = int(sys.argv[1])
    
    # Load all context
    voice = load_file(BASE_DIR / "voice.md")
    world = load_file(BASE_DIR / "world.md")
    characters = load_file(BASE_DIR / "characters.md")
    outline = load_file(BASE_DIR / "outline.md")
    canon = load_file(BASE_DIR / "canon.md")
    
    # Extract dynamic values
    title = extract_title(outline)
    chapter_outline = extract_chapter_outline(outline, chapter_num)
    next_chapter = extract_next_chapter_outline(outline, chapter_num)
    pov = extract_pov_character(chapter_outline, characters)
    
    # Previous chapter (if exists)
    prev_path = CHAPTERS_DIR / f"ch_{chapter_num - 1:02d}.md"
    if prev_path.exists():
        prev_text = prev_path.read_text()
        prev_tail = prev_text[-2000:] if len(prev_text) > 2000 else prev_text
    else:
        prev_tail = "(first chapter -- no previous)"
    
    # Load summaries of all previous chapters for continuity context
    summaries_dir = BASE_DIR / "summaries"
    prev_summaries = ""
    if summaries_dir.exists() and chapter_num > 1:
        parts = []
        for i in range(1, chapter_num):
            sfile = summaries_dir / f"summary_{i:02d}.md"
            if sfile.exists():
                parts.append(f"Chapter {i}: {sfile.read_text().strip()}")
        if parts:
            prev_summaries = "\n\n".join(parts)
    
    prompt = f"""Write Chapter {chapter_num} of "{title}."

VOICE DEFINITION (follow this exactly):
{voice}

THIS CHAPTER'S OUTLINE (hit every beat):
{chapter_outline}

NEXT CHAPTER'S OUTLINE (for continuity -- end this chapter so it flows into the next):
{next_chapter}

PREVIOUS CHAPTERS (summaries of what happened so far):
{prev_summaries if prev_summaries else "(no previous chapters)"}

PREVIOUS CHAPTER'S ENDING (continue from here):
{prev_tail}

WORLD BIBLE (reference for worldbuilding details):
{world}

CHARACTER REGISTRY (reference for speech patterns and behavior):
{characters}

CANON (established facts -- do not contradict):
{canon}

WRITING INSTRUCTIONS:
1. Write the COMPLETE chapter. Target ~3,200 words. Do not truncate or summarize.
2. Third-person limited, past tense, locked to {pov}'s POV.
3. Hit ALL numbered beats from the outline in order.
4. Plant ALL foreshadowing elements listed under "Plants."
5. Show sensory detail: what {pov} hears, smells, feels physically.
6. Ground physical sensations in specifics — not vague discomfort but
   precise, located sensation.
7. Dialogue follows the speech patterns defined in characters.md.
8. No banned words from voice.md Part 1 guardrails.
9. No AI fiction tells: no "a sense of," no "couldn't help but feel," no "eyes widened."
10. Vary sentence length. Short sentences for impact. Longer ones to build.
11. Metaphors from the POV character's experience and world — drawn from
    their occupation, history, and environment.
12. Trust the reader. Don't explain what scenes mean. Let them land.
13. Start the chapter in scene, not with exposition. End on a moment, not a summary.

PATTERNS TO AVOID (these have been flagged in previous chapters):
14. NO triadic sensory lists. Never "X. Y. Z." or "X and Y and Z" as three
    separate items in a row. Combine two, cut one, or restructure.
15. NO "He did not [verb]" more than once per chapter. Convert negatives
    to active alternatives or just cut them.
16. NO "He thought about [X]" constructions. Replace with: the thought
    itself as a fragment, a physical action, or dialogue.
17. NO "the way [X] did [Y]" as a simile connector more than twice per
    chapter. Use different simile structures or cut the comparison.
18. NO over-explaining after showing. If a scene demonstrates something,
    do not have the narrator restate it. Trust the scene.
19. NO section breaks (---) as rhythm crutches. Only use for genuine
    time/location jumps. Max 2 per chapter.
20. VARY paragraph length deliberately. Never more than 3 consecutive
    paragraphs of similar length. Include at least one 1-2 sentence
    paragraph and one 6+ sentence paragraph.
21. END the chapter differently from previous chapters. Find the ending
    that belongs to THIS chapter specifically.
22. INCLUDE at least one moment that surprises -- a character saying
    the wrong thing, an emotional beat arriving early or late, a detail
    that doesn't fit the expected pattern. Predictable excellence is
    still predictable.
23. FAVOR scene over summary. At least 70% of the chapter should be
    in-scene (moment by moment, with dialogue and action) rather than
    summary (narrator compressing time).
24. DIALOGUE should sound like speech, not prose. Characters should
    occasionally stumble, interrupt, trail off, or say something
    slightly wrong. No character speaks in polished epigrams.

Write the chapter now. Full text, beginning to end.
"""

    print(f"Drafting Chapter {chapter_num}...", file=sys.stderr)
    result = _call_writer(prompt)
    
    # Save
    out_path = CHAPTERS_DIR / f"ch_{chapter_num:02d}.md"
    out_path.write_text(result)
    print(f"Saved to {out_path}", file=sys.stderr)
    print(f"Word count: {len(result.split())}", file=sys.stderr)
    print(result)

if __name__ == "__main__":
    main()
