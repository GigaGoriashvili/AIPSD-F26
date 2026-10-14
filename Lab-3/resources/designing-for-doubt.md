# Designing for doubt

*Sent here from Lab 3 Part 3 step 3: "How the user sees each route is a design decision." This guide answers: once `decide()` has picked a route, what should the person on the other side of the screen see, and why do the obvious choices fail?*

This is the week's named pattern, Uncertainty-Aware UX. In one sentence: the interface should carry the system's doubt to the user intact, neither hiding it nor dumping it on them as a number.

## Four routes, four experiences

**Accepted.** Every field has verbatim evidence, normalised cleanly, passed every world check. Show it as fact: an event card with title, date, time and room, and a small "from poster" link to the source photo. No confirmation step: make people confirm what the system is sure about and they stop reading the confirmations that matter.

**Confirm.** Fields are filled and plausible but something soft was flagged: low confidence, a date that normalised into the past, two runs that disagreed. Show the prefilled values, highlight the flagged field with a coloured border (not a red error), and ask one question in plain words: "We read the date as Friday 14 March. Is that right?" with the evidence quote beside it. On "no", the field clears and they type.

**Review.** At least one required field is hard-flagged: missing, no evidence, unknown room. Show the photo large on one side and the form on the other. Flagged fields are empty. Not placeholder text showing the model's guess, not a "suggested" value in lighter type: empty. Fields with verbatim evidence may be prefilled and marked as such.

**Rejected.** `is_event_poster` was false. Say what it was recognised as ("This looks like a notice board, not a single poster") and offer the next move ("Try again closer, or add the event by hand"). A rejection without explanation reads as a crash.

## Why prefilled guesses get approved

Reviewers anchor. Put a plausible value in a box and the question they answer silently changes from "what is the date on this poster?" to "is anything obviously wrong with 14 March?" The second is easier and far more likely to get a yes. On a torn poster nothing is obviously wrong with 14 March; there is simply no date. A reviewer who is not forced to look for one will not notice it is missing.

You can watch this in any real review queue: content moderation, invoice approval, medical coding. Once a queue is mostly correct suggestions, reviewers approve at a rate approaching 100 percent, wrong ones included, because the base rate has taught them that looking is wasted effort. The usual name is automation bias, and it is a rational response to a stream of mostly-right prefills, not laziness. The reliable countermeasure is to not prefill what you are unsure about, so the reviewer has to read.

An empty box costs ten seconds of typing. A prefilled wrong date costs a room full of nobody.

## The language of doubt

Never put "confidence 0.62" on a screen. Users do not know whether 0.62 is good, and the number is not calibrated anyway (see `confidence-signals.md`). Translate the system's state into a sentence about the world, with the action attached.

| Internal state | On screen |
|---|---|
| `accepted` | "From the poster in Corridor B" |
| `low_confidence` on room | "We think this is room B0.14. Check the poster?" |
| `in_the_past` | "This date has already passed. Did you mean next year?" |
| `unstable` on date | "The date was hard to read. Please confirm it." |
| `no_evidence` on date | (empty field, label:) "Date: not found on poster" |
| `unknown_room` | "We don't recognise room 'B0.l4'. Pick one from the list?" |
| `rejected` | "This doesn't look like an event poster. It looks like a timetable." |

Three rules: say what the system did, not how it feels ("we read", not "we're not sure"); name the specific field, never the whole record; end with the action the user can take.

## Progressive disclosure of evidence

The `evidence` string is valuable to a reviewer and noise on a card. Hide it behind a light affordance by default: a dotted underline on the value, a quotation mark icon, a tap target on mobile. On hover or tap, show the exact text the model read and, if you can, highlight that region on the thumbnail.

For `confirm`, show the evidence by default beside the highlighted field; that is the moment of judgement.

## Recovery paths

Every route except `accepted` needs a way out that is not "give up". Offer three, in order of effort:

· **Retake.** One button, opens the camera. Most bad extractions are bad photos: glare, angle, distance.
· **Crop.** Drag a box around the poster, or around the one unreadable field, and re-run on the crop. Right when the poster is small in frame or two posters overlap.
· **Type it.** Always available, always last.

Log which recovery was chosen. If half your reviews end in a retake, your capture screen needs a frame guide, not a smarter model.

## Audit trail

Only `accepted` results become an `Event`; everything else is a `Draft` until a human acts. When they do, record who confirmed which fields, from which image, when, and what the model proposed before the human changed it. Store the original `Extraction` JSON beside the final `Event`, unchanged.

When a wrong event appears, the audit row tells you whether the model misread, the reviewer misclicked, or the poster was wrong. It is also your evaluation data: every correction is a labelled example for the confusion matrix in `confidence-signals.md`.

## Anti-patterns

**The confidence bar.** Green-to-red under each field. Users cannot act on "72 percent" and learn to ignore it.

**Silent fallback.** Validation fails and the code substitutes a default: today's date, the first room in the list, "other". The user sees a confident record with no hint that part of it came from a `try/except`: a wrong answer with the appearance of a right one. Every fallback must change the route.

**Hiding the image from the reviewer.** A review form without the photo asks the reviewer to judge a transcription without the source. They will approve it. Always show the image, readable, beside the fields.

**Confirm fatigue.** Routing too much to `confirm` because it feels safe. Each unnecessary confirmation trains the "yes" tap, and the habit carries over to the one that mattered.

## A wireframe for the CampusPulse review page

Desktop, two columns. Left, about 55 percent of the width: the uploaded photo, fit to height, zoomable, with a "Crop and re-read" button beneath. Right: a header "Check this event" and a one-line reason ("We couldn't find the date on the poster"). Below, four fields stacked: Title, Date, Time, Room, then a Category dropdown.

Each field has a label, an input and a status line. With verbatim evidence: prefilled, status "Read from poster: 'INTRO TO RUST'" in muted text, collapsed behind the quote icon on narrow screens. Soft-flagged: prefilled, amber border, the plain-language question from the table, evidence expanded by default. Hard-flagged: empty input, label note "not found on poster", focused on load, no placeholder text.

Bottom right: a primary "Publish event" button, disabled until every required field has a value, and two secondary actions, "Retake photo" and "Discard". Publishing writes the `Event` and the audit row in one transaction.

Mobile: the same, stacked, photo pinned to the top third and collapsible while typing. It never scrolls fully away.

## Apply it to your feature

1. Build one screen per route; do not reuse the `confirm` form for `review` with fields "just emptied", because the reason line and focus behaviour differ.
2. Replace every number on screen with a sentence from the language table, and add a test that no template renders the string "confidence".
3. Make hard-flagged inputs empty with no placeholder, and test that the rendered `review` page for the torn-poster fixture contains no date value anywhere in the HTML.
4. Write the audit row (user, image id, proposed values, final values, timestamp) in the same transaction as the `Event`.
5. Put the retake button on every non-accepted screen and log which recovery path users pick during your Demo Day rehearsal.
