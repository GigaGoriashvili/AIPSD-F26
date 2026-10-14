import io

import pytest
from PIL import Image
from pydantic import ValidationError

from src import extract as ex
from src.extract import Extraction, Field, disagreements


def good_payload(**overrides):
    base = {n: {"value": v, "evidence": v, "confidence": 0.9} for n, v in {
        "title": "Open Build Night", "date": "2026-10-22", "time": "18:00",
        "location": "B204", "organizer": "Robotics Club"}.items()}
    base.update(overrides)
    return base


def test_rejects_confidence_as_string():
    with pytest.raises(ValidationError):
        Extraction.model_validate(good_payload(
            title={"value": "x", "evidence": "x", "confidence": "high"}))


def test_rejects_confidence_out_of_range():
    with pytest.raises(ValidationError):
        Field(value="x", evidence="x", confidence=1.4)
    with pytest.raises(ValidationError):
        Field(value="x", evidence="x", confidence=-0.1)


def test_rejects_missing_field():
    payload = good_payload()
    del payload["organizer"]
    with pytest.raises(ValidationError):
        Extraction.model_validate(payload)


def test_extract_with_fake_complete_json(monkeypatch):
    seen = {}

    def fake(prompt, image, schema):
        seen.update(prompt=prompt, image=image, schema=schema)
        return good_payload()

    monkeypatch.setattr(ex, "complete_json", fake)
    buf = io.BytesIO()
    Image.new("RGB", (1600, 2200), "white").save(buf, format="PNG")
    x = ex.extract(buf.getvalue())
    assert x.title.value == "Open Build Night"
    assert seen["prompt"] == ex.PROMPT
    assert seen["schema"]["title"] == "Extraction"
    assert seen["image"][:2] == b"\xff\xd8"           # downscaled to JPEG before sending


def test_extract_raises_on_wrong_shape(monkeypatch):
    monkeypatch.setattr(ex, "complete_json", lambda *a, **k: {"title": "just a string"})
    buf = io.BytesIO()
    Image.new("RGB", (100, 100)).save(buf, format="PNG")
    with pytest.raises(ValidationError):
        ex.extract(buf.getvalue())


def test_disagreements_names_fields_that_flip(clean, ambiguous):
    assert disagreements(clean, clean) == []
    second = clean.model_copy(deep=True)
    second.date = Field(value="2026-10-29", evidence="Oct 29", confidence=0.6)
    assert disagreements(clean, second) == ["date"]
    assert set(disagreements(clean, ambiguous)) == {"title", "date", "time", "location", "organizer"}
