#!/usr/bin/env python3
"""
Build a condensed arc summary for full-novel evaluation.

Splits chapters into 3 batches, each sent as a single API call with
full chapter texts. The model sees arc progression within each batch
and is told what came before so it doesn't repeat established context.
"""
import re
import sys
import time
from pathlib import Path

from config import CHAPTERS_DIR, analysis_language_note
from writer import call_writer as _call_api

_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 10
_BATCH_SIZE = 8  # chapters per batch (~24k words ≈ 30k tokens)

BASE_DIR = Path(__file__).parent

_SYSTEM = (
    "You summarize novel chapters precisely. "
    "State what HAPPENS, what CHANGES, and what QUESTIONS are left open. "
    "No evaluation. No praise. Just events and shifts. "
    "Do NOT repeat information established in earlier chapters — "
    "each summary should only cover what is NEW in that chapter."
    + analysis_language_note()
)


def call_writer_with_retry(prompt, max_tokens=4000):
    """call_writer with retry on transient HTTP errors."""
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            return _call_api(prompt, system=_SYSTEM, max_tokens=max_tokens,
                             temperature=0.1, timeout=None)
        except Exception as exc:
            status = getattr(getattr(exc, 'response', None), 'status_code', None)
            print(
                f"  WARNING: attempt {attempt}/{_MAX_RETRIES} failed"
                + (f" (HTTP {status})" if status else f": {exc}"),
                file=sys.stderr,
            )
            if attempt == _MAX_RETRIES:
                print(f"  ERROR: failed after {_MAX_RETRIES} attempts", file=sys.stderr)
                raise
            delay = _RETRY_BASE_DELAY * attempt
            print(f"  Retrying in {delay}s...", file=sys.stderr)
            time.sleep(delay)


def extract_key_passages(text):
    """Get opening, closing, and best dialogue from a chapter."""
    words = text.split()
    opening = ' '.join(words[:150])
    closing = ' '.join(words[-150:])

    dialogue = re.findall(r'["""]([^"""]{20,})["""]', text)
    dialogue.sort(key=len, reverse=True)
    top_dialogue = dialogue[:3]

    return opening, closing, top_dialogue


def discover_chapters() -> list[int]:
    """Return sorted list of chapter numbers from files on disk."""
    nums = []
    for p in sorted(CHAPTERS_DIR.glob("ch_*.md")):
        m = re.match(r"ch_(\d+)", p.name)
        if m:
            nums.append(int(m.group(1)))
    return sorted(nums)


def main():
    chapter_nums = discover_chapters()

    # Load all chapter texts
    chapters = []
    for ch in chapter_nums:
        path = CHAPTERS_DIR / f"ch_{ch:02d}.md"
        text = path.read_text()
        wc = len(text.split())
        chapters.append((ch, wc, text))
        print(f"Ch {ch}: loaded ({wc}w)")

    total_wc = sum(wc for _, wc, _ in chapters)

    # Split into batches of _BATCH_SIZE
    batches = [chapters[i:i + _BATCH_SIZE] for i in range(0, len(chapters), _BATCH_SIZE)]
    print(f"\n{len(chapters)} chapters → {len(batches)} batches of ≤{_BATCH_SIZE}")

    # Summaries from previous batches — passed as context so the model
    # knows what's already been established and doesn't repeat.
    prior_summaries = ""
    summaries_by_ch: dict[int, str] = {}

    for batch_idx, batch in enumerate(batches):
        batch_label = f"batch {batch_idx + 1}/{len(batches)} (Ch {batch[0][0]}–{batch[-1][0]})"
        print(f"\nCalling writer for {batch_label}...")

        chapters_block = ""
        for ch, wc, text in batch:
            chapters_block += f"=== CHAPTER {ch} ({wc} words) ===\n{text}\n\n"

        prior_context = ""
        if prior_summaries:
            prior_context = (
                f"SUMMARIES OF EARLIER CHAPTERS (already covered — do NOT repeat this information):\n"
                f"{prior_summaries}\n\n"
            )

        prompt = (
            f"{prior_context}"
            f"Below are chapters {batch[0][0]}–{batch[-1][0]} of a novel "
            f"({total_wc:,} words total across all chapters).\n\n"
            f"For EACH chapter, write a 2-3 sentence summary. "
            f"Focus on what is NEW in that chapter — do not repeat "
            f"information already established in earlier chapters.\n\n"
            f"Use this format for each:\n"
            f"## Ch <N>\n<summary>\n\n"
            f"{chapters_block}"
        )

        raw = call_writer_with_retry(prompt, max_tokens=3000)

        # Parse summaries from model output
        for m in re.finditer(r"##\s*Ch\s*(\d+)\s*\n(.+?)(?=\n##\s*Ch|\Z)", raw, re.DOTALL):
            ch_num = int(m.group(1))
            summary = m.group(2).strip()
            summaries_by_ch[ch_num] = summary
            prior_summaries += f"Ch {ch_num}: {summary}\n"

        parsed = len(summaries_by_ch)
        print(f"  {batch_label} done — parsed {len(summaries_by_ch) - (parsed - len(batch))} summaries")

    # Assemble with local extractions
    entries = []
    for ch, wc, text in chapters:
        opening, closing, dialogue = extract_key_passages(text)
        summary = summaries_by_ch.get(ch, "[Summary not found in model output]")
        entry = f"""### Chapter {ch} ({wc} words)
**Summary:** {summary}

**Opening:** {opening}...

**Closing:** ...{closing}

**Key dialogue:**
"""
        for d in dialogue:
            entry += f'> "{d}"\n\n'

        entries.append(entry)

    # Title from outline
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
    full += '\n---\n\n'.join(entries)

    out_path = BASE_DIR / "arc_summary.md"
    out_path.write_text(full)
    print(f"\nSaved to {out_path} ({len(full.split())} words)")
    print(f"Model summaries parsed: {len(summaries_by_ch)}/{len(chapter_nums)}")


if __name__ == "__main__":
    main()
