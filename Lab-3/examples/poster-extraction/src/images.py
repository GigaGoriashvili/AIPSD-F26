"""Image prep before the model sees anything.

A phone photo of a poster is 3000 px wide and 4 MB. The model does not
read it any better than a 1024 px JPEG, and you pay for every tile.
"""

import io
import math

from PIL import Image


def downscale(image_bytes: bytes, max_side: int = 1024, quality: int = 85) -> bytes:
    """Return JPEG bytes with the longest side at most max_side.

    Converts to RGB (drops alpha, handles PNG and HEIC-decoded input),
    keeps the aspect ratio, and never upscales a small image.
    """
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    w, h = img.size
    scale = max_side / max(w, h)
    if scale < 1:
        img = img.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=quality, optimize=True)
    return out.getvalue()


def approx_image_tokens(w: int, h: int, tile: int = 768, tokens_per_tile: int = 258) -> int:
    """Rough estimate for budgeting only.

    Assumes about 258 tokens per 768x768 tile, which is an approximation
    of how Gemini-family models bill images. Providers change this, and
    small images are often billed as a single tile. Use the tokens_in in
    logs/usage.jsonl as the real number; use this only to plan a budget.
    """
    tiles = math.ceil(w / tile) * math.ceil(h / tile)
    return max(1, tiles) * tokens_per_tile
