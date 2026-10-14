# How models see images

*Sent here from Lab 3 Part 2: "Images are downscaled before sending. Curious why?" This guide answers: what happens to a poster photo between your phone and the model, and what that means for what you can trust in the extraction.*

## An image is tokens, not pixels

When you send a photo to `google/gemini-3.8-flash`, the model does not look at it the way you do. The image is cut into fixed-size patches (sometimes called tiles), each patch becomes a vector, and those vectors enter the same sequence as your text prompt. To the model, a poster is a few hundred to a couple of thousand "visual words" followed by your instructions.

The exact numbers are provider-specific and change with releases, so treat them as approximate and check the provider's current documentation before budgeting. The shape is stable: a small image costs a few hundred tokens; a larger one is split into more tiles and costs proportionally more; above a provider-set ceiling the image is downscaled server-side anyway, so pixels past that point buy nothing.

That is the first reason Lab 3 downscales to a longest side of 1024 px. A 12-megapixel phone photo (roughly 4000 × 3000 px) is either shrunk by the provider before encoding, so you paid upload time for nothing, or tiled into far more patches than a poster needs, so you paid tokens for nothing. Neither makes the date more readable.

## Resolution versus legibility

Downscaling throws away information. The question is whether it throws away information the model needed.

A corridor poster is designed to be read from two metres away: a 60 pt title, a date and room at 24 pt or larger, the whole thing on A3. At 1024 px on the long side, a 24 pt line is still 15 to 20 pixels tall, comfortably where printed text survives. You lose the fine print ("Organised with support from...") and you lose texture, but the fields CampusPulse needs remain legible.

A till receipt is the opposite case: 80 mm wide, 8 pt dot-matrix, forty lines of low-contrast text. Downscale that to 1024 px and each character is four or five pixels tall. The model will still answer, confidently and wrongly in places, because the signal is gone. For receipts you crop tightly and keep resolution; for posters you do not.

The rule: downscale to the size at which the fields you need are still clearly readable by a human squinting at the screen. If you cannot read it in the resized image, do not expect the model to.

JPEG quality 85 follows the same logic. Artefacts at that setting are invisible at poster text sizes and the file is a third the size of quality 100. Below about 70 you start to see ringing around letters, which worsens the 0 versus O problem below.

## What vision models are good at

Printed text in common fonts at reasonable size: very reliable. Layout: they understand that the big line at the top is a title and the block of three short lines near the bottom is probably date, time, place. Common objects and scenes: a photo of a cat or a fire-exit sign is recognised as such, which is why the "not applicable" test image gets routed to `rejected` with a sensible description.

## What vision models are bad at

Small text. Handwriting, especially marker pen on a glossy surface. Counting (how many bullet points are on the poster is a guess). Exact positions. Rotated text: a poster photographed sideways is read noticeably worse, and text at 45 degrees is close to a coin flip. Visually similar glyphs: 0 and O, 1 and l and I, 5 and S, 8 and B. Room codes like "B0.14" versus "BO.14" are exactly where this bites CampusPulse, and it is one reason the lab normalises rooms against a canonical list in code rather than trusting the transcription.

The model is also bad at knowing which of these failures it is currently making. That is why Part 3 exists.

## Why two runs disagree, even at temperature 0

Temperature 0 is not deterministic, for reasons that stack. The image encoding and attention run as large batched floating-point operations, and floating-point addition is not associative, so different batch compositions on the provider's side produce slightly different intermediate values. Providers route requests across hardware and software versions. And "temperature 0" usually means greedy decoding over a candidate set the provider controls.

For plain text the effect is small. For an ambiguous image region (a smudged digit, a torn edge) the model is often near a tie between two readings, and near-ties are exactly where tiny numerical differences flip the output. The same torn poster can return "14 March" on one run and "17 March" on the next. `confidence-signals.md` turns this into a tool: disagreement between runs is evidence of ambiguity.

## Orientation and EXIF rotation

Phones store photos in the sensor's native orientation and write a rotation flag into EXIF metadata. Viewers obey the flag; many image libraries and API clients do not. The result is a photo that looks upright on your laptop and reaches the model rotated 90 degrees.

Lab 3's `prepare_image()` applies the rotation before resizing and strips the metadata. If extraction is mysteriously poor on photos from one phone, check this first, by opening the resized JPEG that is actually sent.

```python
from PIL import Image, ImageOps

def prepare_image(path, longest=1024, quality=85):
    img = ImageOps.exif_transpose(Image.open(path))
    img.thumbnail((longest, longest))
    out = io.BytesIO()
    img.convert("RGB").save(out, "JPEG", quality=quality)
    return out.getvalue()
```

## When to crop instead of downscale

Downscale when the whole frame matters and the text is large. Crop when the text is small and you know where it is: several posters in one photo; the field you need is in a small region; the poster fills a quarter of the frame because the photographer stood too far back. Cropping to the poster's bounding box before resizing to 1024 px can double the effective text height at no extra token cost. A production pipeline detects the poster region, crops, then downscales. Lab 3 keeps it simple and asks the photographer to fill the frame.

## Cost arithmetic for one poster

All numbers approximate; re-verify the price and the provider's image token formula before you ship.

A 1024 × 768 JPEG lands in the region of 1,000 input tokens for most current providers (it could be a few hundred or closer to two thousand depending on tiling). Add about 300 tokens of prompt and schema. The structured reply is around 250 output tokens.

· Input: roughly 1,300 tokens × $0.75 per million ≈ $0.001
· Output: roughly 250 tokens × $3.75 per million ≈ $0.0009
· Total: about $0.002 per poster, roughly $2 per thousand

Send the 12-megapixel original instead and you pay between the same and ten times more, with no gain in accuracy. Your `llm.py` log records real token counts for every call, so after ten extractions you can replace these estimates with your own.

## Apply it to your feature

1. Open the resized image your code actually sends and confirm you can read every field you expect the model to read.
2. Photograph your four test images upright and filling the frame; then take one rotated and one from too far back, and compare the extraction logs.
3. Run the same image three times and diff the `value` fields; note which ones flip and use that in your confidence policy.
4. Pull input token counts from your `llm.py` log and compute your real cost per poster.
5. If any required field is below about 15 px tall in the resized image, crop before you resize rather than raising the resolution.
