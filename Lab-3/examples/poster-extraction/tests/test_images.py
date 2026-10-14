import io

from PIL import Image

from src.images import approx_image_tokens, downscale


def png(w, h):
    buf = io.BytesIO()
    Image.new("RGBA", (w, h), (200, 30, 30, 255)).save(buf, format="PNG")
    return buf.getvalue()


def test_downscale_caps_longest_side_and_keeps_ratio():
    out = Image.open(io.BytesIO(downscale(png(3000, 4000))))
    assert max(out.size) == 1024
    assert out.size == (768, 1024)


def test_downscale_never_upscales():
    out = Image.open(io.BytesIO(downscale(png(400, 300))))
    assert out.size == (400, 300)


def test_downscale_returns_rgb_jpeg():
    data = downscale(png(800, 1100))
    assert data[:2] == b"\xff\xd8"
    out = Image.open(io.BytesIO(data))
    assert out.format == "JPEG" and out.mode == "RGB"


def test_approx_tokens_grows_with_tiles():
    assert approx_image_tokens(700, 700) == 258
    assert approx_image_tokens(768, 1024) == 2 * 258
