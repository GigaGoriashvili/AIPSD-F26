# CampusPulse · poster extraction (Lab 3 reference)

A student photographs an event poster. A vision model reads it into a fixed
shape. Pure Python decides whether the result can be published, needs a
quick confirm, needs a human to fill the gaps, or is not an event at all.
This is the Week 3 pattern, Extract then Verify, end to end, in about 400
lines.

**Tests never call a model.** Every test runs offline on hand-written
extractions in `tests/conftest.py`. The only thing that spends money is
`eval_live.py`, and you run that on purpose.

## Setup

```
pip install -r requirements.txt && cp .env.example .env
```

Put your OpenRouter key in `.env` only when you want the live path.

## Run

| What | Command |
|---|---|
| Tests (offline, 33 of them) | `python -m pytest` |
| Regenerate the four synthetic posters | `python make_posters.py` |
| The app | `uvicorn src.app:app --reload` then POST an image to `/extract`, open `/review` |
| Live eval, two runs per poster, compared to `expected.json` | `export $(cat .env) && python eval_live.py` |

Example upload: `curl -F image=@posters/torn.png localhost:8000/extract`

## Folder map

```
src/extract.py    Field, Extraction, PROMPT, extract(), disagreements()
src/llm.py        complete_json() with strict JSON schema, log_usage() to logs/usage.jsonl
src/images.py     downscale() to 1024 px JPEG, approx_image_tokens()
src/checks.py     decide(): the pure function that routes accepted / confirm / review / rejected
src/review.py     Event, Draft, ReviewQueue: hard fields are blanked, never prefilled
src/promo.py      promo_image(): banned-brief check, mocked image model, our text on top
src/app.py        FastAPI: POST /extract, GET /review, POST /review/{id}
posters/          clean, torn, ambiguous, not-an-event (synthetic, drawn with Pillow)
expected.json     the route and hard set each poster should produce
tests/            33 offline tests
eval_live.py      the only file that costs money
```

## What to copy into your own repo

1. **The Field / Extraction shape.** Every field carries `value`, `evidence`
   and `confidence`. Evidence is the exact text the model read. No evidence
   means the value is a guess, whatever the confidence says.
2. **`complete_json()`.** One function owns the model call: strict schema,
   temperature 0, one usage line per call with tokens, cost and latency.
3. **`decide()` as a pure function.** Takes the extraction, today, and the
   room list as arguments. No network, no clock, no files. That is why it
   has fifteen tests and the model call has none.
4. **The review-page rule.** Hard fields (missing or unsupported) render as
   empty inputs. Soft fields render prefilled but highlighted. A reviewer
   should type what the poster says, not approve what the model imagined.

## Known limits

`parse_date` only accepts `YYYY-MM-DD`; anything else is flagged, not
guessed. The room list in `rooms.json` is a stand-in for your campus data.
Prices in `src/llm.py` were checked on 4 October 2026 and will drift: verify
live before you ship.
