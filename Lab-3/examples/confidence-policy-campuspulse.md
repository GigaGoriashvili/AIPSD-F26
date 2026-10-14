# Confidence policy · Poster to event (CampusPulse)

*The Lab 3 template, filled in. `poster-extraction/src/checks.py` implements exactly this table; `tests/test_checks.py` proves it.*

## 1 · Routes

| Route | What it means | What the user sees | What gets created |
|---|---|---|---|
| `accepted` | title, date, location present, evidenced, consistent | the event card with "from the poster you photographed" | an `Event` |
| `confirm` | soft flags only | the card with the flagged value highlighted and one question | a `Draft` until confirmed |
| `review` | at least one hard flag | the review page: flagged fields empty, the photo beside them | a `Draft` in the review queue |
| `rejected` | not a poster for an event | "This looks like a notice, not an event. Photograph the poster itself?" | nothing |

## 2 · Signals, per required field (`title`, `date`, `location`)

| Signal | Condition | Flag | Hard or soft |
|---|---|---|---|
| value present | `value is None` | `missing` | hard |
| evidence present | `evidence is None` | `no_evidence` | hard |
| self-rated confidence | `confidence < 0.6` | `low_confidence` | soft |
| date parses | `date.value` not ISO | `unparseable_date` | soft on its own |
| date is ahead | `date < today` | `in_the_past` | soft on its own |
| room exists | `location not in rooms` | `unknown_room` | soft on its own |
| event-like at all | all three required values null, or the title reads like a notice | (no flag) | `rejected` |

Order: missing, then evidence, then confidence. Evidence is checked before the model's number; that is what catches the torn poster, where the model writes a date with confidence 0.9 and nothing to quote.

"Soft on its own" means: it routes to `confirm` by itself, but when a hard flag is also present the whole extraction goes to `review` and these fields join the hard set, because a reviewer is already looking.

## 3 · From flags to a route

```
not looks_like_event(x)                     → rejected
any missing or no_evidence                  → review   hard = every flagged field except low_confidence
any other flag                              → confirm
no flags                                    → accepted
```

## 4 · The reason text

| Flag | On screen |
|---|---|
| `missing` on date | "Date: not found on the poster" |
| `no_evidence` on date | "Date: we could not find the text this came from" |
| `low_confidence` on location | "We think this is room B204. Check the poster?" |
| `in_the_past` | "This date has already passed. Is the year right?" |
| `unknown_room` | "We do not recognise room B2O4. Pick one from the list?" |
| `unparseable_date` | "We could not read this as a date. Type it in?" |

## 5 · Tests (in `poster-extraction/tests/test_checks.py`, 15 of the 33)

1. Clean extraction → `accepted`, no flags.
2. Torn poster, date null → `review`, hard `{date}`.
3. Torn poster, invented past date with no evidence → `review`, flags include `no_evidence` and `in_the_past`, hard `{date}`.
4. Low confidence on location only → `confirm`.
5. Unknown room → `confirm`; unknown room plus missing title → `review` with both in hard.
6. Quiet Hours notice → `rejected`.
7. Evidence is checked before confidence (a field with no evidence and confidence 0.99 is still hard).

## 6 · What we measure once it runs

- Share of posters per route in the first week; target under 30% in review.
- Wrong accepts found by students reporting a wrong room or date: each one becomes a test.
- Thresholds revisited after twenty real posters; change recorded in `docs/decisions/`.
