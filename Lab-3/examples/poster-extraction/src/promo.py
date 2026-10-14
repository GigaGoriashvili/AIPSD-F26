"""Promo art for an accepted event.

The model paints the mood; it never writes the facts. Title, date and
room are overlaid by us with our fonts, so a typo in the art can never
reach a student. People, logos and photoreal content are refused before
any model call: the check is a brief string test, cheap and offline.
"""

import base64
import hashlib
import io
import os

from PIL import Image, ImageDraw, ImageFont

from .llm import client
from .review import Event

BANNED = ("face", "person", "student", "logo", "kiu", "photo of", "realistic")


class PromoRejected(Exception):
    pass


def stable_seed(event_id: str) -> int:
    return int(hashlib.sha256(event_id.encode()).hexdigest()[:8], 16)


def generate_image(model: str, prompt: str, aspect: str, seed: int) -> bytes:
    """Ask OpenRouter for one image and return its PNG bytes.

    Image models answer through the same chat completions endpoint with
    modalities ["image", "text"]; the picture comes back base64 in
    message.images[0].image_url.url. Tests monkeypatch this function.
    """
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        modalities=["image", "text"],
        extra_body={"image_config": {"aspect_ratio": aspect}, "seed": seed},
    )
    msg = resp.choices[0].message
    images = getattr(msg, "images", None) or msg.model_extra.get("images") or []
    if not images:
        raise RuntimeError("image model returned no image")
    url = images[0]["image_url"]["url"]
    return base64.b64decode(url.split(",", 1)[1])


def overlay_text(img_bytes: bytes, title: str, when_where: str) -> bytes:
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    w, h = img.size
    draw = ImageDraw.Draw(img)
    band_top = int(h * 0.78)
    draw.rectangle([0, band_top, w, h], fill=(5, 9, 19))
    draw.text((w * 0.06, band_top + h * 0.04), title, fill="white",
              font=ImageFont.load_default(size=max(18, w // 16)))
    draw.text((w * 0.06, band_top + h * 0.13), when_where, fill=(200, 210, 230),
              font=ImageFont.load_default(size=max(12, w // 28)))
    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()


def watermark(img_bytes: bytes, text: str) -> bytes:
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    w, h = img.size
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=max(10, w // 40))
    draw.text((w * 0.03, h * 0.015), text, fill=(255, 255, 255), font=font)
    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()


def promo_image(event: Event) -> bytes:
    brief = f"{event.theme_words}, flat illustration, bold shapes, warm light"
    if any(b in brief.lower() for b in BANNED):
        raise PromoRejected("brief would generate people, logos or photoreal content")
    img = generate_image(
        model=os.environ.get("CAMPUSPULSE_IMAGE_MODEL", "google/gemini-3.1-flash-image"),
        prompt=brief + ". No text, no people, no logos.",
        aspect="4:5", seed=stable_seed(event.id),
    )
    img = overlay_text(img, event.title, event.when_where)   # our fonts, our facts
    return watermark(img, "AI-generated art")
