# Confidence signals

*Sent here from Lab 3 Part 3 step 1: "Do not rely on the model's self-rated confidence alone." This guide answers: if the number is not trustworthy, what is, and how do you turn several weak signals into a routing decision you can measure?*

## What the number is, and what it is not

When `google/gemini-3.8-flash` returns `"confidence": 0.9`, it has not computed a probability. It has written a token. You asked it to estimate how sure it is, and it produced a number the way it produces any text: by predicting what a plausible answer looks like.

A calibrated probability has a specific meaning: of all the times the system says 0.9, about 90 percent should be correct. Self-reported confidences do not have that property. They cluster high, they are swayed by how confident the surrounding text sounds, and they are only loosely tied to the pixels. A model that has just produced a fluent, well-formatted date feels confident about it, in the only sense that applies, whether or not the date was on the poster.

The number is not useless: it is free, weakly informative, and a very low value is a real signal. Treat it as one vote among several, never the verdict.

## The torn poster, in detail

A poster whose bottom edge is torn so the date is gone. Title, time and room are intact. The model returns `date.value = "14 March 2027"`, `date.confidence = 0.9`, `date.evidence = null`.

What happened: the model saw a workshop poster with a time and a room. It knows posters have dates. It filled the slot with the most plausible completion and, because the completion was fluent, rated it high. Nothing in generation asked "did I read this or infer it?" The prompt said not to guess; the schema allowed null; it guessed anyway. A minority of the time is enough to put wrong events in a calendar.

The evidence field saves you. Evidence must be exact text from the image, and there is no date text, so the model either returns null (honest) or fabricates a quote (detectable, signal five). Either way `decide()` flags `no_evidence`, the field is hard, and the reviewer sees an empty date box beside the photo. The 0.9 never gets a vote.

The general lesson: a signal produced by the same process as the value cannot audit that value. You need signals from outside the generation.

## Five signals better than the number

**1. Evidence present and verbatim.** Is `evidence` non-null and does it look printed rather than described? Evidence should be short, free of words like "appears" or "likely", and contain the characters the normalised value came from. "Fri 14 March" supports `2027-03-14`; "the date near the bottom" supports nothing.

**2. Format validity.** Did the value normalise? A date `normalise_date()` cannot parse, a time of "evening", a room absent from the campus list: each is an objective failure that costs nothing to detect. A value that fails validity is wrong regardless of confidence.

**3. Consistency with the world.** You know things the model does not: today's date (`in_the_past`), the room list (`unknown_room`), opening hours (a 03:00 workshop is unlikely), term dates. Each is a plain conditional in `decide()`, and each catches a class of error the model cannot see.

**4. Agreement between two runs.** Call the model twice on the same image. Decoding is not perfectly deterministic (see `how-models-see-images.md`), so ambiguous regions produce different readings while clearly printed text comes back identical. If `date.value` matches, raise your trust; if it differs, you have found an ambiguous field without knowing why. Cost: one extra call, about $0.002 per poster at current pricing (approximate; re-verify). Run the second pass only when the first has a soft flag, and you pay it on perhaps a third of posters.

**5. Agreement between two readings.** Compare the model's `evidence` against an independent reading: a local OCR engine such as Tesseract, or a second model. You are not asking OCR to extract the date, only whether the characters the model claims to have read exist in the image. If OCR finds no "14" anywhere, the model is quoting something it did not see. This catches the nastier torn-poster failure where the model invents evidence to match its invented value.

```python
def evidence_corroborated(evidence: str | None, ocr_text: str) -> bool:
    if not evidence:
        return False
    norm = lambda s: re.sub(r"\s+", " ", s.upper()).strip()
    return norm(evidence) in norm(ocr_text)
```

Forgiving on whitespace and case, strict on digits.

## Combining signals into routes

`decide()` is a pure function, and the way to keep it honest is to write the policy as a table before the code.

| Condition on a field | Flag | What the example does with it |
|---|---|---|
| `value` is null | `missing` | hard: route `review`, field shown empty |
| `evidence` is null | `no_evidence` | hard: route `review`, field shown empty |
| `confidence` below 0.6 | `low_confidence` | soft: route `confirm` |
| date is not ISO `YYYY-MM-DD` | `unparseable_date` | soft: route `confirm` (hard only if a hard flag is also present) |
| date before `today` | `in_the_past` | soft: route `confirm` (hard only if a hard flag is also present) |
| room not in the campus list | `unknown_room` | soft: route `confirm` (hard only if a hard flag is also present) |
| nothing event-like at all | (no flag) | `looks_like_event()` is false: route `rejected` |

That is the table `examples/poster-extraction/src/checks.py` implements, in that order: evidence is checked before the model's own number. Two flags you will probably add for your own feature, and which the example leaves to you: `invalid` (a value that fails to normalise, for example a time of "25:70") and `unstable` (two runs disagree on the value; see `disagreements()` in `src/extract.py`). Decide their hardness in your `docs/confidence-policy.md` before you write the code.

Then the route for the whole extraction:

| Situation | Route |
|---|---|
| `is_event_poster` is false | `rejected` |
| any hard flag on a required field | `review` (hard fields shown empty) |
| no hard flags, one or more soft | `confirm` (prefilled, highlighted) |
| no flags | `accepted` |

Two properties to preserve. Hard beats soft: a field with `no_evidence` goes to `review` empty even at confidence 0.99. And the number sits near the bottom of the table: it can push a clean field into `confirm`; it can never pull a flagged field into `accepted`.

The thresholds are policy, not truth. Put them in one place as named constants.

## Measuring whether your policy is any good

A routing policy you have not measured is a guess with extra steps.

Build a labelled set: twenty to forty poster images, each with the correct values and the route a human would want. Your four lab images are the seed; the class's images, pooled, are a respectable set.

Run the pipeline and build a confusion matrix of routes: rows are what your policy chose, columns are what the label says. The interesting cells are off the diagonal.

Weigh the cells, because errors are not symmetric. A wrong `review` (a clean poster sent to a human) costs thirty seconds. A wrong `accepted` (a wrong date published as fact) costs a student at an empty room, a correction, and trust. Price the first at 1 and the second at 50, and move the thresholds until weighted cost is lowest. Most first policies are too trusting; the fix is usually another world-consistency check.

Report three numbers in your Safety and Eval Audit: the fraction of posters reaching `accepted`, the fraction of those actually correct, and the weighted cost. All three come from fixtures and logged outputs, so the measurement is repeatable without live calls.

## Logprobs: not available here

Some APIs return the log-probability of each generated token. With those you can read the model's uncertainty at the moment it wrote "14": if that digit had probability 0.51 with "17" at 0.47, it is a coin flip, whatever the confidence text says. Token probabilities are closer to calibrated than self-reports, and most useful on exactly the short, digit-heavy fields a poster has.

`google/gemini-3.8-flash` through OpenRouter does not expose logprobs, so this lab does without. If you later move to a model that does, add a sixth signal, `min_token_prob` over the characters of `value`, and give it a row in the flag table. Routes, UX and audit stay the same. That containment is the payoff for keeping `decide()` pure and signal-driven rather than wiring the UI to one number.

## Apply it to your feature

1. Write the flag table and route table as comments at the top of `decide.py`, then make the code match the table.
2. Add OCR corroboration on `evidence` for the date and room fields; log how often it disagrees with the model.
3. Run a second extraction only when the first has a soft flag, and treat disagreement as `unstable`.
4. Build a labelled set of at least twenty images with the class, compute the route confusion matrix, and pick cost weights for wrong accept versus wrong review.
5. Move every threshold into named constants and record in your Pattern Journal what changed when you moved one.
