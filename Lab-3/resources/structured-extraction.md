# Structured extraction

*Sent here from Lab 3 Part 2: "A JSON schema passed to the model, and the reply validated in code. Stuck?" This guide answers: how to get a model to return data your program can use, and why you check that data anyway.*

## The ask and the check

The ask is the schema you pass with `response_format={"type": "json_schema", ..., "strict": True}`. It tells the provider to constrain generation so the reply parses as JSON of your shape: no undeclared keys, no missing required keys, no prose where a number belongs.

The check is the pydantic model you validate the reply against in your own code, after it arrives, with your rules.

Why both? Four reasons.

Providers differ. OpenRouter fronts dozens of models; not all support strict schemas, some fall back silently to "JSON mode" (valid JSON, any shape), and a few wrap the JSON in markdown fences. Your code should not care which model sits behind the string in `llm.py`.

Strict mode limits what the schema can express. Most providers support a subset of JSON Schema: no `minimum`/`maximum`, limited `format`, caps on nesting. "Confidence between 0 and 1" cannot be enforced by the provider; pydantic can.

Models produce strings where numbers belong. You will occasionally receive `"confidence": "0.9"` or `"high"`. When pydantic raises `confidence: Input should be a valid number`, the check is doing its job; route the extraction to `review`, do not patch the parser.

Validity is not correctness. A perfectly shaped reply can contain a past date or a room that does not exist. The schema cannot know that; `decide()` can.

## Designing the schema

Each extracted field is a triple:

```python
class Field(BaseModel):
    value: str | None
    evidence: str | None
    confidence: float = PydanticField(ge=0.0, le=1.0)

class Extraction(BaseModel):
    title: Field
    date: Field
    time: Field
    room: Field
    category: Literal["talk", "workshop", "social", "sport", "other"]
    is_event_poster: bool
```

**`value` and `evidence` are nullable.** The most important line. A model forced to return a string for every field will do so, including for fields it cannot read. `null` gives it a legitimate way to say "not here," and the prompt tells it to use it.

**`evidence` is the exact text the model read.** Not a paraphrase. "The date below the title" is not evidence; "Fri 14 March" is. This is what catches the torn poster: a model that invents a date has no text to quote, so either `evidence` is null (and `decide()` flags `no_evidence`) or it is a fabrication that a second reading or a human glance will expose.

**`confidence` is bounded in pydantic**, because strict mode will not do it for you.

**`category` is an enum.** When the set of answers is closed, say so. The model cannot return "Talk" or "lecture"; it must pick. Count how often `other` is used.

**No free-text `notes` field.** It is tempting to add one "so the model can explain." A notes field is where every uncertainty hides, it cannot be tested, and it invites the model to put the real answer in the notes and a guess in `value`.

**`is_event_poster` sits at the top.** The "not applicable" route needs a signal that the whole image is off-topic, separate from any one field being unreadable.

## The prompt lines that matter

The schema shapes the reply; the prompt shapes behaviour. Three sentences do most of the work:

> If a field is not legible in the image, set its `value` and `evidence` to null. Never infer or guess a value that is not printed.

> `evidence` must be the exact characters as they appear, including abbreviations and typos. Do not normalise or expand them.

> `confidence` is your estimate, from 0 to 1, that `value` is exactly what is printed.

Everything else is context. These three are rules, and the torn-poster image exists to test whether the model follows them.

## Two worked examples

Clean poster:

```json
{
  "title": {"value": "Intro to Rust", "evidence": "INTRO TO RUST", "confidence": 0.98},
  "date":  {"value": "14 March 2027", "evidence": "Fri 14 March",  "confidence": 0.95},
  "time":  {"value": "18:00",         "evidence": "18:00",         "confidence": 0.97},
  "room":  {"value": "B0.14",         "evidence": "Room B0.14",    "confidence": 0.85},
  "category": "workshop",
  "is_event_poster": true
}
```

The room confidence is lower on a clean image. That is the 0 versus O ambiguity surfacing, and it is a reasonable self-report.

Torn poster, date torn off:

```json
{
  "title": {"value": "Intro to Rust", "evidence": "INTRO TO RUST", "confidence": 0.98},
  "date":  {"value": "14 March 2027", "evidence": null,            "confidence": 0.9},
  "time":  {"value": "18:00",         "evidence": "18:00",         "confidence": 0.97},
  "room":  {"value": "B0.14",         "evidence": "Room B0.14",    "confidence": 0.85},
  "category": "workshop",
  "is_event_poster": true
}
```

Look at `date`: plausible value, high confidence, null evidence. The model guessed and rated its own guess at 0.9. Trust the number and you publish a wrong date. `decide()` sees `evidence is None`, flags `no_evidence`, and routes to `review` with the date shown empty. A well-behaved run returns `value: null` instead; both route the same way, so your policy does not depend on the model behaving.

## Normalising after extraction

Raw values are strings as printed: "Fri 14 March", "14/03", "March 14th" are one date; "B0.14", "B 0.14", "Room B0.14" are one room. Normalisation produces one canonical form: ISO 8601 dates, 24-hour `HH:MM`, a member of the campus room list.

Do this in code, not in the prompt. It is testable: `normalise_date("Fri 14 March", today)` has a right answer you can assert. It is cheap and deterministic. And it keeps `evidence` honest: if the model normalises, the value drifts from what was printed and you lose the ability to compare.

Year inference lives here too. Posters rarely print the year; the normaliser takes `today` and picks the next 14 March, and `decide()` checks whether that is in the past. Keep `today` a parameter, never `datetime.now()` inside the function, or your tests break on 15 March.

```python
def normalise_room(raw: str | None, rooms: set[str]) -> str | None:
    if raw is None:
        return None
    key = re.sub(r"[^A-Z0-9.]", "", raw.upper().replace("O", "0"))
    return key if key in rooms else None
```

Returning `None` for an unknown room lets `decide()` raise `unknown_room` instead of passing "B0.l4" into an `Event`.

## Common failures and the test that catches each

| Failure | Symptom | Unit test (fixture, no model call) |
|---|---|---|
| Model guesses a missing field | Plausible value, null evidence | Torn-poster fixture into `decide()`; assert `review` and `no_evidence` on `date` |
| Confidence as string | pydantic `ValidationError` | Feed `"high"`; assert error raised and caller routes to `review` |
| Markdown fences | `JSONDecodeError` | Feed a fenced string; assert it fails loudly and is logged |
| Date in the past | Valid date before `today` | `date="2024-01-10"`, `today=2026-10-05`; assert `in_the_past` |
| Room not on campus | Normaliser returns None | Feed `"Z9.99"`; assert `unknown_room` |
| Category outside enum | Impossible under strict mode, possible on fallback | Feed `"lecture"`; assert pydantic rejects it |
| Evidence is a paraphrase | Not found by OCR or second run | See `confidence-signals.md`; here, assert the prompt contains the "exact characters" rule |

Every row uses a fixture. These are the Evidence Rule's tests; the `llm.py` entry for each real call is its log.

## Apply it to your feature

1. Write the schema first, with `value` and `evidence` nullable and `confidence` bounded in pydantic; delete any free-text field you were tempted to add.
2. Save clean and torn JSON fixtures in `tests/fixtures/` and write the seven tests above against them.
3. Put the three prompt rules in `prompts/extract.txt` verbatim, with a test that the loaded prompt contains each.
4. Move every normalisation step into `normalise.py`, with `today` and `rooms` as parameters.
5. Run the real model once on each of your four images, store the raw replies as fixtures, and note in your Pattern Journal whether any required a code change to pass validation.
