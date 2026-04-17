#!/usr/bin/env python3
"""Generate remaining chapters + foreshadowing ledger."""
import os
import sys

from config import language_instruction, BASE_DIR
from writer import call_writer as _call_api

_SYSTEM = (
    "You are a novel architect continuing an outline. Write in the same format "
    "as the preceding chapters. Every chapter needs: POV, Location, Save the Cat beat, "
    "% mark, Emotional arc, Try-fail cycle, Beats, Plants, Payoffs, Character movement, "
    "The lie, Word count target."
    + language_instruction()
)

def call_writer(prompt, max_tokens=16000):
    return _call_api(prompt, system=_SYSTEM, max_tokens=max_tokens,
                     temperature=0.5, timeout=None)

part1_path = os.environ.get("OUTLINE_PART1_PATH", "/tmp/outline_output.md")
part1 = open(part1_path).read()
mystery = (BASE_DIR / "MYSTERY.md").read_text()

prompt = f"""Here is the first part of a novel outline that was cut off mid-chapter.
Continue from where it left off, then complete the remaining chapters,
then write the Foreshadowing Ledger.

THE OUTLINE SO FAR:
{part1}

THE CENTRAL MYSTERY (for reference):
{mystery}

Complete the remaining chapters following the same format as the outline so far.
Each chapter should have: title, POV, location, Save the Cat beat, emotional arc,
try-fail cycle, beats, plants, payoffs, character movement, and word count target.

Then write:

## Foreshadowing Ledger

| # | Thread | Planted (Ch) | Reinforced (Ch) | Payoff (Ch) | Type |
|---|--------|-------------|-----------------|-------------|------|

Include at LEAST 15 threads. Types: object, dialogue, action, symbolic, structural.
Plant-to-payoff distance must be at least 3 chapters.

REMEMBER:
- Derive ALL plot details from the outline so far and the mystery above
- The climax should use the world's established rules in a surprising way
- Not everything resolves cleanly (Stability Trap)
- The protagonist's core false belief must be fully shattered by the climax
- Final Image should mirror the Opening Image but show transformation
- At least one quiet chapter in the back half
"""

print("Calling writer model...", file=sys.stderr)
result = call_writer(prompt)
print(result)
