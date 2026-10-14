"""Poster to structured event: the extraction step.

The model never decides anything here. It reads the image and returns
value, evidence and confidence for each field. Deciding what to do with
that (accept, confirm, review, reject) lives in checks.py, which is pure
and testable without a model.
"""

from pydantic import BaseModel
from pydantic import Field as PField
from .llm import complete_json      # logs model, tokens, cost_usd, latency_ms
from .images import downscale        # longest side 1024 px, JPEG quality 85


class Field(BaseModel):
    value: str | None                # normalised, or null
    evidence: str | None             # exact text read, or null
    confidence: float = PField(ge=0.0, le=1.0)   # 0..1, the model's own estimate


class Extraction(BaseModel):
    title: Field
    date: Field
    time: Field
    location: Field
    organizer: Field


FIELDS = ("title", "date", "time", "location", "organizer")

PROMPT = ("Read this campus poster. For every field return value, evidence "
          "(the exact text you read) and confidence. If you cannot read a "
          "field, set value and evidence to null. Never guess.")


def extract(image_bytes: bytes) -> Extraction:
    img = downscale(image_bytes)
    raw = complete_json(PROMPT, image=img, schema=Extraction.model_json_schema())
    return Extraction.model_validate(raw)   # raises if the shape is wrong


def disagreements(a: Extraction, b: Extraction) -> list[str]:
    """Names of fields whose value differs between two runs.

    Used by the stretch exercise: run extract() twice on the same poster.
    A field that flips between runs is a field the model is not sure about,
    whatever confidence number it reported.
    """
    return [n for n in FIELDS if getattr(a, n).value != getattr(b, n).value]
