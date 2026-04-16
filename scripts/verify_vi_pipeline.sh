#!/usr/bin/env bash
# =============================================================================
# verify_vi_pipeline.sh — Vietnamese Foundation Pipeline Live Verification
# =============================================================================
#
# PURPOSE
#   Runs the autonovel foundation phase with AUTONOVEL_LANGUAGE=vi and verifies
#   that all output files contain Vietnamese text and that state.json records
#   the correct language code. This is the live integration test for slices
#   S02–S04 working together with a Vietnamese seed concept.
#
# PREREQUISITES
#   - ANTHROPIC_API_KEY must be set in the environment (or in .env file)
#   - uv must be installed (https://docs.astral.sh/uv/)
#   - The autonovel project dependencies must be resolved (uv sync)
#   - seed_vi.txt must exist in the project root
#
# HOW TO RUN
#   From the project root directory:
#
#     chmod +x scripts/verify_vi_pipeline.sh
#     ./scripts/verify_vi_pipeline.sh
#
#   Or directly:
#
#     bash scripts/verify_vi_pipeline.sh
#
# WHAT CONSTITUTES SUCCESS
#   All 6 checks must pass:
#     1. world.md exists and contains Vietnamese diacritical characters
#     2. characters.md exists and contains Vietnamese diacritical characters
#     3. outline.md exists and contains Vietnamese diacritical characters
#     4. canon.md exists and contains Vietnamese diacritical characters
#     5. state.json contains "language": "vi"
#     6. No foundation script exited with a non-zero return code
#
#   A Vietnamese diacritical character is one of: ă â đ ê ô ơ ư (and uppercase)
#   These are unique to Vietnamese and not found in standard English text.
#
# EXPECTED COST
#   The foundation phase makes 5-6 API calls to Claude:
#     1. gen_world.py      (~2000 output tokens)
#     2. gen_characters.py (~2000 output tokens)
#     3. gen_outline.py    (~2000 output tokens)
#     4. gen_outline_part2.py (~1000 output tokens)
#     5. gen_canon.py      (~1500 output tokens)
#     6. evaluate.py       (~500 output tokens)
#   Plus voice_fingerprint.py (~500 output tokens)
#   Total: approximately 10,000 output tokens across 6-7 calls.
#   At Claude Sonnet pricing, this costs roughly $0.05–$0.10 USD.
#
# INTERPRETING THE OUTPUT
#   The script prints a line for each check:
#     PASS  — the check succeeded
#     FAIL  — the check failed (see the description for details)
#   At the end it prints a summary:
#     "ALL CHECKS PASSED" — everything works correctly
#     "N of 6 CHECKS FAILED" — list of failures to investigate
#
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# --- Prerequisites check ----------------------------------------------------

if [ ! -f seed_vi.txt ]; then
    echo "FAIL: seed_vi.txt not found in $PROJECT_ROOT"
    exit 1
fi

if [ -z "${ANTHROPIC_API_KEY:-}" ] && [ ! -f .env ]; then
    echo "FAIL: ANTHROPIC_API_KEY not set and no .env file found."
    echo "      Set the environment variable or create .env with your key."
    exit 1
fi

if ! command -v uv &>/dev/null; then
    echo "FAIL: uv is not installed. See https://docs.astral.sh/uv/"
    exit 1
fi

# --- Setup ------------------------------------------------------------------

echo "=== Vietnamese Pipeline Verification ==="
echo "Project root: $PROJECT_ROOT"
echo ""

# Set language environment variable
export AUTONOVEL_LANGUAGE=vi

# Create seed.txt from seed_vi.txt if it doesn't exist
if [ ! -f seed.txt ]; then
    echo "Copying seed_vi.txt -> seed.txt"
    cp seed_vi.txt seed.txt
else
    echo "seed.txt already exists (not overwriting)"
fi

# Clean any prior state if running fresh
if [ -f state.json ]; then
    echo "Removing existing state.json for clean run"
    rm -f state.json
fi

# --- Run the foundation phase -----------------------------------------------

echo ""
echo "Running foundation phase with AUTONOVEL_LANGUAGE=vi ..."
echo ""

uv run python run_pipeline.py --from-scratch --phase foundation
PIPELINE_EXIT=$?

echo ""
echo "Pipeline exited with code: $PIPELINE_EXIT"
echo ""

# --- Verification checks ----------------------------------------------------

PASS_COUNT=0
FAIL_COUNT=0
FAILURES=()

check_file_vietnamese() {
    local label="$1"
    local filepath="$2"

    if [ ! -f "$filepath" ]; then
        echo "FAIL: $label — file does not exist ($filepath)"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        FAILURES+=("$label: file missing")
        return
    fi

    local size
    size=$(wc -c < "$filepath")
    if [ "$size" -lt 50 ]; then
        echo "FAIL: $label — file too small ($size bytes)"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        FAILURES+=("$label: too small ($size bytes)")
        return
    fi

    # Check for Vietnamese-specific diacritical characters
    # ă â đ ê ô ơ ư and their uppercase equivalents Ă Â Ê Ô Ơ Ư
    # Note: Đ/đ is the most distinctive Vietnamese character
    if grep -qP '[ăâđêôơưĂÂÊÔƠƯ]' "$filepath"; then
        echo "PASS: $label — exists ($size bytes) with Vietnamese characters"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo "FAIL: $label — exists ($size bytes) but NO Vietnamese characters found"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        FAILURES+=("$label: no Vietnamese chars")
    fi
}

check_state_language() {
    local filepath="$1"

    if [ ! -f "$filepath" ]; then
        echo "FAIL: state.json — file does not exist"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        FAILURES+=("state.json: file missing")
        return
    fi

    if grep -q '"language".*:.*"vi"' "$filepath"; then
        echo "PASS: state.json — contains \"language\": \"vi\""
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo "FAIL: state.json — does not contain \"language\": \"vi\""
        FAIL_COUNT=$((FAIL_COUNT + 1))
        FAILURES+=("state.json: language not set to vi")
    fi
}

check_pipeline_exit() {
    if [ "$PIPELINE_EXIT" -eq 0 ]; then
        echo "PASS: pipeline exit code is 0"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo "FAIL: pipeline exited with code $PIPELINE_EXIT"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        FAILURES+=("pipeline exit code: $PIPELINE_EXIT")
    fi
}

echo "=== Running verification checks ==="
echo ""

check_file_vietnamese "world.md"      "world.md"
check_file_vietnamese "characters.md"  "characters.md"
check_file_vietnamese "outline.md"     "outline.md"
check_file_vietnamese "canon.md"       "canon.md"
check_state_language  "state.json"
check_pipeline_exit

echo ""
echo "=== Results ==="
echo "Passed: $PASS_COUNT"
echo "Failed: $FAIL_COUNT"

if [ "$FAIL_COUNT" -gt 0 ]; then
    echo ""
    echo "Failures:"
    for f in "${FAILURES[@]}"; do
        echo "  - $f"
    done
    echo ""
    echo "$FAIL_COUNT of $((PASS_COUNT + FAIL_COUNT)) CHECKS FAILED"
    exit 1
else
    echo ""
    echo "ALL $PASS_COUNT CHECKS PASSED"
    exit 0
fi
