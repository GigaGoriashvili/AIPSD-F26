# Chunking and retrieval

*Helps with Lab 4, Part 1: retrieval spec, and Part 2: retrieve and cite.*

## 1. The idea in plain language

A model cannot read your whole corpus for every question (see `rag-or-long-context.md` for the cost). So we cut documents into **chunks**, index them, and at question time hand the model the few chunks most likely to contain the answer. Two decisions control almost everything:

- **How you cut.** A chunk should answer one kind of question and make sense on its own.
- **How you find.** Which chunks come back, and how many.

Get the cut wrong and no retriever can save you.

## 2. Why it matters in production

Most "the model made it up" bugs in RAG systems are retrieval bugs. The model was never shown the fact, so it filled the gap with something plausible. When a golden question fails, look at `retrieved` in `logs/answers.jsonl` before you touch the prompt. If the right chunk is not in that list, the prompt is not the problem.

### The orphan sentence

Here is a sentence from `data/corpus/clubs/robotics.md`:

> The next one is on Thursday 22 October 2026 at 18:00 in Lab B204.

The next *what*? Out of context this sentence is useless. It does not say Robotics Club, and it does not say Open Build Night. A naive chunker that cuts every 200 characters could easily produce a chunk that starts here. That chunk would embed as "a date and a room" and would never match "When is the Robotics Open Build Night?". Worse, if it were retrieved, the model could attach it to the wrong event.

CampusPulse fixes this twice: by cutting on the document's own structure, and by carrying the title and section into every chunk.

## 3. Worked example: CampusPulse, step by step

### Step 1: structure first

`src/chunk.py::chunk_markdown()` makes one chunk per `## ` section. Our documents are written one topic per heading (About, Meetings, Membership, Contact), so a section is already a self-contained answer. Text that appears before the first `## ` heading goes into a section called "Overview". Empty sections are dropped.

The robotics page becomes five chunks, with ids `clubs/robotics#1` to `clubs/robotics#5`. The `doc_id` is the path under `data/corpus` without `.md`. The whole corpus (14 documents) gives 52 chunks.

### Step 2: title and section travel with the text

Every `Chunk` has `title` and `section`. What gets embedded is not the bare text but:

```python
def embed_text(self) -> str:
    return f"{self.title} · {self.section}\n{self.text}"
```

So the orphan sentence is embedded as:

```
KIU Robotics Club · Open Build Night
Once a month the club runs an Open Build Night for anyone curious. The next one is on Thursday 22 October 2026 at 18:00 in Lab B204. ...
```

This also keeps "Meetings" in the Chess Club page from looking identical to "Meetings" in the Robotics Club page. The same title and section appear in the prompt too: `format_sources()` in `src/answer.py` prints `[n] {title} · {section}` above each chunk.

### Step 3: size second

Only if a section is too long do we split it. `MAX_CHARS = 1200` (about 300 tokens of English, at roughly 4 characters per token). `_split_long()` splits on blank lines (paragraphs) and never inside a paragraph.

For our small corpus no section comes close: the longest chunk is 292 characters. The rule still matters, because your capstone corpus will have long sections, and `test_long_section_splits_with_one_paragraph_overlap` proves the split works.

### Step 4: overlap

`OVERLAP_PARAS = 1`. When a long section is split, each new piece starts with the last paragraph of the piece before it:

```python
current = current[-OVERLAP_PARAS:] if OVERLAP_PARAS else []
```

A fact that sits on a boundary, such as a rule in one paragraph and its exception in the next, appears whole in at least one chunk. The cost is a little duplication in the index.

### Step 5: choosing k

`answer()` defaults to `k=5`: five chunks, roughly 1,500 tokens of sources. That is enough for one main source plus a second one for questions that need two documents, and small enough that the prompt stays cheap and focused.

Too small and multi-source questions fail. In the golden set, dropping to k=1 takes the pass rate from 0.80 to 0.60 (see `golden-sets-and-the-evidence-rule.md`). Too large and you pay for tokens the model mostly ignores, and you give it more chances to cite the wrong thing. Treat k as a setting you choose with the golden set, not a constant you guess.

### Step 6: BM25 for exact words

Vectors find meaning. They are weak on exact tokens: room codes, names, numbers. `src/bm25.py` is BM25 in about thirty lines. It scores each chunk by how often the query's words appear in it, boosted for rare words (the `idf` term) and adjusted for chunk length (`k1=1.5`, `b=0.75`). "B204" appears in few chunks, so it carries a lot of weight. `test_bm25_finds_exact_room_codes` checks that "capacity of B204" picks the B204 line out of three room descriptions.

### Step 7: hybrid with Reciprocal Rank Fusion

`hybrid()` in `src/retrieve.py` runs both and merges them:

1. Vector ranking: the top `pool=20` chunks by cosine.
2. Keyword ranking: the top 20 by BM25, keeping only chunks with a score above zero.
3. Merge with `rrf()`.

Reciprocal Rank Fusion (Cormack, Clarke and Büttcher, 2009) ignores the raw scores, which live on different scales, and uses only positions:

```python
fused[i] = fused.get(i, 0.0) + 1.0 / (k + rank)
```

With `RRF_K = 60`, rank 1 in a list is worth 1/61 and rank 10 is worth 1/70. The constant flattens the curve, so a chunk ranked well in *both* lists beats a chunk ranked first in only one. `test_rrf_rewards_agreement_and_keeps_singletons` shows exactly that.

Real numbers from offline mode for "How many people fit in B204?":

| Chunk | Vector rank | BM25 rank | Fused rank |
|---|---|---|---|
| `regulations/room-booking#3` (Room capacities) | 1 | 1 | 1 |
| `clubs/robotics#5` (Contact) | 3 | 7 | 2 |
| `clubs/robotics#2` (Meetings) | 13 | 5 | 3 |

The capacities chunk wins clearly because both methods agree.

Note one detail: the `score` on each `Hit` that `hybrid()` returns is still the **cosine**, not the fused score. The refusal threshold in `answer()` needs a number with a fixed meaning, and RRF scores do not have one.

### Step 8: when to leave NumPy

The index is a NumPy array in `data/index/vectors.npy`. For a few thousand chunks that is the right database: it loads in milliseconds and there is nothing to run. Move to pgvector (Postgres with a vector column) or a vector store when you have:

- tens of thousands of chunks or more,
- several processes writing to the index,
- filtering by metadata ("only this user's documents", "only this semester"),
- a need to update single documents without rebuilding everything.

The interface stays the same: question in, `list[Hit]` out.

## 4. Common mistakes and how to spot them

- **Fixed-size chunks that cut mid-sentence.** Spot it: open `data/index/chunks.json` and read ten random chunks. If you cannot tell what one is about, neither can the retriever.
- **No title or section in the embedded text.** Spot it: several chunks from different documents get near-identical scores for a question naming one of them.
- **Chunks far too large.** One chunk covers five topics, so its vector matches none of them well. Spot it: the right document comes back, but ranked low.
- **Diagnosing the model when retrieval failed.** Spot it: the needed `chunk_id` is not in `retrieved` in `logs/answers.jsonl`. Our g3 is a real case: offline, the food rule `regulations/club-policy#5` is fused rank 6 for the snacks question, one place outside k=5.
- **Tuning k by feel.** Change it, rerun `python -m evals.run_golden --k N`, compare the result files.
- **Forgetting to rebuild.** After any corpus edit, run `python -m src.index`.

## Check yourself

1. Why does CampusPulse embed `"{title} · {section}\n{text}"` rather than the chunk text alone? Use the orphan sentence in your answer.
2. A chunk is rank 2 in the vector list and rank 3 in the BM25 list. Another is rank 1 in the vector list and absent from BM25. Using `RRF_K = 60`, which ranks higher after fusion?
3. A golden question fails and the answer cites the wrong document. What is the first thing you check, and where?

<details>
<summary>Answers</summary>

1. The sentence "The next one is on Thursday 22 October 2026 at 18:00 in Lab B204." names no club and no event. With "KIU Robotics Club · Open Build Night" prepended, its vector carries what it is about, and the model sees the same header in the prompt.
2. The first: 1/62 + 1/63 ≈ 0.0320. The second: 1/61 ≈ 0.0164. Agreement between the two lists wins.
3. Whether the right chunk was retrieved at all: the `retrieved` list for that question in `logs/answers.jsonl`. If it is missing, fix chunking, k or retrieval before touching the prompt.

</details>
