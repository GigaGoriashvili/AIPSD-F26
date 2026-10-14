# Retrieval spec · [your product]

*Copy to `docs/retrieval-spec.md`. One page. Every line should be something an agent could build from and a test could check. Filled example: `Lab-4/examples/retrieval-spec-campuspulse.md`.*

## 1 · What the documents are

| Folder in `data/corpus/` | What is in it | Who owns the real version | How often it changes | Documents |
|---|---|---|---|---|
| | | | | |

Not in the corpus, on purpose: [anything users might ask about that you will refuse, and why]

## 2 · Chunking

- Split on: [the document's own structure: `## ` headings, FAQ entries, one product per chunk ...]
- Header glued to each chunk before embedding: [title · section]
- Maximum size: [characters or tokens] · Overlap: [none / one paragraph]

## 3 · Retrieval

- Embedding model: [model id] · price per million tokens: [verified on (date)]
- Retriever: [vector only / hybrid with BM25] · k = [ ]
- Refusal threshold (starting value, tuned in Part 3): [ ]

## 4 · Answering

- Model: [model id from `CAMPUSPULSE_MODEL` or your env var]
- Reply shape: `{answer, citations, grounded}`, validated in code
- Every sentence cites a retrieved source as `[n]`. A citation that fails the check is a refusal, never a warning.
- Refuse before calling the model when nothing scores above the threshold.

## 5 · What the user sees

- A cited answer looks like: [one example, with the source label the user can open]
- A refusal says: "[the exact sentence]" and offers: [the one thing they can do next]

## 6 · Acceptance criteria

- AC1 [a question your corpus answers] returns `answered`, citing [document]
- AC2 [a question it cannot answer] returns `refused` without a model call
- AC3 a reply citing a source that was not retrieved is refused
- AC4 every answer and refusal writes one log line with the reason
- AC5 the golden set in `evals/golden.yaml` passes at 0.70 or above, run live
