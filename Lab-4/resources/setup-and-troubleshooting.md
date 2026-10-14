# Setup and troubleshooting

*Helps with Lab 4, all parts: getting the CampusPulse example running.*

Run every command from the example root, `examples/campuspulse-rag/`. The code uses relative paths (`data/corpus`, `data/index`, `logs/`, `evals/`).

## 1. Install

```bash
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

`requirements.txt` installs openai, pydantic, numpy, pyyaml, fastapi, uvicorn, httpx and pytest.

## 2. Set your key, or go offline

**Live mode** needs an OpenRouter key.

bash or zsh:

```bash
export OPENROUTER_API_KEY="sk-or-..."
```

PowerShell:

```powershell
$env:OPENROUTER_API_KEY = "sk-or-..."
```

This lasts for the current terminal only. You can also copy `.env.example` to `.env` as a record of your settings (`.env` is in `.gitignore`), but the code reads environment variables and does not load `.env` by itself, so export them.

**Offline mode** needs no key and no network:

```bash
export CAMPUSPULSE_OFFLINE=1          # PowerShell: $env:CAMPUSPULSE_OFFLINE = "1"
```

Offline swaps in `src/offline.py`: a trigram-hash embedder and an extractive answerer. Use it for tests and to check plumbing. Do not judge answer quality with it.

## 3. Build the index

```bash
python -m src.index
```

Output: `indexed 52 chunks from data/corpus with <model> -> data/index`. It writes `vectors.npy`, `chunks.json` and `meta.json`. Rebuild after any corpus change and after switching between offline and live.

## 4. Run the app

```bash
uvicorn src.app:app --reload
```

Then ask a question:

```bash
curl -X POST http://127.0.0.1:8000/ask -H "Content-Type: application/json" \
     -d '{"question": "Is the Robotics Club free to join?"}'
```

Or open `http://127.0.0.1:8000/docs` and use the form. Questions must be 3 to 500 characters.

## 5. Run the golden set and tests

```bash
python -m evals.run_golden            # k=5
python -m evals.run_golden --k 1      # same set, different k
pytest
```

`run_golden` writes `evals/results/<timestamp>-<mode>-k<k>.json` and exits 1 below the threshold. `pytest` always runs offline (`tests/conftest.py` sets `CAMPUSPULSE_OFFLINE=1` and sends logs to a temp folder).

## 6. Useful settings

| Variable | Effect |
|---|---|
| `CAMPUSPULSE_OFFLINE=1` | Offline stand-ins, no key |
| `CAMPUSPULSE_VERBOSE=1` | Print every usage line (model, tokens, cost_usd, latency_ms) to stderr as well as `logs/usage.jsonl` |
| `CAMPUSPULSE_MIN_SCORE=0.30` | Override the refusal threshold (default 0.25). Tune it on your golden set |
| `CAMPUSPULSE_MODEL` | Chat model, default `google/gemini-3.8-flash` |
| `CAMPUSPULSE_EMBED_MODEL` | Embedding model, default `openai/text-embedding-3-small`. Changing it means rebuilding the index |

To tune the threshold, look at `best_score` in `logs/answers.jsonl` for questions that should answer and questions that should refuse. Put the threshold between the two groups.

## 7. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `IndexMismatch: index built with offline/trigram-hash, queries use openai/text-embedding-3-small` (or the reverse) | Index and queries use different embedding models | `python -m src.index` in the mode you will run in |
| `FileNotFoundError` on `data/index/meta.json` | Index never built, or you are not in the example root | `cd examples/campuspulse-rag` then `python -m src.index` |
| Every question refused with `best match 0.xx below threshold` | Threshold too high for your embedding model, or the index is empty or stale | Check `meta.json` shows the expected chunk count; lower `CAMPUSPULSE_MIN_SCORE` a little; rebuild |
| `KeyError: 'OPENROUTER_API_KEY'` | Key not exported in this terminal | Export it again (section 2) |
| `401` from OpenRouter | Key wrong, revoked or out of credit | Check the key on openrouter.ai; re-export with no extra spaces or quotes |
| The embeddings call fails (`client.embeddings.create` returns 404 or a provider error) | `embed()` uses the OpenAI SDK against OpenRouter's `/api/v1/embeddings` endpoint, and the provider behind your embedding model rejected the request | Try another embedding model, for example `CAMPUSPULSE_EMBED_MODEL=google/gemini-embedding-2` or `baai/bge-m3`, then rebuild the index. Add its price to `PRICES` in `src/llm.py`, or `cost_usd` logs 0 |
| A chat model rejects the request mentioning `response_format`, `json_schema` or `strict` | Not every model or provider supports strict JSON schema output | Use a model that lists structured outputs on its OpenRouter page, or switch back to the default |
| `pydantic.ValidationError` from `Reply.model_validate` | The model returned extra or missing fields | Same as above: the model is not honouring the schema |
| Tests are slow, ask for a key or hit the network | A test imported `src.llm` before `conftest.py` set offline mode, or you ran a test file outside pytest | Run tests with `pytest` from the example root; never set `OFFLINE` yourself inside a test module; use the `index` fixture |
| Answers change after you edited a corpus file | Stale index | Rebuild |

When something odd happens, read the last lines of `logs/answers.jsonl`. `status`, `reason`, `best_score` and `retrieved` usually tell you which stage went wrong.
