import pytest

from src.checks import decide
from src.extract import Field
from src.review import Event, ReviewQueue, event_from


def test_hard_fields_are_blanked_in_draft(torn, today, rooms):
    torn.date = Field(value="2025-10-22", evidence=None, confidence=0.4)   # a guess
    q = ReviewQueue()
    draft = q.add(torn, decide(torn, today, rooms), "torn.png")
    assert draft.fields["date"] is None            # never prefill a guess
    assert draft.fields["title"] == "Open Build Night"
    assert q.pending() == [draft]


def test_soft_fields_stay_prefilled(ambiguous, today, rooms):
    q = ReviewQueue()
    draft = q.add(ambiguous, decide(ambiguous, today, rooms), "ambiguous.png")
    assert draft.fields["location"] == "B2O4"
    assert draft.decision.hard == set()


def test_resolve_yields_event_and_clears_queue(torn, today, rooms):
    q = ReviewQueue()
    draft = q.add(torn, decide(torn, today, rooms), "torn.png")
    ev = q.resolve(draft.id, {"date": "2026-10-22"})
    assert isinstance(ev, Event)
    assert ev.date == "2026-10-22" and ev.location == "B204"
    assert ev.source_image == "torn.png"
    assert q.pending() == []


def test_resolve_refuses_blank_required_field(torn, today, rooms):
    q = ReviewQueue()
    draft = q.add(torn, decide(torn, today, rooms), "torn.png")
    with pytest.raises(ValueError):
        q.resolve(draft.id, {"date": ""})


def test_accepted_becomes_event_directly(clean, today, rooms):
    assert decide(clean, today, rooms).route == "accepted"
    ev = event_from(clean, "clean.png")
    assert ev.title == "Open Build Night"
    assert ev.when_where == "2026-10-22 · 18:00 · B204"
    assert "open" in ev.theme_words and "build" in ev.theme_words
    assert len(ev.id) == 12 and ev.id == event_from(clean, "other.png").id
