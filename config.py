#!/usr/bin/env python3
"""
Shared configuration module for the autonovel pipeline.

Centralizes all environment variable reading so scripts don't duplicate
load_dotenv() calls and env var names. Import what you need:

    from config import get_language, API_KEY, WRITER_MODEL
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Bootstrap: load .env once at import time
# ---------------------------------------------------------------------------
BASE_DIR: Path = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# ---------------------------------------------------------------------------
# API credentials
# ---------------------------------------------------------------------------
API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")
GEMINI_KEY: str = os.environ.get("GEMINI_API_KEY", "")
ELEVENLABS_KEY: str = os.environ.get("ELEVENLABS_API_KEY", "")

# ---------------------------------------------------------------------------
# Model names
# ---------------------------------------------------------------------------
WRITER_MODEL: str = os.environ.get("AUTONOVEL_WRITER_MODEL", "claude-sonnet-4-6")
JUDGE_MODEL: str = os.environ.get("AUTONOVEL_JUDGE_MODEL", "claude-sonnet-4-6")
REVIEW_MODEL: str = os.environ.get("AUTONOVEL_REVIEW_MODEL", "claude-opus-4-6")

# ---------------------------------------------------------------------------
# API base URL
# ---------------------------------------------------------------------------
API_BASE: str = os.environ.get("AUTONOVEL_API_BASE_URL", "https://api.anthropic.com")

# ---------------------------------------------------------------------------
# Directory constants
# ---------------------------------------------------------------------------
CHAPTERS_DIR: Path = BASE_DIR / "chapters"

# ---------------------------------------------------------------------------
# Language support
# ---------------------------------------------------------------------------
_SUPPORTED_LANGUAGES = {"en", "vi"}


def get_language() -> str:
    """Return the pipeline language code (e.g. ``'en'``, ``'vi'``).

    Reads ``AUTONOVEL_LANGUAGE`` from the environment.  Defaults to
    ``'en'`` for backward compatibility.  Prints a warning to *stderr*
    when the value is not in the supported set so misconfiguration is
    visible in logs.
    """
    lang = os.environ.get("AUTONOVEL_LANGUAGE", "en")
    if lang not in _SUPPORTED_LANGUAGES:
        print(
            f"WARNING: AUTONOVEL_LANGUAGE='{lang}' is not in the supported set "
            f"{sorted(_SUPPORTED_LANGUAGES)}. Defaulting to 'en'.",
            file=sys.stderr,
        )
        return "en"
    return lang


# ---------------------------------------------------------------------------
# Language-aware prompt helpers
# ---------------------------------------------------------------------------

_VI_CREATIVE_INSTRUCTION = (
    "Write all prose, descriptions, dialogue, and narrative in natural, "
    "literary Vietnamese. Use authentic Vietnamese phrasing and idiom — "
    "avoid word-for-word translation from English."
)

_VI_ANALYSIS_NOTE = (
    "The text you are analysing is written in Vietnamese. You may respond "
    "in English for analysis and commentary, but you MUST preserve all "
    "quoted Vietnamese prose exactly as written — do not translate or "
    "paraphrase quoted passages."
)


def language_instruction() -> str:
    """Return a creative-writing language instruction when the pipeline
    language is Vietnamese, otherwise an empty string.

    Append the result to the user prompt of any content-generating LLM
    call so the model writes in the target language.
    """
    if get_language() == "vi":
        return _VI_CREATIVE_INSTRUCTION
    return ""


def analysis_language_note() -> str:
    """Return a Vietnamese-awareness note when the pipeline language is
    Vietnamese, otherwise an empty string.

    Intended for evaluation / analysis prompts where the LLM should
    understand Vietnamese text but respond in English, preserving all
    quoted Vietnamese exactly.
    """
    if get_language() == "vi":
        return _VI_ANALYSIS_NOTE
    return ""
