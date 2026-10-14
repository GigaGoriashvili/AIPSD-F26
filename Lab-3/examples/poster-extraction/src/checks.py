"""Deterministic checks on top of the model's extraction.

This file is the Week 3 pattern: Extract, then Verify. The model reads;
code decides. decide() is a pure function: no network, no clock of its
own (today comes in as an argument), no file access. That is what makes
it testable with hand-written fixtures and safe to run on every upload.

Routes, from best to worst:
  accepted   every required field has a value, evidence, and confidence
  confirm    soft problems only; show the user prefilled fields to confirm
  review     something required is missing or unsupported; a human fills it
  rejected   this is not an event poster at all
"""

from dataclasses import dataclass, field
from datetime import date

from .extract import Extraction

REQUIRED = ("title", "date", "location")

# Words that mark a notice rather than an event. Matched against the
# title evidence, lowercased.
NOT_EVENT_WORDS = ("quiet hours", "notice", "out of order", "wifi", "maintenance")

REASON_TEXT = {
    "missing": "{F}: the model could not read it",
    "no_evidence": "{F}: the model gave a value but no readable text to support it",
    "low_confidence": "{F}: the model read it but is not sure",
    "in_the_past": "{F}: this date is already behind us",
    "unparseable_date": "{F}: the date is not in YYYY-MM-DD form",
    "unknown_room": "{F}: this room is not on the campus room list",
}


@dataclass
class Decision:
    route: str                                   # accepted, confirm, review, rejected
    flags: list[tuple[str, str]]                 # (kind, field_name)
    hard: set[str] = field(default_factory=set)  # fields a human must fill, never prefilled

    def reasons(self) -> list[str]:
        return [REASON_TEXT.get(k, "{F}: " + k).format(F=n.capitalize()) for k, n in self.flags]


def parse_date(value: str) -> date | None:
    """ISO YYYY-MM-DD only. Returns None instead of raising on anything else,
    so decide() can flag it rather than crash on a creative model answer."""
    try:
        return date.fromisoformat(value.strip())
    except (ValueError, AttributeError):
        return None


def looks_like_event(x: Extraction) -> bool:
    if x.title.value is None and x.date.value is None and x.location.value is None:
        return False
    ev = (x.title.evidence or "").lower()
    return not any(w in ev for w in NOT_EVENT_WORDS)


def decide(x: Extraction, today: date, rooms: set[str]) -> Decision:
    flags: list[tuple[str, str]] = []
    for name in REQUIRED:
        f = getattr(x, name)
        if f.value is None:                     flags.append(("missing", name))
        elif f.evidence is None:                flags.append(("no_evidence", name))
        elif f.confidence < 0.6:                flags.append(("low_confidence", name))
    if x.date.value and parse_date(x.date.value) is None:
        flags.append(("unparseable_date", "date"))
    elif x.date.value and parse_date(x.date.value) < today:
        flags.append(("in_the_past", "date"))
    if x.location.value and x.location.value not in rooms:
        flags.append(("unknown_room", "location"))

    if not looks_like_event(x):                        return Decision("rejected", flags)
    if any(k in ("missing", "no_evidence") for k, _ in flags):
        return Decision("review", flags, hard={n for k, n in flags if k != "low_confidence"})
    if flags:                                          return Decision("confirm", flags)
    return Decision("accepted", flags)
