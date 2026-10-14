# Multimodal spec · Poster to event (CampusPulse)

*The Lab 3 template, filled in for CampusPulse. The code that implements it is in `poster-extraction/`.*

## 1 · The input

- **What the user has in their hand:** a printed A4 or A3 poster on a corridor wall announcing a club event.
- **How it reaches us:** a phone photo taken by a student and uploaded in the CampusPulse app.
- **Typical quality:** indoor light, slight angle, 12 megapixels, occasionally glare on laminated posters; about one in ten is partly covered or torn.
- **What we will never accept:** photos with faces in frame, notices containing phone numbers or personal names other than a club's name.

## 2 · The fields

| Field | Type after normalisation | Required | Normalisation rule | Example value | Example evidence |
|---|---|---|---|---|---|
| `title` | string | yes | trim, collapse whitespace, keep case | `Open Build Night` | `OPEN BUILD NIGHT` |
| `date` | ISO date `YYYY-MM-DD` | yes | resolve weekday names and "Oct 22" against the current academic year | `2026-10-22` | `Thursday 22 October` |
| `time` | `HH:MM` 24-hour | no | "6pm" → `18:00`; ranges keep the start | `18:00` | `18:00` |
| `location` | one of the campus room list | yes | uppercase, strip spaces, `O` → `0` inside room codes only when the result is a known room | `B204` | `Room B204` |
| `organizer` | string | no | trim | `Robotics Club` | `Robotics Club` |

Every field returns `value`, `evidence`, `confidence`. `null` when unreadable. A guess is never a value.

## 3 · The schema

```python
class Field(BaseModel):
    value: str | None
    evidence: str | None
    confidence: float = PField(ge=0.0, le=1.0)

class Extraction(BaseModel):
    title: Field
    date: Field
    time: Field
    location: Field
    organizer: Field
```

## 4 · Acceptance criteria

1. Given `posters/clean.png`, all three required fields have non-null value and evidence, the result validates, and the route is `accepted`.
2. Given `posters/torn.png`, `date` is `null` or lands in `review` with `date` in the hard set. It is never accepted.
3. Given `posters/ambiguous.png` (two dates, room `B2O4`), the route is `confirm` and the reason text names the field.
4. Given `posters/not-an-event.png`, the route is `rejected` and no `Event` or `Draft` is created.
5. One call at the 1024 px downscale costs under $0.005 and returns in under 8 seconds (measured from the usage log; approximate).
6. `decide()` makes no network call and its tests run in under one second.

## 5 · Test images (in `poster-extraction/posters/`)

| File | What it is | What we expect |
|---|---|---|
| `clean.png` | crisp poster, all fields printed | accepted |
| `torn.png` | same poster, date area torn off, lower contrast | review, hard `{date}` |
| `ambiguous.png` | two dates ("Oct 22", "Rescheduled: Oct 29"), room printed as `B2O4` | confirm |
| `not-an-event.png` | a Quiet Hours notice from the library | rejected |

## 6 · Model and budget

- Model: `google/gemini-3.8-flash` via OpenRouter. Verified 4 October 2026: image input and `response_format` JSON schema with `strict: true` both work; no logprobs.
- Approximate cost per poster at 1024 px: about a fifth of a cent (around 1,000 image tokens plus prompt, at $0.75 per million input and $3.75 per million output; re-verify prices before you ship).
- Expected volume: 50 posters a day in the first week of term → under $1 a week.

## 7 · Out of scope for this slice

- Multi-page documents, posters in Georgian only (next slice), handwritten posters, batch upload, recurring events.

## 8 · Stretch

- Run twice and flag disagreeing fields (`disagreements()`).
- Corroborate `date` and `location` evidence with an OCR pass.
