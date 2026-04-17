#!/usr/bin/env python3
"""Compare GLM-5 vs GLM-5.1, each with reasoning=enabled and reasoning=disabled.

Uses Z.AI Coding Plan OpenAI-compatible endpoint.
Ref: https://docs.z.ai/guides/llm/glm-5
     https://docs.z.ai/guides/capabilities/thinking-mode
     https://docs.z.ai/devpack/tool/others
"""
import json
import httpx
from config import API_KEY

# Coding Plan endpoint (not the general /api/paas/v4)
API_BASE = "https://api.z.ai/api/coding/paas/v4"

PROMPT = "Viết một đoạn văn khoảng 100 chữ tả cảnh một người lạ bước vào quán rượu làng giữa cơn bão. Chữ nghĩa văn chương, tả thực, không sáo rỗng."
SYSTEM = "Bạn là nhà văn văn học Việt Nam. Viết bằng tiếng Việt tự nhiên, đậm chất văn chương. Tránh văn dịch, dùng thành ngữ và cách nói thuần Việt.QUAN TRỌNG: Khi suy nghĩ (reasoning), hãy suy nghĩ bằng tiếng Việt."

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

MODELS = ["GLM-5", "GLM-5.1"]


def call(label, model, extra_payload, max_tokens=128000):
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": PROMPT},
        ],
    }
    payload.update(extra_payload)
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"  model={model}  max_tokens={max_tokens}  extra_keys={list(extra_payload.keys())}")
    print(f"{'='*60}")
    try:
        resp = httpx.post(
            f"{API_BASE}/chat/completions",
            headers=HEADERS,
            json=payload,
            timeout=180,
        )
        resp.raise_for_status()
        data = resp.json()

        choice = data["choices"][0]
        msg = choice.get("message", {})

        # Reasoning / thinking
        reasoning = msg.get("reasoning_content", "")
        if reasoning:
            print(f"\n--- reasoning ({len(reasoning)} chars) ---")
            print(reasoning[:2000])
            if len(reasoning) > 2000:
                print(f"    ... ({len(reasoning) - 2000} more chars)")
        else:
            print("\n--- reasoning: (none) ---")

        # Main content
        content = msg.get("content", "")
        print(f"\n--- content ({len(content)} chars) ---")
        print(content)

        # Usage
        usage = data.get("usage", {})
        print(f"\n  usage: prompt_tokens={usage.get('prompt_tokens','?')}  completion_tokens={usage.get('completion_tokens','?')}  total={usage.get('total_tokens','?')}")

        # Finish reason
        print(f"  finish_reason: {choice.get('finish_reason', '?')}")

    except httpx.HTTPStatusError as e:
        print(f"  ERROR {e.response.status_code}: {e.response.text[:500]}")
    except Exception as e:
        print(f"  ERROR: {e}")


for model in MODELS:
    # Reasoning OFF — explicitly disable (GLM-5 defaults to enabled)
    call(f"{model} — REASONING OFF", model, {
        "thinking": {"type": "disabled"},
        "temperature": 0.8,
    })

    # Reasoning ON — Z.AI default for GLM-5
    call(f"{model} — REASONING ON", model, {
        "thinking": {"type": "enabled"},
    }, max_tokens=128000)
