"""The only file that talks to a model.

Week 2 gave us complete(); Week 3 adds complete_json(), which sends an
image and asks for a strict JSON schema back. Every call writes one usage
line so cost and latency are never a surprise.

The client is built lazily: importing this module needs no key, and the
tests monkeypatch complete_json so they never reach this far.
"""

import base64
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from openai import OpenAI

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
LOG_PATH = Path(os.environ.get("CAMPUSPULSE_USAGE_LOG", "logs/usage.jsonl"))

# USD per million tokens (input, output). Verified 4 October 2026, promotional.
# verify live before you ship
PRICES = {
    "google/gemini-3.8-flash": (0.75, 3.75),
}

_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        key = os.environ.get("OPENROUTER_API_KEY")
        if not key:
            raise RuntimeError("OPENROUTER_API_KEY is not set; copy .env.example to .env")
        _client = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=key)
    return _client


class _LazyClient:
    """Lets the on-screen code say client.chat... without building it at import."""

    def __getattr__(self, name):
        return getattr(get_client(), name)


client = _LazyClient()


def data_url(image: bytes) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(image).decode("ascii")


def cost_usd(model: str, tokens_in: int, tokens_out: int) -> float:
    price_in, price_out = PRICES.get(model, (0.0, 0.0))
    return round((tokens_in * price_in + tokens_out * price_out) / 1_000_000, 6)


def log_usage(resp, latency_ms: int = 0) -> dict:
    usage = getattr(resp, "usage", None)
    tokens_in = getattr(usage, "prompt_tokens", 0) or 0
    tokens_out = getattr(usage, "completion_tokens", 0) or 0
    line = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": resp.model,
        "tokens_in": tokens_in,            # includes the image tokens
        "tokens_out": tokens_out,
        "cost_usd": cost_usd(resp.model, tokens_in, tokens_out),
        "latency_ms": latency_ms,
    }
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a") as f:
        f.write(json.dumps(line) + "\n")
    return line


def complete_json(prompt: str, image: bytes, schema: dict) -> dict:
    t0 = time.perf_counter()
    resp = client.chat.completions.create(
        model=os.environ.get("CAMPUSPULSE_MODEL", "google/gemini-3.8-flash"),
        messages=[{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": data_url(image)}}]}],
        response_format={"type": "json_schema",
                         "json_schema": {"name": "extraction", "schema": schema, "strict": True}},
        temperature=0,
    )
    log_usage(resp, latency_ms=int((time.perf_counter() - t0) * 1000))   # tokens_in includes the image
    return json.loads(resp.choices[0].message.content)
