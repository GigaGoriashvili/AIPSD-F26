"""Hand-written extractions that stand in for what the model would return.

No test in this folder calls a model. These fixtures are what we expect
a good vision model to say about the four posters in posters/.
"""

from datetime import date

import pytest

from src.extract import Extraction, Field

TODAY = date(2026, 10, 5)
ROOMS = {"A101", "A102", "B204", "B205", "C310", "Library", "Main Hall"}


def f(value, evidence=None, confidence=0.95):
    if evidence is None and value is not None:
        evidence = value
    return Field(value=value, evidence=evidence, confidence=confidence)


@pytest.fixture
def today():
    return TODAY


@pytest.fixture
def rooms():
    return set(ROOMS)


@pytest.fixture
def clean():
    return Extraction(
        title=f("Open Build Night", "OPEN BUILD NIGHT"),
        date=f("2026-10-22", "Thursday 2026-10-22"),
        time=f("18:00"),
        location=f("B204", "Room B204"),
        organizer=f("Robotics Club"),
    )


@pytest.fixture
def torn():
    """Date covered by torn paper. A model that follows the prompt returns null
    for both value and evidence; a model that guesses invents a date. Both
    shapes appear in the tests."""
    return Extraction(
        title=f("Open Build Night", "OPEN BUILD NIGHT", 0.8),
        date=f(None, None, 0.1),
        time=f("18:00", confidence=0.7),
        location=f("B204", "Room B204", 0.75),
        organizer=f("Robotics Club", confidence=0.6),
    )


@pytest.fixture
def ambiguous():
    """Two dates and a room with a letter O. Evidence exists for everything,
    but confidence is low and the room is not on the list."""
    return Extraction(
        title=f("Film Night", "FILM NIGHT"),
        date=f("2026-10-29", "Rescheduled: Oct 29", 0.55),
        time=f("20:00"),
        location=f("B2O4", "Room B2O4", 0.5),
        organizer=f("Student Cinema Society"),
    )


@pytest.fixture
def notice():
    return Extraction(
        title=f("Quiet Hours", "QUIET HOURS"),
        date=f(None, None, 0.0),
        time=f("22:00", "22:00 to 08:00", 0.9),
        location=f("Library"),
        organizer=f("Library Services", confidence=0.7),
    )
