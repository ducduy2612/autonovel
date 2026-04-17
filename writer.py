#!/usr/bin/env python3
"""
Shared writer function for all LLM calls.

Centralises the Z.AI OpenAI-compatible API call pattern so thinking mode,
headers, and response parsing are maintained in one place.

Usage:
    from writer import call_writer

    text = call_writer(
        prompt="Write a chapter...",
        system="You are a novelist...",
        max_tokens=16000,
        timeout=600,
    )

Thinking mode is controlled by the AUTONOVEL_THINKING env var:
  - "off" : no thinking (default)
  - "on"  : thinking enabled

When thinking is enabled, temperature is forced to 1.0.
max_tokens is generous (128K) when thinking is on since reasoning + output
share the same token budget on Z.AI.
"""

import os
import httpx

from config import API_KEY, ZAI_CODING_BASE, WRITER_MODEL

# ---------------------------------------------------------------------------
# Thinking configuration
# ---------------------------------------------------------------------------

_THINKING_MODES = {"off", "on"}


def is_thinking_enabled() -> bool:
    """Return True if thinking mode is enabled.

    Reads AUTONOVEL_THINKING from the environment.  Defaults to ``"off"``.
    """
    level = os.environ.get("AUTONOVEL_THINKING", "off").lower()
    if level not in _THINKING_MODES:
        valid = ", ".join(sorted(_THINKING_MODES))
        print(
            f"WARNING: AUTONOVEL_THINKING='{level}' is not valid. "
            f"Choose from: {valid}. Defaulting to 'off'.",
        )
        return False
    return level == "on"


# ---------------------------------------------------------------------------
# Shared API call
# ---------------------------------------------------------------------------

_HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

# GLM-5 max output = 128K tokens. Be generous so thinking + output
# both fit without truncation.
_MAX_OUTPUT_THINKING = 131072  # 128K
_MAX_OUTPUT_DEFAULT = 16384


def call_writer(
    prompt: str,
    system: str,
    max_tokens: int = 16000,
    temperature: float = 0.8,
    timeout: int = 300,
    use_beta: bool = False,  # kept for signature compat, ignored
    model: str | None = None,
) -> str:
    """Call the writer model and return the text response.

    Args:
        prompt:       The user message content.
        system:       The system prompt.
        max_tokens:   Maximum output tokens (includes thinking when enabled).
                      When thinking is on, this is ignored in favour of a
                      generous 128K budget so reasoning doesn't truncate output.
        temperature:  Sampling temperature.  Ignored when thinking is enabled
                      (forced to 1.0).
        timeout:      HTTP request timeout in seconds.
        use_beta:     Ignored (kept for backward compatibility).
        model:        Override model name.  Falls back to WRITER_MODEL.

    Returns:
        The text content of the model's response.
    """
    thinking_on = is_thinking_enabled()

    # When thinking is on, use generous max_tokens so reasoning + output
    # both fit. Caller's max_tokens is too small for combined budget.
    effective_max = _MAX_OUTPUT_THINKING if thinking_on else max_tokens

    # Thinking adds significant latency — generous timeout
    effective_timeout = timeout * 2 if thinking_on else timeout

    payload: dict = {
        "model": model or WRITER_MODEL,
        "max_tokens": effective_max,
        "temperature": 1.0 if thinking_on else temperature,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    }

    if thinking_on:
        payload["thinking"] = {"type": "enabled"}

    resp = httpx.post(
        f"{ZAI_CODING_BASE}/chat/completions",
        headers=_HEADERS,
        json=payload,
        timeout=effective_timeout,
    )
    resp.raise_for_status()

    data = resp.json()
    choice = data["choices"][0]
    msg = choice.get("message", {})

    content = msg.get("content", "")

    # If content is empty but reasoning exists, the model used all tokens
    # on thinking — return reasoning as fallback so caller gets something.
    if not content:
        reasoning = msg.get("reasoning_content", "")
        if reasoning:
            return reasoning

    return content
