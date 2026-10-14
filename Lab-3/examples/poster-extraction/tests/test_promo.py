import io

import pytest
from PIL import Image

from src import promo
from src.promo import PromoRejected, promo_image, stable_seed
from src.review import Event


def event(title="Open Build Night"):
    return Event(title=title, date="2026-10-22", time="18:00", location="B204",
                 organizer="Robotics Club", source_image="clean.png")


def fake_png(w=800, h=1000):
    buf = io.BytesIO()
    Image.new("RGB", (w, h), (240, 180, 90)).save(buf, format="PNG")
    return buf.getvalue()


def test_banned_brief_is_refused_before_any_model_call(monkeypatch):
    calls = []
    monkeypatch.setattr(promo, "generate_image", lambda **kw: calls.append(kw) or fake_png())
    with pytest.raises(PromoRejected):
        promo_image(event("Student Photo Booth Night"))
    assert calls == []


def test_happy_path_returns_png_with_facts_overlaid(monkeypatch):
    seen = {}

    def fake(model, prompt, aspect, seed):
        seen.update(model=model, prompt=prompt, aspect=aspect, seed=seed)
        return fake_png()

    monkeypatch.setattr(promo, "generate_image", fake)
    out = promo_image(event())
    assert out[:8] == b"\x89PNG\r\n\x1a\n"
    assert Image.open(io.BytesIO(out)).size == (800, 1000)
    assert "No text, no people, no logos." in seen["prompt"]
    assert "2026-10-22" not in seen["prompt"]      # facts are ours, not the model's
    assert seen["aspect"] == "4:5"
    assert seen["seed"] == stable_seed(event().id)


def test_stable_seed_is_deterministic():
    assert stable_seed("abc") == stable_seed("abc")
    assert stable_seed("abc") != stable_seed("abd")
