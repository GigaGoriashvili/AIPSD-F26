"""Review queue: where anything short of 'accepted' waits for a human.

The one rule on the review page: never prefill a guess. A hard field
(missing or unsupported by evidence) is blanked in the Draft so the
reviewer types what the poster says instead of clicking OK on fiction.
Soft fields stay prefilled but are highlighted in the UI.

Only two things produce an Event: an accepted Decision, or a resolved
Draft. Everything else stays a Draft.
"""

import hashlib
import itertools
from dataclasses import dataclass, field

from .checks import Decision
from .extract import Extraction, FIELDS

STOPWORDS = {"the", "a", "an", "of", "and", "for", "to", "in", "at", "night", "day", "club"}


@dataclass
class Event:
    title: str
    date: str
    time: str | None
    location: str
    organizer: str | None
    source_image: str

    @property
    def id(self) -> str:
        key = f"{self.title}|{self.date}|{self.location}".lower()
        return hashlib.sha256(key.encode()).hexdigest()[:12]

    @property
    def when_where(self) -> str:
        bits = [self.date, self.time, self.location]
        return " · ".join(b for b in bits if b)

    @property
    def theme_words(self) -> str:
        """Content words from the title, for the promo image brief.
        Facts (date, room, organizer) never go in; those are overlaid as text."""
        words = [w.strip(".,:!") for w in self.title.lower().split()]
        return ", ".join(w for w in words if w and w not in STOPWORDS) or "campus event"


@dataclass
class Draft:
    id: str
    image_name: str
    decision: Decision
    fields: dict[str, str | None]            # hard fields are None here
    evidence: dict[str, str | None]
    confidence: dict[str, float]


def event_from(x: Extraction, image_name: str) -> Event:
    return Event(
        title=x.title.value, date=x.date.value, time=x.time.value,
        location=x.location.value, organizer=x.organizer.value,
        source_image=image_name,
    )


class ReviewQueue:
    def __init__(self) -> None:
        self._drafts: dict[str, Draft] = {}
        self._ids = itertools.count(1)

    def add(self, extraction: Extraction, decision: Decision, image_name: str) -> Draft:
        fields = {n: getattr(extraction, n).value for n in FIELDS}
        for name in decision.hard:
            fields[name] = None                # never prefill a guess
        draft = Draft(
            id=f"d{next(self._ids)}",
            image_name=image_name,
            decision=decision,
            fields=fields,
            evidence={n: getattr(extraction, n).evidence for n in FIELDS},
            confidence={n: getattr(extraction, n).confidence for n in FIELDS},
        )
        self._drafts[draft.id] = draft
        return draft

    def get(self, draft_id: str) -> Draft | None:
        return self._drafts.get(draft_id)

    def pending(self) -> list[Draft]:
        return list(self._drafts.values())

    def resolve(self, draft_id: str, corrections: dict) -> Event:
        draft = self._drafts[draft_id]
        merged = {**draft.fields, **{k: (v or None) for k, v in corrections.items()}}
        for name in ("title", "date", "location"):
            if not merged.get(name):
                raise ValueError(f"{name} is required to publish an event")
        del self._drafts[draft_id]
        return Event(
            title=merged["title"], date=merged["date"], time=merged.get("time"),
            location=merged["location"], organizer=merged.get("organizer"),
            source_image=draft.image_name,
        )
