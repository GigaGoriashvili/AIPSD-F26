# Retrieval spec · CampusPulse

*The filled version of `templates/retrieval-spec.md` for the reference app in `campuspulse-rag/`. Yours will be about your own documents.*

## 1 · What the documents are

| Folder in `data/corpus/` | What is in it | Who owns the real version | How often it changes | Documents |
|---|---|---|---|---|
| `clubs/` | one page per student club: about, meetings, membership, contact | each club lead | every semester | 6 |
| `regulations/` | room booking, club policy, academic calendar extract | Student Affairs | once a year, plus corrections | 3 |
| `archive/` | write-ups of past events | Student Affairs and club leads | after each event | 3 |

Not in the corpus, on purpose: IT and Wi-Fi details, anything about individual students, exam timetables. We refuse those and point to the right office.

## 2 · Chunking

- Split on: `## ` headings. Each section of our pages covers one topic.
- Header glued to each chunk before embedding: `title · section`, for example `KIU Robotics Club · Membership`
- Maximum size: 1,200 characters (about 300 tokens) · Overlap: one paragraph when a section is split

## 3 · Retrieval

- Embedding model: `openai/text-embedding-3-small` · $0.02 per million tokens (verified on OpenRouter, 13 October 2026)
- Retriever: hybrid, vectors and BM25 merged with Reciprocal Rank Fusion · k = 5
- Refusal threshold: best cosine score 0.25 (starting value; tuned with the golden set)

## 4 · Answering

- Model: `google/gemini-3.8-flash` from `CAMPUSPULSE_MODEL` ($0.75 in / $3.75 out per million tokens, promotional, verified 13 October 2026)
- Reply shape: `{answer, citations, grounded}`, validated with pydantic, extra fields forbidden
- Every sentence cites a retrieved source as `[n]`. A citation that fails the check is a refusal, never a warning.
- Refuse before calling the model when nothing scores above the threshold.

## 5 · What the user sees

- A cited answer: "Membership is free [1]." with a chip `[1] KIU Robotics Club · Membership` that opens the section.
- A refusal: "I can't answer that from CampusPulse's sources. I know about clubs, room rules and past events." Next step offered: the Student Affairs office.

## 6 · Acceptance criteria

- AC1 "Is the Robotics Club free to join?" returns `answered`, citing `clubs/robotics`, and the answer says "free"
- AC2 "What is the Wi-Fi password for the library?" returns `refused` without a model call
- AC3 a reply citing `[7]` when 5 sources were retrieved is refused (`tests/test_answer.py`)
- AC4 every answer and refusal writes one line to `logs/answers.jsonl` with the reason
- AC5 `evals/golden.yaml` passes at 0.70 or above, run live
