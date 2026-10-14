# Embeddings, explained

*Helps with Lab 4, Part 2: retrieve and cite.*

## 1. The idea in plain language

An embedding is a list of numbers that stands for a piece of text. The embedding model is trained so that texts with similar meaning get similar lists. "How much does the club cost?" and "Membership costs 20 GEL per semester" share almost no words, but their vectors point in roughly the same direction.

`openai/text-embedding-3-small`, the model CampusPulse uses, returns 1,536 numbers per text. You never read those numbers yourself. You only compare them.

The comparison we use is **cosine similarity**: the cosine of the angle between two vectors. It is 1 when they point the same way, about 0 when they are unrelated, and it ignores length. A long chunk and a short question can still score high if they point the same way.

Cosine is normally `a · b / (|a| |b|)`. If every vector already has length 1, the bottom of that fraction is 1 and cosine becomes a plain dot product. That is why `embed()` in `src/llm.py` ends with this line:

```python
return v / np.linalg.norm(v, axis=1, keepdims=True)   # unit length
```

And that is why `search()` in `src/retrieve.py` can score every chunk with a single matrix multiplication:

```python
scores = index.vectors @ q            # cosine, because every row is unit length
```

One line, every chunk scored. `test_vectors_are_unit_length` guards that property.

## 2. Why it matters in production

Embeddings find the right page when the user's words and the page's words differ. Students do not type the way regulations are written. Three production facts follow.

**The index and the queries must use the same model.** Vectors from two different models live in different spaces. A dot product between them is a number, but it means nothing. Nothing crashes. Retrieval just quietly returns rubbish. So `src/index.py` writes the model name into `data/index/meta.json` when it builds the index, and `load()` refuses to continue if the query model differs:

```python
if meta["embed_model"] != embed_model_name():
    raise IndexMismatch(f"index built with {meta['embed_model']}, queries use {embed_model_name()}. "
                        "Vectors from different models are not comparable: rebuild with python -m src.index")
```

A loud error beats a silent wrong answer. `test_index_built_with_another_model_is_refused` proves the guard works.

**Embeddings are cheap.** `openai/text-embedding-3-small` costs $0.02 per million input tokens on OpenRouter (verified 13 October 2026, and it is in `PRICES` in `src/llm.py`). Embedding a 180,000-token corpus costs:

```
180,000 / 1,000,000 × $0.02 = $0.0036
```

Less than half a cent for the whole index. A question of about 15 tokens costs a few millionths of a dollar to embed. The expensive call in a RAG system is the chat model, not the embedding model.

**Embeddings have blind spots.** We cover them in section 4. They are the reason CampusPulse does not rely on vectors alone.

## 3. Worked example: CampusPulse, step by step

Build the index, then follow one question through it.

**Step 1: what gets embedded.** `src/index.py::build()` embeds `c.embed_text()` for every chunk, in batches of `BATCH = 64`. For the Robotics Club membership section that text is:

```
KIU Robotics Club · Membership
Membership is free. To join, come to any Wednesday meeting and add your name to the member list. ...
```

The title and section are part of the vector. See `chunking-and-retrieval.md` for why.

**Step 2: what gets stored.** `save()` writes three files to `data/index/`: `vectors.npy` (one row per chunk), `chunks.json` (the text and ids) and `meta.json` (`embed_model`, `dims`, `chunks`, `built_at`). The CampusPulse corpus produces 52 chunks.

**Step 3: the question.** `search(index, "Is the Robotics Club free to join?", k=5)` embeds the question with the same model, takes the dot product with all 52 rows, and returns the top 5 as `Hit(chunk, score)`.

**Step 4: the refusal case.** Now ask "What is the Wi-Fi password for the library?". Nothing in the corpus answers it. The search still returns five hits, because the nearest vector is always the nearest vector, even when it is far away. In offline mode the best hybrid hit is the hackathon archive's "What went wrong" section (it mentions Wi-Fi) with a score of 0.20. That is below the 0.25 threshold in `DEFAULT_MIN_SCORE`, so `answer()` refuses before any model call. The score is what tells "near" from "nearest".

## 4. What embeddings are bad at

| Weakness | CampusPulse example | What we do about it |
|---|---|---|
| Exact tokens | "B204", "A112", "21:45". A semantic model may treat B204 and B214 as near neighbours | BM25 keyword scoring next to vectors (`src/bm25.py`, hybrid in `src/retrieve.py`) |
| Negation | "Which clubs do NOT charge a fee?" lands on the same fee sections as "Which clubs charge a fee?" | Let the chat model read the sources and reason; test it with a golden question |
| "Nothing relevant" | The Wi-Fi question still gets 5 hits | A minimum score (`min_score()` in `src/answer.py`), tuned on your golden set |
| Different model, different space | Index built offline, queries sent live | `IndexMismatch` |

Scores are also model-specific. A cosine of 0.25 means something different for every embedding model. That is why `DEFAULT_MIN_SCORE` is a dictionary keyed by model name and why you can override it with `CAMPUSPULSE_MIN_SCORE`.

## 5. The offline stand-in

`src/offline.py` lets tests, CI and the classroom demo run with no key and no network. Set `CAMPUSPULSE_OFFLINE=1` and `embed()` calls `offline.embed()` instead. Its model name is `offline/trigram-hash`.

It works like this: drop stop words, pad each word with spaces, cut it into three-letter pieces (" ro", "rob", "obo" and so on), hash each piece into one of `DIMS = 512` slots, count, normalise to unit length.

What it **can** do:

- Survive typos. "robtics" shares most of its trigrams with "robotics", so `test_hybrid_survives_a_typo` passes.
- Match shared words and exact codes like B204.
- Produce unit-length vectors with the same shape of interface as the real thing, so every other line of code runs unchanged.

What it **cannot** do:

- Understand meaning. "fee" and "cost" have no trigrams in common, so to the stand-in they are unrelated. "snacks" and "food" are unrelated too, which is exactly why golden question g3 fails offline (see `golden-sets-and-the-evidence-rule.md`).

So offline numbers measure plumbing: retrieval wiring, thresholds and citation checks. They do not measure answer quality. Run live before you trust a number.

## Common mistakes and how to spot them

- **Forgetting to rebuild after changing `CAMPUSPULSE_EMBED_MODEL`.** You get `IndexMismatch`. Run `python -m src.index`.
- **Dot products on unnormalised vectors.** Long chunks win for no reason. `np.linalg.norm(index.vectors, axis=1)` should be all 1.0.
- **Trusting the top hit because it is the top hit.** Compare `best_score` in `logs/answers.jsonl` for answered and refused questions.
- **Copying a threshold from a tutorial.** It belongs to one model. Tune yours on your golden set.

## Check yourself

1. Why can `search()` use `index.vectors @ q` instead of computing a full cosine formula?
2. You built the index offline, then removed `CAMPUSPULSE_OFFLINE=1` and started the app. What happens, and why is that the behaviour we want?
3. A question has nothing to do with the corpus. Why does `search()` still return five hits, and what in CampusPulse stops them becoming an answer?

<details>
<summary>Answers</summary>

1. `embed()` divides every vector by its length, so all vectors have length 1. For unit vectors the dot product equals the cosine, and one matrix multiplication scores every chunk at once.
2. `load()` raises `IndexMismatch`, because `meta.json` says `offline/trigram-hash` and queries now use `openai/text-embedding-3-small`. Vectors from two models are not comparable, and a loud failure is better than silent wrong retrieval.
3. Ranking always has a top result: the nearest vector is the nearest even when it is far. `answer()` compares the best score with `min_score()` and refuses before calling the model if it is below the threshold (0.25 by default).

</details>
