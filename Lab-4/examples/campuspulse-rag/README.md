# CampusPulse · grounded answers (Week 4 reference)

Answers questions about KIU clubs, room rules and past events from 12 documents in `data/corpus/`, cites the section each sentence came from, and refuses when it cannot. Every line of code shown in the Week 4 lecture is in these files.

## Run it

```
pip install -r requirements.txt

# offline: no key, no network, no cost. Tests, CI and the classroom demo use this.
export CAMPUSPULSE_OFFLINE=1
python -m src.index                 # chunk + embed data/corpus/ into data/index/
pytest                              # 37 offline tests
python -m evals.run_golden          # golden set, k=5
python -m evals.run_golden --k 1    # same set, one chunk: watch it fail the threshold
python -m demo.break citations      # the lecture's lying-model demo

# live: real embeddings and the real model
export CAMPUSPULSE_OFFLINE=0 OPENROUTER_API_KEY=...
python -m src.index                 # rebuild: the index remembers which model made it
python -m evals.run_golden          # costs about one cent
uvicorn src.app:app --reload        # POST /ask {"question": "..."}
```

Set `CAMPUSPULSE_VERBOSE=1` to print every usage line. Logs go to `logs/usage.jsonl` (every model call) and `logs/answers.jsonl` (every answer and refusal, with the reason).

## Where things are

| File | What it does | Lecture slide |
|---|---|---|
| `src/llm.py` | every model call: `complete_json()` (image now optional), `embed()`, usage logging | 9 |
| `src/offline.py` | the stand-ins: trigram-hash embeddings and an extractive "model" that never writes anything new | 9, 23 |
| `src/chunk.py` | one chunk per `## ` section, title and section glued on, 1,200-character cap with overlap | 13 |
| `src/index.py` | build, save, load; refuses an index built with a different embedding model | 9, 12 |
| `src/bm25.py` · `src/retrieve.py` | keyword scoring; `search()` (vectors) and `hybrid()` (vectors + BM25 with RRF) | 9, 18 |
| `src/answer.py` | the prompt, the `Reply` schema, `check_citations()`, the four routes, one log line per answer | 12, 14, 15 |
| `src/app.py` | `POST /ask` | |
| `evals/golden.yaml` · `evals/run_golden.py` | five golden questions and the scorer; exit code 1 below 0.70 | 21, 22 |
| `evals/results/` | two committed offline runs: k=5 (0.80) and k=1 (0.60) | 23 |
| `docs/decisions/` | why hybrid retrieval, why k=5 | 19 |
| `demo/break.py` | the two live breakages from the lab demo | 15, 23 |

## What the offline numbers mean

The offline stand-ins measure retrieval and the citation checks, not answer quality. They match letters, not meaning, so g3 ("snacks" in Lab B204) fails offline in every setting: "snacks" and "food" share no letters. Run the golden set live before you trust a number.

Prices used in `src/llm.py` were verified on openrouter.ai on 13 October 2026: `google/gemini-3.8-flash` $0.75 in / $3.75 out per million tokens (50% promotional), `openai/text-embedding-3-small` $0.02 per million.
