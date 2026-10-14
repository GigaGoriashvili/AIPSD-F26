from datetime import date
import pytest
from src import next_events as ne

TODAY = date(2026, 10, 5)


def test_three_sorted():
    ev = ne.next_events("Robotics Club", TODAY)
    assert [e.title for e in ev] == ["Open Build Night", "Soldering 101", "Robot Sumo"]
    assert all(date.fromisoformat(e.date) >= TODAY for e in ev)


def test_fields_non_empty():
    for e in ne.next_events("Robotics Club", TODAY):
        assert e.title and e.date and e.time and e.room


def test_no_upcoming_is_empty_list():
    assert ne.next_events("Chess Club", TODAY) == []


def test_case_insensitive():
    assert ne.next_events("robotics club", TODAY)


def test_unknown_club_suggests_three():
    with pytest.raises(ne.UnknownClub) as exc:
        ne.next_events("Robotic Club", TODAY)
    assert "Robotics Club" in str(exc.value)
    assert str(exc.value).count(",") == 2


def test_same_day_sorted_by_time():
    ev = ne.next_events("Rowing Club", TODAY)
    assert [e.time for e in ev] == ["06:30", "07:00"]


def test_stale_warning_logic():
    assert not ne.data_is_stale(date(2026, 10, 10))
    assert ne.data_is_stale(date(2026, 11, 10))
