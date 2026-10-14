# Multimodal spec · [feature name]

*Copy to `docs/multimodal-spec.md`. Fill every line; "TBD" is allowed only in the stretch section. Filled example: `Lab-3/examples/multimodal-spec-campuspulse.md`.*

## 1 · The input

- **What the user has in their hand:** [a receipt, a menu, a timetable screenshot, a handwritten form, a PDF page]
- **How it reaches us:** [phone photo upload / screenshot / PDF page rendered to PNG]
- **Typical quality:** [lighting, angle, resolution, how often it is partly unreadable]
- **What we will never accept:** [faces, ID documents, anything with another person's personal data]

## 2 · The fields

| Field | Type after normalisation | Required | Normalisation rule | Example value | Example evidence (exact text on the image) |
|---|---|---|---|---|---|
| | | yes / no | | | |
| | | | | | |
| | | | | | |

Every field returns `value`, `evidence`, `confidence`. `value` and `evidence` are `null` when the model cannot read the field. A guess is never a value.

## 3 · The schema

Paste the pydantic model (or JSON schema) you send with the request. It must match the table above exactly.

```python
```

## 4 · Acceptance criteria

Each one decidable by a script. At least one covers the degraded case and one covers cost or latency.

1. Given `tests/images/clean.jpg`, every required field has a non-null value with non-null evidence, and the result validates.
2. Given `tests/images/degraded.jpg`, [field] is `null` or routed to confirm or review; it is never accepted.
3. Given `tests/images/not-applicable.jpg`, the route is `rejected` and nothing is created.
4. One call costs under [amount] and returns in under [seconds] at the 1024 px downscale.
5. [yours]

## 5 · Test images (in `tests/images/`)

| File | What it is | What we expect |
|---|---|---|
| `clean.jpg` | | accepted |
| `degraded.jpg` | | confirm or review, with [field] flagged |
| `ambiguous.jpg` | | confirm, with [field] flagged |
| `not-applicable.jpg` | | rejected |

## 6 · Model and budget

- Model: `google/gemini-3.8-flash` via OpenRouter (or [other], with the reason). Verified on [date] that it accepts image input and `response_format` with a JSON schema.
- Approximate cost per image at 1024 px: [amount], from one logged call.
- Expected volume: [images per day] → [cost per month].

## 7 · Out of scope for this slice

- [e.g. multiple pages, batch upload, languages other than English and Georgian, handwriting]

## 8 · Stretch

- Run twice and flag disagreeing fields.
- [yours]
