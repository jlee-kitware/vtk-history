"""OpenAI chat for the review agent, returning messages in the shape Ollama's /api/chat returns.

A model name starting with gpt- or o<digit> goes to OpenAI; the key comes from OPENAI_API_KEY (or OPENAI_AI_KEY) in
the environment or the repository's .env. Token use is appended to data/logs/openai_usage.jsonl, and calls stop
once the logged cost reaches OPENAI_BUDGET_USD (default 2).
"""

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL = "https://api.openai.com/v1/chat/completions"
USAGE_LOG = ROOT / "data/logs/openai_usage.jsonl"
# USD per 1M tokens: input, cached input, output (OpenAI list prices, August 2026)
PRICES = {"gpt-5.5": (5.0, 0.5, 30.0), "gpt-5.4": (2.5, 0.25, 15.0), "gpt-5.4-mini": (0.75, 0.075, 4.5),
          "gpt-5.4-nano": (0.2, 0.02, 1.25), "gpt-5-mini": (0.25, 0.025, 2.0)}


class BudgetExceeded(RuntimeError):
    pass


def cost(rec):
    model = max((m for m in PRICES if rec["model"].startswith(m)), key=len, default=None)
    if model is None:
        return rec["prompt"] * 5e-6 + rec["completion"] * 30e-6
    i, c, o = PRICES[model]
    return ((rec["prompt"] - rec["cached"]) * i + rec["cached"] * c + rec["completion"] * o) / 1e6


def spent():
    if not USAGE_LOG.exists():
        return 0.0
    return sum(cost(json.loads(line)) for line in USAGE_LOG.read_text().splitlines() if line.strip())


def is_openai(model):
    return bool(re.match(r"(gpt-|o\d)", model or ""))


def _key():
    for name in ("OPENAI_API_KEY", "OPENAI_AI_KEY"):
        if os.environ.get(name):
            return os.environ[name].strip()
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            name, _, value = line.partition("=")
            if name.strip() in ("OPENAI_API_KEY", "OPENAI_AI_KEY") and value.strip():
                return value.strip().strip("'\"")
    raise RuntimeError("no OpenAI key in the environment or .env")


def _to_openai(messages):
    out, pending = [], []
    for m in messages:
        role = m["role"]
        if role == "assistant" and m.get("tool_calls"):
            calls = []
            for i, c in enumerate(m["tool_calls"]):
                fn = c.get("function", {})
                args = fn.get("arguments") or {}
                cid = c.get("id") or f"call_{len(out)}_{i}"
                calls.append({"id": cid, "type": "function",
                              "function": {"name": fn.get("name"),
                                           "arguments": args if isinstance(args, str) else json.dumps(args)}})
            pending = [c["id"] for c in calls]
            out.append({"role": "assistant", "content": m.get("content") or None, "tool_calls": calls})
        elif role == "tool":
            cid = pending.pop(0) if pending else None
            if cid:
                out.append({"role": "tool", "tool_call_id": cid, "content": m.get("content") or ""})
        else:
            out.append({"role": role, "content": m.get("content") or ""})
    return out


def chat(model, messages, tools=None, json_mode=False, label=""):
    budget = float(os.environ.get("OPENAI_BUDGET_USD", "2"))
    if spent() >= budget:
        raise BudgetExceeded(f"OpenAI spending reached ${spent():.2f} of the ${budget:.2f} budget")
    payload = {"model": model, "messages": _to_openai(messages)}
    if tools:
        payload["tools"] = tools
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {_key()}"}
    for attempt in range(4):
        try:
            req = urllib.request.Request(URL, json.dumps(payload).encode(), headers)
            body = json.load(urllib.request.urlopen(req, timeout=600))
            break
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:300]
            print(f"  OpenAI call failed ({e.code}: {detail}); retrying", file=sys.stderr)
            if e.code in (400, 401, 403, 404):
                return {"role": "assistant", "content": ""}
            time.sleep(20 * (attempt + 1))
        except (OSError, json.JSONDecodeError) as e:
            print(f"  OpenAI call failed ({e}); retrying", file=sys.stderr)
            time.sleep(20 * (attempt + 1))
    else:
        return {"role": "assistant", "content": ""}
    usage = body.get("usage") or {}
    USAGE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(USAGE_LOG, "a") as f:
        f.write(json.dumps({"t": time.strftime("%Y-%m-%dT%H:%M:%S"), "model": model, "label": label,
                            "prompt": usage.get("prompt_tokens", 0),
                            "cached": (usage.get("prompt_tokens_details") or {}).get("cached_tokens", 0),
                            "completion": usage.get("completion_tokens", 0)}) + "\n")
    msg = body["choices"][0]["message"]
    calls = [{"id": c["id"], "function": {"name": c["function"]["name"], "arguments": c["function"]["arguments"]}}
             for c in msg.get("tool_calls") or []]
    return {"role": "assistant", "content": msg.get("content") or "", **({"tool_calls": calls} if calls else {})}
