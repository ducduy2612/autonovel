#!/usr/bin/env python3
"""
Adversarial editing pass: identify what to IMPROVE in a chapter.
Every flagged passage gets a concrete rewrite suggestion.

Usage: python adversarial_edit.py 1        # single chapter
       python adversarial_edit.py all      # all chapters
"""
import sys
import json
import re
from pathlib import Path

from config import API_KEY, JUDGE_MODEL, CHAPTERS_DIR, analysis_language_note

BASE_DIR = Path(__file__).parent
EDIT_LOG_DIR = BASE_DIR / "edit_logs"
EDIT_LOG_DIR.mkdir(exist_ok=True)

def call_judge(prompt, max_tokens=8000):
    from writer import call_writer

    system_prompt = (
        "You are a revision editor who improves passages. "
        "You find what's weak in prose and show how to fix it. "
        "Every problem you identify comes with a concrete rewrite suggestion. "
        "You quote exactly from the text. "
        "You never invent or paraphrase. Always respond with valid JSON."
        + analysis_language_note()
    )
    return call_writer(
        prompt, system=system_prompt, max_tokens=max_tokens,
        temperature=0.3, timeout=None, model=JUDGE_MODEL)

def parse_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r'^```\w*\n?', '', text)
        text = re.sub(r'\n?```$', '', text)
    start = text.find('{')
    if start == -1:
        start = text.find('[')
    if start == -1:
        raise ValueError("No JSON found")
    # Try direct parse first
    try:
        return json.loads(text[start:], strict=False)
    except json.JSONDecodeError:
        # Find matching brace
        depth = 0
        in_string = False
        escape = False
        open_char = text[start]
        close_char = '}' if open_char == '{' else ']'
        for i in range(start, len(text)):
            c = text[i]
            if escape:
                escape = False
                continue
            if c == '\\' and in_string:
                escape = True
                continue
            if c == '"' and not escape:
                in_string = not in_string
                continue
            if in_string:
                continue
            if c == open_char:
                depth += 1
            elif c == close_char:
                depth -= 1
                if depth == 0:
                    return json.loads(text[start:i+1], strict=False)
        return json.loads(text[start:], strict=False)

EDIT_PROMPT = """You are editing a fantasy novel chapter. Your job: identify exactly
what needs improvement and provide a concrete rewrite for each passage.

THE CHAPTER ({word_count} words):
{chapter_text}

YOUR TASK:
1. Find 10-20 specific passages that should be REVISED.
   For each, quote the EXACT text (minimum 10 words of the quote so
   it's unambiguous), explain why it's weak, and provide a concrete rewrite.

2. Classify each issue as one of:
   - OVER-EXPLAIN: narrator explaining what the scene already demonstrated
   - REDUNDANT: restates what a previous sentence/scene already showed
   - TELL: names an emotion or state instead of showing it
   - GENERIC: could appear in any novel, not specific to this world/character
   - FLAT_DIALOGUE: dialogue that lacks voice, subtext, or character specificity
   - PACING: passage that disrupts the rhythm — too rushed or too slow
   - WEAK_OPENING: chapter or scene opening that fails to hook
   - PASSTHROUGH: narrator just moving characters between scenes without drama

3. Every item MUST have a concrete rewrite. No nulls.

4. After the individual revisions, provide:
   - recurring_patterns: what weaknesses keep appearing
   - missed_opportunities: moments in the chapter that could be stronger
   - revision_strategy: a 1-2 sentence overall approach for revising this chapter

Respond with JSON:
{{
  "revisions": [
    {{
      "quote": "exact text from the chapter (10+ words)",
      "type": "OVER-EXPLAIN|REDUNDANT|TELL|GENERIC|FLAT_DIALOGUE|PACING|WEAK_OPENING|PASSTHROUGH",
      "reason": "why this needs improvement",
      "rewrite": "concrete replacement text — always provided, never null"
    }}
  ],
  "tightest_passage": "quote the best 2-3 sentences in the chapter -- the ones you'd never touch",
  "loosest_passage": "quote the worst 2-3 sentences -- the ones that most need work",
  "recurring_patterns": ["pattern 1", "pattern 2"],
  "missed_opportunities": ["opportunity 1", "opportunity 2"],
  "revision_strategy": "1-2 sentence overall revision approach",
  "one_sentence_verdict": "what this chapter does well and what needs work, in one sentence"
}}
"""

def edit_chapter(ch_num):
    ch_path = CHAPTERS_DIR / f"ch_{ch_num:02d}.md"
    text = ch_path.read_text()
    word_count = len(text.split())
    
    prompt = EDIT_PROMPT.format(chapter_text=text, word_count=word_count)
    raw = call_judge(prompt)
    result = parse_json(raw)
    
    # Save log
    log_path = EDIT_LOG_DIR / f"ch{ch_num:02d}_cuts.json"
    with open(log_path, "w") as f:
        json.dump(result, f, indent=2)
    
    return result, word_count

def main():
    if len(sys.argv) < 2:
        print("Usage: python adversarial_edit.py <chapter_num|all>")
        sys.exit(1)
    
    if sys.argv[1] == "all":
        # Discover chapters dynamically from files on disk
        chapters = []
        for p in sorted(Path(CHAPTERS_DIR).glob("ch_*.md")):
            m = re.match(r"ch_(\d+)", p.name)
            if m:
                chapters.append(int(m.group(1)))
        chapters.sort()
        if not chapters:
            print("No chapter files found in chapters/")
            sys.exit(1)
    else:
        chapters = [int(sys.argv[1])]
    
    for ch in chapters:
        print(f"\n{'='*50}")
        print(f"EDITING CH {ch}")
        print(f"{'='*50}")
        
        try:
            result, wc = edit_chapter(ch)
        except Exception as e:
            print(f"  ERROR: {e}")
            continue
        
        revisions = result.get("revisions", [])
        verdict = result.get("one_sentence_verdict", "")
        strategy = result.get("revision_strategy", "")
        patterns = result.get("recurring_patterns", [])
        opportunities = result.get("missed_opportunities", [])
        
        # Count by type
        type_counts = {}
        for r in revisions:
            t = r.get("type", "?")
            type_counts[t] = type_counts.get(t, 0) + 1
        
        print(f"  Words: {wc}")
        print(f"  Revisions found: {len(revisions)}")
        print(f"  By type: {type_counts}")
        print(f"  Strategy: {strategy}")
        if patterns:
            print(f"  Recurring patterns: {patterns}")
        if opportunities:
            print(f"  Missed opportunities: {opportunities}")
        print(f"  Verdict: {verdict}")
        print(f"  Tightest: {result.get('tightest_passage', '')[:100]}...")
        print(f"  Loosest:  {result.get('loosest_passage', '')[:100]}...")

if __name__ == "__main__":
    main()
