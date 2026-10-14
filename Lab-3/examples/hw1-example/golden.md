# HW1 golden questions · Next three events for a club

Run on 5 October 2026 with `python -m src.next_events <club> --today 2026-10-05`. Seed data: `src/data/events.json` (updated 2026-10-01).

| # | Question (input) | Expected | Actual | Pass? | How I ran it |
|---|---|---|---|---|---|
| 1 | `"Robotics Club"` | three events: Open Build Night 2026-10-22 18:00 B204; Soldering 101 2026-10-29 17:00 B204; Robot Sumo 2026-11-12 16:00 Atrium | exactly those three, in that order | pass | command above; also `tests/test_next_events.py::test_three_sorted` |
| 2 | `"Chess Club"` (its only event was 2026-09-30) | `[]`, exit code 0, message "No upcoming events for Chess Club" | `[]`, exit 0, message as expected | pass | command above |
| 3 | `"Robotic Club"` (typo) | `UnknownClub` raised, message names three clubs including Robotics Club, exit code 1 | `Unknown club 'Robotic Club': did you mean Robotics Club, Rowing Club, Radio Club?`, exit 1 | pass | command above; the spec does not fix the order of suggestions, so the test checks the count and that Robotics Club is present |

What I learned from running them: question 3 first returned only one suggestion because the agent used an exact prefix match. I added the test, the agent switched to `difflib.get_close_matches`, and the three suggestions appeared.
