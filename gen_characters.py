#!/usr/bin/env python3
"""
One-shot characters.md generator for foundation phase.
Reads seed.txt + voice.md + world.md + CRAFT.md, calls writer model.
"""
import sys

from config import language_instruction, BASE_DIR
from writer import call_writer as _call_api

_SYSTEM = (
    "You are a character designer for literary fiction with deep knowledge of "
    "wound/want/need/lie frameworks, Sanderson's three sliders, and dialogue "
    "distinctiveness. You create characters who feel like real people with "
    "contradictions, secrets, and speech patterns you can hear. "
    "You never use AI slop words. You write in clean, direct prose."
    + language_instruction()
)

def call_writer(prompt, max_tokens=16000):
    return _call_api(prompt, system=_SYSTEM, max_tokens=max_tokens,
                     temperature=0.7, timeout=300)

seed = (BASE_DIR / "seed.txt").read_text()
world = (BASE_DIR / "world.md").read_text()

# Voice Part 2 only
voice = (BASE_DIR / "voice.md").read_text()
voice_lines = voice.split('\n')
part2_start = next((i for i, l in enumerate(voice_lines) if 'Part 2' in l), None)
voice_part2 = '\n'.join(voice_lines[part2_start:]) if part2_start is not None else ""

prompt = f"""Build a complete character registry for this fantasy novel. This is CHARACTERS.MD --
the definitive reference for WHO exists in this story, what drives them, how they speak,
and what secrets they carry.

SEED CONCEPT:
{seed}

WORLD BIBLE (the world these characters inhabit):
{world}

VOICE IDENTITY (the novel's tone):
{voice_part2}

CHARACTER CRAFT REQUIREMENTS (from CRAFT.md):

### The Three Sliders (Sanderson)
Every character has three independent dials (0-10):
  PROACTIVITY -- Do they drive the plot or react to it?
  LIKABILITY  -- Does the reader empathize with them?
  COMPETENCE  -- Are they good at what they do?
Rule: compelling = HIGH on at least TWO, or HIGH on one with clear growth.

### Wound / Want / Need / Lie Framework
A causal chain:
  GHOST (backstory event) -> WOUND (ongoing damage) -> LIE (false belief to cope)
    -> WANT (external goal driven by Lie) -> NEED (internal truth, opposes Lie)
Rules: Want and Need must be IN TENSION. Lie statable in one sentence.
  Truth is its direct opposite.

### Dialogue Distinctiveness (8 dimensions)
1. Vocabulary level  2. Sentence length  3. Contractions/formality
4. Verbal tics  5. Question vs statement ratio  6. Interruption patterns
7. Metaphor domain  8. Directness vs indirectness
Test: Remove dialogue tags. Can you tell who's speaking?

BUILD THE REGISTRY WITH AT LEAST THESE CHARACTER ROLES:

1. **Protagonist** (POV character)
   - Full wound/want/need/lie chain
   - Three sliders with justification
   - Arc type (positive/negative/flat)
   - Detailed speech pattern (8 dimensions)
   - Physical habits and tells
   - At least 2 secrets
   - Key relationships mapped

2. **Central relationship** (parent, mentor, sibling, or partner)
   - Same depth as protagonist
   - What they know and what they're hiding
   - How their relationship creates tension

3. **Absent/missing figure** (someone whose absence drives the plot)
   - Even though they may not appear much, they need full depth
   - What actually happened to them
   - Their presence through absence

4. **Antagonist**
   - Not a villain -- someone whose interests conflict with the protagonist
   - Their own wound/want/need/lie (they should be understandable)

5. **Institutional figure** (system personified)
   - Represents the power structure
   - Believes they're protecting something

6. **Outsider/alternative perspective**
   - Sees the system from outside
   - What they represent thematically

7. **At least 1-2 additional characters** that the story needs
   - A peer/friend for the protagonist?
   - Someone connected to the central conflict?
   - A figure with divided loyalties?

FOR EACH CHARACTER INCLUDE:
- Name, age, role
- Ghost/Wound/Want/Need/Lie chain (for major characters)
- Three sliders (proactivity/likability/competence) with numbers and justification
- Arc type and arc trajectory
- Speech pattern (all 8 dimensions, with example lines)
- Physical appearance (specific, not generic)
- Physical habits and unconscious tells
- Secrets (what the reader doesn't learn immediately)
- Key relationships (mapped to other characters)
- Thematic role (what question does this character embody?)

IMPORTANT:
- Derive character names, roles, and relationships ENTIRELY from the seed concept
  and world bible above. Do not reuse names or roles from any other story.
- Characters must INTERCONNECT. Their wants should conflict with each other.
- Every secret should be something that would CHANGE the story if revealed.
- Speech patterns must be distinct enough to pass the no-tags test.
- Give the protagonist habits that come from their specific circumstances and abilities.
- The antagonist should be as fully realized as the protagonist -- a worthy opponent.
- Target ~3000-4000 words. Dense character work, not padding.
"""

print("Calling writer model...", file=sys.stderr)
result = call_writer(prompt)
print(result)
