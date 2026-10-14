# Confidence policy · [feature name]

*Copy to `docs/confidence-policy.md`. This is the table your `decide()` function implements. Write the table first, then make the code match it. Filled example: `Lab-3/examples/confidence-policy-campuspulse.md`.*

## 1 · Routes

| Route | What it means | What the user sees | What gets created |
|---|---|---|---|
| `accepted` | every required field is present, evidenced, consistent | the result as fact, with "from [source]" | the real record (CampusPulse: an `Event`) |
| `confirm` | one or more soft flags | the value, highlighted, with one question | a draft until the user confirms |
| `review` | one or more hard flags | the flagged fields **empty**, the image beside them | a draft in the review queue |
| `rejected` | not the kind of input this feature reads | what it was recognised as, and what to do instead | nothing |

## 2 · Signals, per required field

Tick the signals you check. Self-rated confidence is never the only one.

| Field | Signal | Condition | Flag | Hard or soft |
|---|---|---|---|---|
| [field] | value present | `value is None` | `missing` | hard |
| [field] | evidence present | `evidence is None` | `no_evidence` | hard |
| [field] | self-rated confidence | `confidence < 0.6` | `low_confidence` | soft |
| [field] | format valid | [e.g. not ISO date] | `invalid` | [you decide] |
| [field] | consistent with the world | [e.g. date in the past, room not in list] | [name] | [you decide] |
| [field] | stable across two runs | values differ | `unstable` | [you decide] |

Order matters: check evidence before the model's own number.

## 3 · From flags to a route

```
no event-like content at all          → rejected
any hard flag                         → review  (hard fields shown empty)
any soft flag, no hard flag           → confirm (soft fields prefilled, highlighted)
no flags                              → accepted
```

## 4 · The reason text

For each flag, the sentence the user or reviewer reads. No numbers, no jargon.

| Flag | On screen |
|---|---|
| `missing` on [field] | "[Field]: not found on the image" |
| `no_evidence` on [field] | "[Field]: we could not find the text this came from" |
| `low_confidence` on [field] | "We think this is [value]. Check the image?" |
| | |

## 5 · Tests you will write (in `tests/`, hand-written extractions, no API calls)

1. Clean extraction → `accepted`, no flags.
2. Your degraded image's case → `review` (or `confirm`), with the right field in `hard`.
3. [a consistency case: past date, unknown room, impossible time]
4. [the not-applicable case → `rejected`]

## 6 · What we measure once it runs

- Share of real images per route (if 80% land in review, the thresholds are wrong, or the photos are).
- Wrong accepts found later (the expensive mistake). Wrong reviews (the annoying one).
- Revisit the thresholds after the first twenty real images, and record the change in a decision record.
