#!/usr/bin/env python3
"""
Build a condensed arc summary for full-novel evaluation.
For each chapter: first 150 words, last 150 words, plus any dialogue.
Gives the reader panel enough to evaluate the ARC without 72k tokens.
"""
import re
from pathlib import Path

from config import API_KEY, WRITER_MODEL, CHAPTERS_DIR, analysis_language_note
from writer import call_writer as _call_api

BASE_DIR = Path(__file__).parent

_SYSTEM = "You summarize novel chapters precisely. State what HAPPENS, what CHANGES, and what QUESTIONS are left open. No evaluation. No praise. Just events and shifts." + analysis_language_note()

def call_writer(prompt, max_tokens=4000):
    return _call_api(prompt, system=_SYSTEM, max_tokens=max_tokens,
                     temperature=0.1, timeout=None)

def extract_key_passages(text):
    """Get opening, closing, and best dialogue from a chapter."""
    words = text.split()
    opening = ' '.join(words[:150])
    closing = ' '.join(words[-150:])
    
    # Extract dialogue lines
    dialogue = re.findall(r'["""]([^"""]{20,})["""]', text)
    # Pick up to 3 longest dialogue lines
    dialogue.sort(key=len, reverse=True)
    top_dialogue = dialogue[:3]
    
    return opening, closing, top_dialogue

def discover_chapters() -> list[int]:
    """Return sorted list of chapter numbers from files on disk."""
    import re as _re
    nums = []
    for p in sorted(CHAPTERS_DIR.glob("ch_*.md")):
        m = _re.match(r"ch_(\d+)", p.name)
        if m:
            nums.append(int(m.group(1)))
    return sorted(nums)


def main():
    summaries = []
    
    for ch in discover_chapters():
        path = CHAPTERS_DIR / f"ch_{ch:02d}.md"
        text = path.read_text()
        wc = len(text.split())
        opening, closing, dialogue = extract_key_passages(text)
        
        # Get a 100-word summary from the model
        summary = call_writer(
            f"Summarize this chapter in exactly 3 sentences. What happens, what changes, what question is left open.\n\nCHAPTER {ch}:\n{text}",
            max_tokens=200
        )
        
        entry = f"""### Chapter {ch} ({wc} words)
**Summary:** {summary}

**Opening:** {opening}...

**Closing:** ...{closing}

**Key dialogue:**
"""
        for d in dialogue:
            entry += f'> "{d}"\n\n'
        
        summaries.append(entry)
        print(f"Ch {ch}: summarized ({wc}w)")
    
    # Calculate total word count
    chapter_nums = discover_chapters()
    total_wc = sum(len((CHAPTERS_DIR / f"ch_{c:02d}.md").read_text().split()) for c in chapter_nums)
    
    # Assemble
    # Extract title from outline
    title = "Untitled Novel"
    outline_path = BASE_DIR / "outline.md"
    if outline_path.exists():
        for line in outline_path.read_text().split('\n'):
            stripped = line.strip().lstrip('# ').strip()
            if stripped:
                title = stripped
                break
    
    full = f"""# {title.upper()}
## Full-Arc Summary for Reader Panel

This document contains chapter summaries, opening/closing passages,
and key dialogue for all chapters. Total novel: {total_wc:,} words.

---

"""
    full += '\n---\n\n'.join(summaries)
    
    out_path = BASE_DIR / "arc_summary.md"
    out_path.write_text(full)
    print(f"\nSaved to {out_path} ({len(full.split())} words)")

if __name__ == "__main__":
    main()
