#!/usr/bin/env python3
"""Generate outline.md from seed + world + characters + mystery + craft."""
import sys

from config import language_instruction, BASE_DIR
from writer import call_writer as _call_api

_SYSTEM = (
    "You are a novel architect with deep knowledge of Save the Cat beats, "
    "Sanderson's plotting principles, Dan Harmon's Story Circle, and MICE Quotient. "
    "You build outlines that an author can draft from without inventing structure "
    "on the fly. Every chapter has beats, emotional arc, and try-fail cycle type. "
    "You never use AI slop words. You write in clean, direct prose."
    + language_instruction()
)

def call_writer(prompt, max_tokens=16000):
    return _call_api(prompt, system=_SYSTEM, max_tokens=max_tokens,
                     temperature=0.5, timeout=None, use_beta=True)

seed = (BASE_DIR / "seed.txt").read_text()
world = (BASE_DIR / "world.md").read_text()
characters = (BASE_DIR / "characters.md").read_text()
mystery = (BASE_DIR / "MYSTERY.md").read_text() if (BASE_DIR / "MYSTERY.md").exists() else ""
craft = (BASE_DIR / "CRAFT.md").read_text()

# Voice Part 2 only
voice = (BASE_DIR / "voice.md").read_text()
voice_lines = voice.split('\n')
part2_start = next((i for i, l in enumerate(voice_lines) if 'Part 2' in l), None)
voice_part2 = '\n'.join(voice_lines[part2_start:]) if part2_start is not None else ""

prompt = f"""Build a complete chapter outline for this fantasy novel. Target: 22-26 chapters,
~80,000 words total (~3,000-4,000 words per chapter).

SEED CONCEPT:
{seed}

THE CENTRAL MYSTERY (author's eyes only -- reader discovers gradually):
{mystery}

WORLD BIBLE:
{world}

CHARACTER REGISTRY:
{characters}

VOICE (tone and register):
{voice_part2}

CRAFT REFERENCE (structures to follow):
{craft}

BUILD THE OUTLINE WITH:

## Act Structure
Map out Act I (0-23%), Act II Part 1 (23-50%), Act II Part 2 (50-77%), Act III (77-100%).
State the percentage marks for the key beats.

## Chapter-by-Chapter Outline

For EACH chapter, provide:
### Ch N: [Title]
- **POV:** (specify which character, typically one consistent POV in third-person limited)
- **Location:** Which locations appear
- **Save the Cat beat:** Which beat this chapter serves (Opening Image, Setup, Catalyst, etc.)
- **% mark:** Where this falls in the novel
- **Emotional arc:** Starting emotion → ending emotion
- **Try-fail cycle:** Yes-but / No-and / No-but / Yes-and
- **Beats:** 3-5 specific scene beats that must happen
- **Plants:** Foreshadowing elements planted in this chapter
- **Payoffs:** Foreshadowing elements that pay off here
- **Character movement:** What changes for the protagonist (or other characters) by chapter's end
- **The lie:** How the protagonist's core false belief is reinforced or challenged
- **~Word count target:** for pacing

## Foreshadowing Ledger

A table tracking every planted thread:
| Thread | Planted (Ch) | Reinforced (Ch) | Payoff (Ch) | Type |

Include at LEAST 15 threads. Types: object, dialogue, action, symbolic, structural.

KEY PLOT ARCHITECTURE:
Derive the plot structure entirely from the seed concept, world bible, and characters above.
Follow these structural principles:

Act I: Establish the protagonist's world, their pain, their ability, their relationships.
Plant the central mystery/conflict early.
Catalyst: something forces the protagonist into the main conflict.

Act II Part 1: Investigation/deepening. The protagonist engages with the conflict,
encounters opposition, begins to understand the stakes.
Midpoint: The protagonist learns a partial truth that changes their approach (false victory or defeat).

Act II Part 2: Pressure mounts. Opposition intensifies.
Allies and enemies reveal their true natures. The protagonist's false belief becomes unsustainable.
All Is Lost: The protagonist confronts a devastating truth.

Act III: The protagonist understands the real question. Must choose how to answer.
The climax draws on the world's established rules and the character's growth.
The resolution shows the aftermath — with real cost.

CONSTRAINTS:
- The climax must use the world's established rules and systems
- The protagonist's journey should feel like a mystery overlaid on a character arc
- The Stability Trap: bad things must stay bad. Not everything resolves cleanly.
- Key figures must appear in person at critical moments (not just in memory/letters)
- At least 3 chapters should be "quiet" -- character-focused, low-action, emotionally rich
- Vary the try-fail types: 60%+ should be "yes-but" or "no-and"
- The foreshadowing ledger must have plant-to-payoff distances of at least 3 chapters
- Derive ALL plot details from the seed concept and world bible. Do not reuse plot elements from any other story.
"""

print("Calling writer model...", file=sys.stderr)
result = call_writer(prompt)
print(result)
