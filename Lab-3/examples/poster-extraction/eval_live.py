"""Live evaluation against the four posters. Costs money, needs a key.

    OPENROUTER_API_KEY=... python eval_live.py            # all four posters
    OPENROUTER_API_KEY=... python eval_live.py torn.png   # one poster

For each poster: runs extract() twice, decides, prints route, flags,
fields that disagreed between the two runs, and the usage line. Then
compares route and hard set against expected.json. Exit code 1 on any
mismatch, so you can put it in CI behind a manual trigger.
"""

import json
import os
import sys
from datetime import date
from pathlib import Path

from src.checks import decide
from src.extract import disagreements, extract
from src.llm import LOG_PATH

HERE = Path(__file__).parent


def last_usage_line() -> str:
    try:
        return LOG_PATH.read_text().strip().splitlines()[-1]
    except (FileNotFoundError, IndexError):
        return "(no usage line written)"


def main() -> int:
    if not os.environ.get("OPENROUTER_API_KEY"):
        print("OPENROUTER_API_KEY is not set. Copy .env.example to .env and export it.")
        return 2
    expected = json.loads((HERE / "expected.json").read_text())
    today = date.fromisoformat(expected["today"])
    rooms = set(json.loads((HERE / "rooms.json").read_text()))
    failures = 0

    only = set(sys.argv[1:])
    for name, want in expected["posters"].items():
        if only and name not in only:
            continue
        img = (HERE / "posters" / name).read_bytes()
        a = extract(img)
        b = extract(img)
        d = decide(a, today, rooms)
        print(f"\n== {name}")
        print(f"   route    {d.route}   expected {want['route']}")
        print(f"   flags    {d.flags}")
        print(f"   hard     {sorted(d.hard)}   expected {want['hard']}")
        print(f"   disagree {disagreements(a, b)}")
        for n in ("title", "date", "time", "location", "organizer"):
            fld = getattr(a, n)
            print(f"   {n:9} {fld.value!r:28} evidence={fld.evidence!r} conf={fld.confidence:.2f}")
        print(f"   usage    {last_usage_line()}")
        if d.route != want["route"] or sorted(d.hard) != sorted(want["hard"]):
            print("   MISMATCH")
            failures += 1

    ran = len(only) if only else len(expected['posters'])
    print(f"\n{ran - failures}/{ran} posters matched expected.json")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
