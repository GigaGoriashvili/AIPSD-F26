"""Next three upcoming events for a club. No network, no model call.

Run:  python -m src.next_events "Robotics Club" [--today YYYY-MM-DD]
"""
from __future__ import annotations
import difflib, json, sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

DATA = Path(__file__).parent / "data" / "events.json"
STALE_AFTER = timedelta(days=14)


class UnknownClub(ValueError):
    pass


@dataclass(frozen=True)
class Event:
    title: str
    date: str   # ISO
    time: str   # HH:MM
    room: str


_events: list[dict] = []
_updated: date | None = None


def reload(path: Path = DATA) -> None:
    global _events, _updated
    raw = json.loads(path.read_text())
    _events = raw["events"]
    _updated = date.fromisoformat(raw["updated"])


def clubs() -> list[str]:
    return sorted({e["club"] for e in _events})


def next_events(club: str, today: date, limit: int = 3) -> list[Event]:
    if not _events:
        reload()
    names = clubs()
    match = next((n for n in names if n.lower() == club.strip().lower()), None)
    if match is None:
        close = difflib.get_close_matches(club, names, n=3, cutoff=0.0)
        raise UnknownClub(f"Unknown club {club!r}: did you mean {', '.join(close)}?")
    upcoming = [e for e in _events if e["club"] == match and date.fromisoformat(e["date"]) >= today]
    upcoming.sort(key=lambda e: (e["date"], e["time"]))
    return [Event(e["title"], e["date"], e["time"], e["room"]) for e in upcoming[:limit]]


def data_is_stale(today: date) -> bool:
    if not _events:
        reload()
    return _updated is not None and today - _updated > STALE_AFTER


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__); return 2
    club = argv[0]
    today = date.fromisoformat(argv[argv.index("--today") + 1]) if "--today" in argv else date.today()
    if data_is_stale(today):
        print(f"warning: events.json was updated on {_updated}; it may be out of date", file=sys.stderr)
    try:
        events = next_events(club, today)
    except UnknownClub as e:
        print(e, file=sys.stderr); return 1
    if not events:
        print(f"No upcoming events for {club}"); return 0
    for e in events:
        print(f"{e.date} {e.time}  {e.title}  ({e.room})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
