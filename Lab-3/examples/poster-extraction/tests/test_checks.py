from datetime import date

from src.checks import Decision, decide, looks_like_event, parse_date
from src.extract import Field


def kinds(d: Decision) -> list[tuple[str, str]]:
    return d.flags


def test_clean_is_accepted(clean, today, rooms):
    d = decide(clean, today, rooms)
    assert d.route == "accepted"
    assert d.flags == [] and d.hard == set()


def test_torn_goes_to_review_with_hard_date(torn, today, rooms):
    d = decide(torn, today, rooms)
    assert d.route == "review"
    assert ("missing", "date") in d.flags
    assert d.hard == {"date"}


def test_ambiguous_asks_for_confirmation(ambiguous, today, rooms):
    d = decide(ambiguous, today, rooms)
    assert d.route == "confirm"
    assert ("low_confidence", "date") in d.flags
    assert ("low_confidence", "location") in d.flags
    assert ("unknown_room", "location") in d.flags
    assert d.hard == set()


def test_notice_is_rejected(notice, today, rooms):
    assert decide(notice, today, rooms).route == "rejected"


def test_all_three_required_fields_null_is_rejected(clean, today, rooms):
    for n in ("title", "date", "location"):
        setattr(clean, n, Field(value=None, evidence=None, confidence=0.0))
    assert not looks_like_event(clean)
    assert decide(clean, today, rooms).route == "rejected"


def test_value_without_evidence_is_hard(clean, today, rooms):
    clean.location = Field(value="B204", evidence=None, confidence=0.99)
    d = decide(clean, today, rooms)
    assert d.route == "review"
    assert ("no_evidence", "location") in d.flags
    assert "location" in d.hard


def test_evidence_is_checked_before_confidence(clean, today, rooms):
    # No evidence and low confidence at once: the flag is no_evidence, not
    # low_confidence. Unsupported beats unsure.
    clean.title = Field(value="Open Build Night", evidence=None, confidence=0.2)
    d = decide(clean, today, rooms)
    assert ("no_evidence", "title") in d.flags
    assert ("low_confidence", "title") not in d.flags


def test_torn_poster_with_invented_past_date(torn, today, rooms):
    # A guessing model fills the torn date with something plausible but old.
    torn.date = Field(value="2025-10-22", evidence=None, confidence=0.4)
    d = decide(torn, today, rooms)
    assert d.route == "review"
    assert ("no_evidence", "date") in d.flags
    assert ("in_the_past", "date") in d.flags
    assert d.hard == {"date"}


def test_hard_set_excludes_low_confidence_but_keeps_other_flags(clean, today, rooms):
    clean.date = Field(value=None, evidence=None, confidence=0.0)
    clean.location = Field(value="Z999", evidence="Room Z999", confidence=0.4)
    d = decide(clean, today, rooms)
    assert d.route == "review"
    # low_confidence on location is soft; unknown_room on location is not
    assert d.hard == {"date", "location"}


def test_unknown_room_alone_is_confirm(clean, today, rooms):
    clean.location = Field(value="Z999", evidence="Room Z999", confidence=0.9)
    d = decide(clean, today, rooms)
    assert d.route == "confirm"
    assert d.flags == [("unknown_room", "location")]


def test_past_date_alone_is_confirm(clean, rooms):
    d = decide(clean, date(2026, 11, 1), rooms)
    assert d.route == "confirm"
    assert d.flags == [("in_the_past", "date")]


def test_unparseable_date_is_flagged_not_raised(clean, today, rooms):
    clean.date = Field(value="next Thursday", evidence="next Thursday", confidence=0.9)
    d = decide(clean, today, rooms)
    assert ("unparseable_date", "date") in d.flags
    assert ("in_the_past", "date") not in d.flags
    assert d.route == "confirm"


def test_parse_date_returns_none_on_garbage():
    assert parse_date("2026-10-22") == date(2026, 10, 22)
    assert parse_date("22/10/2026") is None
    assert parse_date("") is None


def test_reasons_wording(torn, today, rooms):
    torn.date = Field(value="2026-10-22", evidence=None, confidence=0.9)
    d = decide(torn, today, rooms)
    assert "Date: the model gave a value but no readable text to support it" in d.reasons()
    assert len(d.reasons()) == len(d.flags)


def test_decide_is_pure(clean, today, rooms):
    before = clean.model_dump()
    decide(clean, today, rooms)
    assert clean.model_dump() == before
