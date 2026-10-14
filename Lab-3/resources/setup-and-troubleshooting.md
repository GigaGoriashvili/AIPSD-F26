# Setup and troubleshooting

*Sent here from the top of the Lab 3 README and from any step that fails before the model is called. This guide answers: how do I get the key, the images and the example running, and what does each error mean?*

## The API key, without saving it to a file

OpenRouter gives you one key. It must reach Python as the environment variable `OPENROUTER_API_KEY` and must never reach GitHub. Export it in the shell session you are working in.

bash (Linux, Git Bash on Windows):

```bash
export OPENROUTER_API_KEY="sk-or-v1-..."
```

zsh (current macOS): the same line. To keep it across terminals, put it in `~/.zshrc`, which is outside the repo.

PowerShell:

```powershell
$env:OPENROUTER_API_KEY = "sk-or-v1-..."
```

Check with `echo $OPENROUTER_API_KEY` (bash, zsh) or `$env:OPENROUTER_API_KEY` (PowerShell). An empty line means a new terminal, a typo, or `set` where you needed `export`.

## .env.example versus .env

The repo ships `.env.example`, a template with variable names and no values. Copy it to `.env` and fill in your key if you prefer a file; `llm.py` loads `.env` when present. `.env` is in `.gitignore`. Confirm before your first commit with `git check-ignore .env`, which should print `.env`. If it prints nothing, fix `.gitignore` first.

## Install and run

```bash
python -m venv .venv
source .venv/bin/activate          # PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest                             # must pass with no key set
python -m campuspulse.app          # needs the key
```

`pytest` passing without a key is a requirement, not a convenience: unit tests never call a real model. A test that needs the key is calling the network, which is a bug in the test.

## Taking the four test images

**Clean**: a well-lit poster, straight on, filling the frame. **Degraded**: similar poster with glare, an angle, a tear, or a covered field. **Ambiguous**: one where a human would hesitate, such as a handwritten date or a room code that could be 0 or O. **Not applicable**: not an event poster at all, such as a timetable, a fire-exit sign, or a notice board from across the hall.

Shoot upright, filling the frame, no flash on laminated surfaces.

To get them to the laptop, AirDrop, USB or email all work, but choose "Medium" or "Large" when the phone offers a size, never "Actual size". Aim for files under about 1 MB. The pipeline downscales to 1024 px anyway.

## HEIC to JPEG

iPhones shoot HEIC by default and Pillow may not open it.

· **Mac:** Finder, right-click, Quick Actions, Convert Image, JPEG. Or `sips -s format jpeg -Z 1600 IMG_0001.HEIC --out poster_clean.jpg`.
· **Windows:** install "HEIF Image Extensions" from the Microsoft Store, then Photos, Save As JPEG. Or `pip install pillow-heif`.
· **Linux:** `heif-convert IMG_0001.HEIC poster_clean.jpg` (package `libheif-examples`), or `pip install pillow-heif`.

Simplest: set the phone camera to "Most Compatible" (iOS) and it shoots JPEG from then on.

## EXIF rotation surprises

Your photo looks upright in every viewer and arrives at the model sideways. Viewers obey an orientation flag; your code did not. `prepare_image()` applies `ImageOps.exif_transpose` before resizing. If you wrote your own loader, add that line. To see what the model receives, save the bytes `prepare_image()` returns and open them.

## Errors and fixes

| What you see | What it means | Fix |
|---|---|---|
| `401 Unauthorized` from OpenRouter | Key missing, wrong, or has a stray space or quote | Re-export; check `echo $OPENROUTER_API_KEY`; regenerate on the dashboard if in doubt |
| `400` mentioning "response_format not supported" or "json_schema" | Model string wrong, or that model lacks strict schemas | Confirm `MODEL = "google/gemini-3.8-flash"` exactly, set only in `llm.py` |
| `ValidationError: confidence: Input should be a valid number` | The model returned `"0.9"` or `"high"` as a string | The check is working. Do not loosen the schema; route to `review` and log it |
| Tests fail in CI with "missing API key" or a network error | A test is calling the real model | Mock `llm.complete()`; every test must pass with the key unset |
| "image too large", `413`, payload-size error | You sent the original photo bytes | Call `prepare_image()` first; check the result is under about 300 KB |
| `git: file exceeds size limit`, push rejected | You committed a full-size photo or HEIC | `git rm --cached` it; add `*.HEIC` and `images/raw/` to `.gitignore`; keep only resized JPEGs |
| Reply wrapped in ```` ```json ```` fences, `json.loads` fails | Strict mode not applied: wrong model string, or `response_format` dropped in a refactor | Check the request in the `llm.py` log; restore `strict: True`; never strip fences silently |
| `KeyError: 'evidence'` after validation | Pydantic model and the schema sent to the provider drifted apart | Generate the schema from `Extraction.model_json_schema()` so there is one source |
| Good on Monday, bad on Tuesday, same images | A different phone or export path changed rotation or compression | Compare the prepared bytes, not the originals |
| Cost per call far above the lab estimate | Original-size images, or a static room list embedded in every prompt | Read token counts from the `llm.py` log; downscale; move static lists out of the prompt |

## Before you ask for help

Run these and paste the output into your question:

```bash
python -c "import os; print(bool(os.getenv('OPENROUTER_API_KEY')))"
python -c "from campuspulse.image import prepare_image; print(len(prepare_image('images/poster_clean.jpg')))"
tail -n 3 logs/llm.jsonl
```

The first should print `True`. The second, a number under about 300000. The third shows the model string, token counts and latency of your last three calls, which is where most "it worked yesterday" mysteries are solved.

## Apply it to your feature

1. Run `pytest` with the key unset and confirm green before writing new code.
2. Add `images/raw/` and `*.HEIC` to `.gitignore` before the first photo lands in the repo.
3. Save the prepared bytes of each test image once and check orientation and legibility.
4. Keep `MODEL` in one place in `llm.py`, with a test that no other file contains a model string.
