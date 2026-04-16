---
estimated_steps: 29
estimated_files: 2
skills_used: []
---

# T03: Prepare Vietnamese seed and live verification script

Prepare the Vietnamese seed concept and create a verification script for the live foundation run.

1. **Create `seed_vi.txt`** — an authentic Vietnamese fantasy novel seed concept. Write it as natural Vietnamese (not machine-translated English). The seed should describe a compelling fantasy world with:
   - A unique magic system concept
   - A protagonist with internal conflict
   - A central tension/mystery
   - Cultural elements that feel Vietnamese-inspired
   Keep it to ~300-500 words. This file is a reference — users copy it to seed.txt when running the Vietnamese pipeline.

2. **Create `scripts/verify_vi_pipeline.sh`** — a shell script that:
   - Sets AUTONOVEL_LANGUAGE=vi in environment
   - Creates seed.txt from seed_vi.txt if it doesn't exist
   - Runs `uv run python run_pipeline.py --from-scratch --phase foundation`
   - After completion, checks:
     - world.md exists and contains Vietnamese characters (ă, â, đ, ê, ô, ơ, ư)
     - characters.md exists and contains Vietnamese characters
     - outline.md exists and contains Vietnamese characters
     - canon.md exists and contains Vietnamese characters
     - state.json contains `"language": "vi"`
   - Reports pass/fail for each check
   - Requires ANTHROPIC_API_KEY in environment (fails gracefully if missing)

3. **Document the live verification procedure** in a comment block at the top of the verification script, explaining:
   - Prerequisites (ANTHROPIC_API_KEY, uv installed)
   - How to run the verification
   - What constitutes success
   - Expected cost (5-6 API calls to Claude)
   - How to interpret the output

Constraints:
- seed_vi.txt must be natural Vietnamese prose, not machine-translated
- The verification script must be self-contained (no external dependencies beyond uv and the pipeline)
- The script should not require manual intervention — fully automated

## Inputs

- `run_pipeline.py`
- `config.py`

## Expected Output

- `seed_vi.txt`
- `scripts/verify_vi_pipeline.sh`

## Verification

test -f seed_vi.txt && test -f scripts/verify_vi_pipeline.sh && grep -q 'AUTONOVEL_LANGUAGE=vi' scripts/verify_vi_pipeline.sh && python3 -c "t=open('seed_vi.txt').read(); assert any(c in t for c in 'ăâđêôơư'), 'No Vietnamese chars in seed'"
