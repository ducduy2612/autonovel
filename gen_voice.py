#!/usr/bin/env python3
"""
One-shot voice Part 2 generator for foundation phase.
Reads seed.txt + the static Part 1 from voice.md, calls the writer model,
outputs Part 2 content (Voice Identity for this specific novel).

Usage: python gen_voice.py
       python gen_voice.py --full   # output the complete voice.md (Part 1 + Part 2)
"""
import sys

from config import language_instruction, BASE_DIR
from writer import call_writer as _call_api

_SYSTEM = (
    "You are a literary voice coach and prose stylist. You have studied "
    "the voices of Ursula Le Guin, Cormac McCarthy, Toni Morrison, "
    "Gene Wolfe, and N.K. Jemisin. You define voice not as 'tone' but as "
    "the complete set of sentence-level decisions a writer makes: rhythm, "
    "vocabulary wells, syntactic habits, what gets shown vs told, how "
    "dialogue sounds, where the camera sits. Your voice definitions are "
    "ACTIONABLE — a writer can read them and produce prose that matches. "
    "You never use AI slop words (delve, tapestry, myriad, etc). "
    "You write in clean, direct prose."
    + language_instruction()
)

def call_writer(prompt, max_tokens=16000):
    return _call_api(prompt, system=_SYSTEM, max_tokens=max_tokens,
                     temperature=0.8, timeout=None)


def extract_part1(voice_text: str) -> str:
    """Extract the static Part 1 (Guardrails) from voice.md."""
    lines = voice_text.split("\n")
    # Find where Part 2 starts
    part2_idx = None
    for i, line in enumerate(lines):
        if "Part 2" in line and line.strip().startswith("##"):
            part2_idx = i
            break
    if part2_idx is not None:
        return "\n".join(lines[:part2_idx]).rstrip()
    # If no Part 2 heading found, return everything up to the last --- separator
    return voice_text


seed = (BASE_DIR / "seed.txt").read_text()

# Load existing voice.md to extract Part 1
voice_path = BASE_DIR / "voice.md"
if voice_path.exists():
    existing_voice = voice_path.read_text()
    part1 = extract_part1(existing_voice)
else:
    sys.exit("ERROR: voice.md not found. It must exist with Part 1 guardrails.")

prompt = f"""Generate the Voice Identity (Part 2) for this specific novel. This will be 
appended to an existing voice.md that contains universal guardrails (Part 1). You are 
defining the unique, actionable voice for THIS story.

SEED CONCEPT:
{seed}

EXISTING GUARDRAILS (Part 1 — for reference, do not repeat these):
{part1}

YOUR TASK: Write Part 2 — the Voice Identity for this novel. It must contain ALL of 
these sections, filled in with specific, actionable content derived from the seed concept:

## Part 2: Voice Identity (generated per novel)

(Include this heading exactly, followed by the intro paragraph below, then the sections.)

Everything below is discovered during the foundation phase.
The agent proposes a voice that serves THIS story, writes exemplar
passages, and calibrates against them throughout drafting.

### Tone
A one-sentence description of the novel's tonal register. Be specific — not 
"dark and serious" but something like "Mythic and weighty, like stone tablets being 
read aloud in a temple" or "Warm, slightly breathless, like a traveler telling 
stories by firelight." The tone must emerge from the seed's world and themes.

### Sentence Rhythm
2-3 sentences describing the rhythm tendencies. What gets long sentences? What gets 
short ones? Where do fragments live? This is not rules — tendencies the writer 
should feel.

### Vocabulary Register
Define 2-3 "vocabulary wells" — the word-hoards this novel draws from. 
For example: "Anglo-Saxon blunt for violence and body; Latinate for ritual and 
law; colloquial for dialogue." Name each well and list 15-20 representative words 
per well. These wells constrain word choice throughout the novel.

### POV and Tense
State the POV strategy and tense. If rotating, explain the rotation rules.

### Dialogue Conventions
Tag strategy, subtext rules, how characters sound different from each other, 
what dialogue NEVER does in this novel.

### Exemplar Passages
Write 3-5 paragraphs that ARE the voice. These are the tuning fork — every 
chapter will be calibrated against them. They should demonstrate:
- The sentence rhythm described above
- Vocabulary from the defined wells
- The tone in action
- Body-before-emotion principle (physical sensation before emotional label)
- Dialogue conventions (if dialogue appears)

Write these passages set in THIS novel's world, using THIS novel's characters 
and situations (derived from the seed). They should feel like real novel prose, 
not abstract demonstrations.

### Anti-Exemplars
3-5 paragraphs showing what this voice is NOT. Not the generic anti-slop stuff 
from Part 1 — specific to THIS novel. For each anti-exemplar, include a brief 
note explaining WHY it's wrong for this voice (too flowery, too modern, too 
detached, etc.).

CRITICAL REQUIREMENTS:
- Be SPECIFIC to this seed concept. A different seed should produce a different Part 2.
- Vocabulary wells must name actual words the writer should reach for.
- Exemplar passages must demonstrate the voice in the novel's actual setting.
- Anti-exemplars must target the specific temptations THIS voice would face.
- No AI slop words in any exemplar or anti-exemplar passages.
- The whole Part 2 should be 2000-3000 words.
- Start with the heading "## Part 2: Voice Identity (generated per novel)"
"""

print("Calling writer model for voice identity...", file=sys.stderr)
result = call_writer(prompt)
print(result)
