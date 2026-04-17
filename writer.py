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

When thinking is enabled:
  - Uses SSE streaming so progress is logged to stderr
  - Temperature is forced to 1.0
  - max_tokens is generous (128K) since reasoning + output share the budget
"""

import json
import os
import sys
import time

import httpx

from config import API_KEY, API_TIMEOUT, ZAI_CODING_BASE, WRITER_MODEL

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

# How often (seconds) to log progress during streaming
_PROGRESS_INTERVAL = 15


def _log(msg: str):
    """Write a progress line to stderr."""
    print(msg, file=sys.stderr, flush=True)


def _build_payload(
    prompt: str,
    system: str,
    max_tokens: int,
    temperature: float,
    model: str | None,
    thinking_on: bool,
    stream: bool = False,
) -> dict:
    """Build the API request payload."""
    payload: dict = {
        "model": model or WRITER_MODEL,
        "max_tokens": _MAX_OUTPUT_THINKING if thinking_on else max_tokens,
        "temperature": 1.0 if thinking_on else temperature,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    }
    if thinking_on:
        payload["thinking"] = {"type": "enabled"}
    if stream:
        payload["stream"] = True
    return payload


def _call_streaming(
    payload: dict,
    effective_timeout: int,
    model_label: str,
) -> str:
    """Stream the response, logging thinking/generation progress to stderr.

    Returns the final content string.
    """
    _log(f"  [writer] Streaming {model_label} (thinking mode, timeout={effective_timeout}s)...")

    thinking_chunks = 0
    output_chunks = 0
    last_log = time.monotonic()
    full_reasoning = ""
    full_content = ""
    started = time.monotonic()

    with httpx.stream(
        "POST",
        f"{ZAI_CODING_BASE}/chat/completions",
        headers=_HEADERS,
        json=payload,
        timeout=effective_timeout,
    ) as resp:
        resp.raise_for_status()

        for line in resp.iter_lines():
            if not line.startswith("data: "):
                continue
            data_str = line[6:]
            if data_str.strip() == "[DONE]":
                break

            try:
                data = json.loads(data_str)
            except json.JSONDecodeError:
                continue

            choices = data.get("choices")
            if not choices:
                continue

            delta = choices[0].get("delta", {})

            # Thinking / reasoning tokens
            rc = delta.get("reasoning_content")
            if rc:
                full_reasoning += rc
                thinking_chunks += 1

            # Output tokens
            ct = delta.get("content")
            if ct:
                full_content += ct
                output_chunks += 1

            # Periodic progress log
            now = time.monotonic()
            if now - last_log >= _PROGRESS_INTERVAL:
                elapsed = int(now - started)
                if not full_content:
                    words_est = len(full_reasoning.split())
                    _log(
                        f"  [writer] ...thinking (~{words_est:,} words, "
                        f"{elapsed}s)"
                    )
                else:
                    words_est = len(full_content.split())
                    _log(
                        f"  [writer] ...generating (~{words_est:,} words, "
                        f"{elapsed}s)"
                    )
                last_log = now

    elapsed = int(time.monotonic() - started)
    think_words = len(full_reasoning.split())
    out_words = len(full_content.split())
    _log(
        f"  [writer] Stream complete: "
        f"{think_words:,} words thinking + {out_words:,} words output "
        f"in {elapsed}s"
    )

    if full_content:
        return full_content
    if full_reasoning:
        _log("  [writer] WARNING: model returned reasoning but no content — returning reasoning as fallback")
        return full_reasoning
    return ""


def _call_non_streaming(
    payload: dict,
    effective_timeout: int,
    model_label: str,
) -> str:
    """Non-streaming call (used when thinking is off)."""
    _log(f"  [writer] Calling {model_label} (timeout={effective_timeout}s)...")

    started = time.monotonic()
    resp = httpx.post(
        f"{ZAI_CODING_BASE}/chat/completions",
        headers=_HEADERS,
        json=payload,
        timeout=effective_timeout,
    )
    resp.raise_for_status()

    elapsed = int(time.monotonic() - started)
    _log(f"  [writer] Response received ({elapsed}s)")

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


def call_writer(
    prompt: str,
    system: str,
    max_tokens: int = 16000,
    temperature: float = 0.8,
    timeout: int | None = None,
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
        timeout:      HTTP request timeout in seconds.  Defaults to
                      ``config.API_TIMEOUT`` when ``None``.
        use_beta:     Ignored (kept for backward compatibility).
        model:        Override model name.  Falls back to WRITER_MODEL.

    Returns:
        The text content of the model's response.
    """
    thinking_on = is_thinking_enabled()

    # Resolve timeout: explicit arg > config default
    effective_timeout = timeout if timeout is not None else API_TIMEOUT

    # Thinking adds significant latency — double the timeout
    effective_timeout = effective_timeout * 2 if thinking_on else effective_timeout

    model_label = model or WRITER_MODEL

    if thinking_on:
        # Streaming: logs progress to stderr so callers can see activity
        payload = _build_payload(
            prompt, system, max_tokens, temperature, model,
            thinking_on=True, stream=True,
        )
        return _call_streaming(payload, effective_timeout, model_label)
    else:
        payload = _build_payload(
            prompt, system, max_tokens, temperature, model,
            thinking_on=False,
        )
        return _call_non_streaming(payload, effective_timeout, model_label)
