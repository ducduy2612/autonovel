#!/usr/bin/env python3
"""
Shared writer function for all LLM calls.

Centralises the Anthropic API call pattern so thinking mode, headers,
and response parsing are maintained in one place.

Usage:
    from writer import call_writer

    text = call_writer(
        prompt="Write a chapter...",
        system="You are a novelist...",
        max_tokens=16000,
        timeout=600,
    )

Thinking mode is controlled by the AUTONOVEL_THINKING env var:
  - "off"   : no thinking (default)
  - "low"   : budget_tokens=4000
  - "medium": budget_tokens=8000
  - "high"  : budget_tokens=16000
When thinking is enabled, temperature is forced to 1.0 (API requirement).
"""

import os
import httpx

from config import API_KEY, API_BASE, WRITER_MODEL

# ---------------------------------------------------------------------------
# Thinking configuration
# ---------------------------------------------------------------------------
_THINKING_BUDGETS = {
    "off": None,
    "low": 4000,
    "medium": 8000,
    "high": 16000,
}


def get_thinking_budget() -> int | None:
    """Return the thinking budget in tokens, or None if thinking is off.

    Reads AUTONOVEL_THINKING from the environment.  Defaults to ``"off"``.
    """
    level = os.environ.get("AUTONOVEL_THINKING", "off").lower()
    if level not in _THINKING_BUDGETS:
        valid = ", ".join(sorted(_THINKING_BUDGETS))
        print(
            f"WARNING: AUTONOVEL_THINKING='{level}' is not valid. "
            f"Choose from: {valid}. Defaulting to 'off'.",
        )
        return None
    return _THINKING_BUDGETS[level]


# ---------------------------------------------------------------------------
# Shared API call
# ---------------------------------------------------------------------------

_HEADERS_BASE = {
    "x-api-key": API_KEY,
    "anthropic-version": "2023-06-01",
    "content-type": "application/json",
}

_HEADERS_BETA = {
    **_HEADERS_BASE,
    "anthropic-beta": "context-1m-2025-08-07",
}


def call_writer(
    prompt: str,
    system: str,
    max_tokens: int = 16000,
    temperature: float = 0.8,
    timeout: int = 300,
    use_beta: bool = False,
) -> str:
    """Call the writer model and return the text response.

    Args:
        prompt:       The user message content.
        system:       The system prompt.
        max_tokens:   Maximum output tokens (does NOT include thinking tokens).
        temperature:  Sampling temperature.  Ignored when thinking is enabled
                      (forced to 1.0 by the API).
        timeout:      HTTP request timeout in seconds.
        use_beta:     Whether to include the anthropic-beta context header.

    Returns:
        The text content of the model's response.
    """
    headers = _HEADERS_BETA if use_beta else _HEADERS_BASE

    budget = get_thinking_budget()
    thinking_enabled = budget is not None

    payload: dict = {
        "model": WRITER_MODEL,
        "max_tokens": max_tokens,
        "temperature": 1.0 if thinking_enabled else temperature,
        "system": system,
        "messages": [{"role": "user", "content": prompt}],
    }

    if thinking_enabled:
        payload["thinking"] = {"type": "enabled", "budget_tokens": budget}

    resp = httpx.post(
        f"{API_BASE}/v1/messages",
        headers=headers,
        json=payload,
        timeout=timeout,
    )
    resp.raise_for_status()

    content = resp.json()["content"]

    if thinking_enabled:
        # Response contains [thinking_block, text_block] — extract the text.
        return next(b["text"] for b in content if b["type"] == "text")

    return content[0]["text"]
