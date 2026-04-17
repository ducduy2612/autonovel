#!/usr/bin/env python3
"""Compare GLM-5 vs GLM-5.1, each with reasoning=high and reasoning=off."""
import json
import httpx
from config import API_KEY, API_BASE

PROMPT = "Viết một đoạn văn khoảng 100 chữ tả cảnh một người lạ bước vào quán rượu làng giữa cơn bão. Chữ nghĩa văn chương, tả thực, không sáo rỗng."
SYSTEM = "Bạn là nhà văn văn học Việt Nam. Viết bằng tiếng Việt tự nhiên, đậm chất văn chương. Tránh văn dịch, dùng thành ngữ và cách nói thuần Việt."

HEADERS = {
    "x-api-key": API_KEY,
    "anthropic-version": "2023-06-01",
    "content-type": "application/json",
}

# Models to compare
MODELS = ["GLM-5", "GLM-5.1"]


def call(label, model, extra_payload):
    payload = {
        "model": model,
        "max_tokens": 2048,
        "system": SYSTEM,
        "messages": [{"role": "user", "content": PROMPT}],
    }
    payload.update(extra_payload)
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"  model={model}  extra_keys={list(extra_payload.keys())}")
    print(f"{'='*60}")
    try:
        resp = httpx.post(
            f"{API_BASE}/v1/messages",
            headers=HEADERS,
            json=payload,
            timeout=180,
        )
        resp.raise_for_status()
        data = resp.json()

        # Show content blocks
        for i, block in enumerate(data.get("content", [])):
            btype = block.get("type", "?")
            if btype == "thinking":
                text = block.get("thinking", "")
                print(f"\n--- thinking block [{i}] ({len(text)} chars) ---")
                print(text[:2000] if text else "(empty)")
            elif btype == "text":
                text = block.get("text", "")
                print(f"\n--- text block [{i}] ({len(text)} chars) ---")
                print(text)
            else:
                print(f"\n--- {btype} block [{i}] ---")
                print(json.dumps(block, indent=2)[:1000])

        # Show usage
        usage = data.get("usage", {})
        print(f"\n  usage: input={usage.get('input_tokens','?')}  output={usage.get('output_tokens','?')}")
        if usage.get("cache_creation_input_tokens"):
            print(f"         cache_create={usage['cache_creation_input_tokens']}")
        if usage.get("cache_read_input_tokens"):
            print(f"         cache_read={usage['cache_read_input_tokens']}")

    except httpx.HTTPStatusError as e:
        print(f"  ERROR {e.response.status_code}: {e.response.text[:500]}")
    except Exception as e:
        print(f"  ERROR: {e}")


for model in MODELS:
    call(f"{model} — REASONING OFF", model, {"temperature": 0.8})

    call(f"{model} — REASONING HIGH", model, {
        "thinking": {"type": "enabled", "budget_tokens": 10000},
    })
