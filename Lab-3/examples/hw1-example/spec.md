# HW1 spec · Next three events for a club

*CampusPulse · individual feature · one page. Run: `pip install -r src/requirements.txt && pytest src` · Try it: `python -m src.next_events "Robotics Club"`*

## Goal

A student types a club name and gets that club's next three upcoming events, soonest first, each with date, start time and room. Nothing else.

## Users

Students deciding whether to go to something this week. They know the club name; they do not know the schedule.

## Acceptance criteria

1. `next_events("Robotics Club", today=2026-10-05)` returns at most three events, all with `date >= today`, sorted by date then start time.
2. Each event has `title`, `date` (ISO), `time` (HH:MM) and `room`; no field is empty.
3. A club with no upcoming events returns an empty list, not an error.
4. An unknown club raises `UnknownClub` with the three closest club names in the message (case-insensitive match, so "robotics club" works).
5. Runs in under 50 ms on the seed file of 200 events; no network, no model call.

## Context the agent needs

- `src/data/events.json`: seed data, fields `club`, `title`, `date`, `time`, `room`.
- `AGENTS.md` at the repo root: conventions, test command, Never lines.
- This file.

## Out of scope

Recurring events, time zones, a web endpoint, events from the extraction pipeline (Lab 3 slice owns that).

## Napkin math

No model call in this feature, so cost is zero per request. If a later slice adds natural-language club matching through a model, budget about 300 input tokens per request.

## Risks

Stale seed data shows an event that was cancelled. Mitigation: the data file carries an `updated` date, and the function warns when it is older than 14 days.
