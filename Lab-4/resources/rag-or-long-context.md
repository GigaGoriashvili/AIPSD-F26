# RAG or long context?

*Helps with Lab 4, Part 1: retrieval spec.*

## 1. The idea in plain language

Modern models accept very long inputs. So a fair question in your retrieval spec is: why retrieve at all? Why not paste every document into the prompt and let the model find the answer?

Sometimes that is the right call. Usually, for a product like CampusPulse, it is not. Two reasons: **cost**, which you can calculate, and **attention**, which you can measure.

## 2. Why it matters in production

### Cost, step by step

Prices for `google/gemini-3.8-flash`, CampusPulse's chat model, verified on OpenRouter on 13 October 2026:

- $0.75 per million input tokens
- $3.75 per million output tokens

These are a 50% promotional price. The standard price is $1.50 / $7.50, so every figure below doubles when the promotion ends. The ratio between the two approaches stays the same.

Assumptions: a corpus of 180,000 tokens (a mid-sized university knowledge base; our lab corpus is much smaller), a question plus instructions of about 150 tokens, and an answer of 150 output tokens.

**Option A: stuff the whole corpus into every prompt.**

```
input   180,000 + 150 = 180,150 tokens
        180,150 / 1,000,000 × $0.75 = $0.1351125
output  150 / 1,000,000 × $3.75     = $0.0005625
total                                 $0.1356750  ≈ $0.1357 per question
```

**Option B: retrieve 5 chunks of about 300 tokens.**

```
input   5 × 300 + 150 = 1,650 tokens
        1,650 / 1,000,000 × $0.75   = $0.0012375
output  150 / 1,000,000 × $3.75     = $0.0005625
total                                 $0.0018000  ≈ $0.0018 per question
```

**Ratio:** $0.1357 / $0.0018 ≈ 75. Retrieval is about 75 times cheaper per question.

**At scale:** 1,000 questions a day for 30 days is 30,000 questions.

```
Option A   30,000 × $0.135675 = $4,070.25   ≈ $4,070 a month
Option B   30,000 × $0.0018   = $54.00      ≈ $54 a month
```

Retrieval adds an embedding call per question, but at $0.02 per million tokens a 15-token question costs $0.0000003. Rounding error.

You can check every one of these numbers against your own system. `cost_usd()` in `src/llm.py` uses the same prices, and each call's real token counts land in `logs/usage.jsonl`.

### Attention

Even if money were free, a longer prompt is not a better prompt.

**Lost in the Middle (Liu et al., 2023).** The researchers placed the one document containing an answer at different positions in a long list of documents. Accuracy was highest when it sat at the start or the end, and dropped when it sat in the middle: a U-shaped curve. A model "accepting" 180,000 tokens does not mean it reads all of them equally well.

**Context Rot (Chroma, 2025).** Chroma's report tested many models, including recent ones, on tasks where only the input length changed. Performance degraded as input grew, even on simple tasks well inside the advertised context window.

For CampusPulse this matters directly. The fact that Robotics membership is free sits in one sentence. Put it in the middle of 180,000 tokens of club pages, and the Photography Club's "Membership costs 20 GEL per semester" is right there too. That is the g1 failure from the lecture, with more chances to happen.

## 3. Worked example: CampusPulse, step by step

Take "How many days ahead must a club book a room for an evening event?" (golden question g2).

1. **Retrieve.** `hybrid()` returns 5 chunks. In the offline run the top one is `regulations/room-booking`, section "How far in advance".
2. **Prompt.** `format_sources()` builds a SOURCES block of about 5 × 300 tokens at most (our real chunks are shorter: the longest is 292 characters, about 75 tokens).
3. **Answer.** "Rooms for events that start after 17:00 must be booked at least five working days in advance [1]."
4. **Log.** One usage line in `logs/usage.jsonl` with `tokens_in`, `tokens_out` and `cost_usd`.

With long context, step 1 disappears, step 2 becomes the entire corpus, and step 3 depends on the model finding one sentence among thousands. The citation `[1]` also gets harder: in a stuffed prompt every document is a source, so a citation narrows nothing down.

## 4. When each one wins

**Long context wins when:**

- the corpus is small (a few thousand tokens: a syllabus, a single policy),
- the task needs the whole document (summarise this contract, find contradictions across this report),
- it is a one-off analysis, not a feature serving thousands of questions.

**RAG wins when:**

- the corpus is large or growing,
- you serve many questions,
- answers must cite a specific source,
- documents change often (re-embed one document instead of rewriting a prompt),
- different users may see different documents (filter at retrieval time).

CampusPulse ticks every RAG box.

**Prompt caching** (Week 10) changes the cost side. If the same long prefix is sent repeatedly, providers can charge much less for the cached part. That narrows the gap. It does nothing for attention: the model still has to find one sentence in 180,000 tokens, and a cached prompt is just as long as an uncached one.

## 5. Common mistakes and how to spot them

- **Quoting a promotional price as permanent.** Write the date you verified it and the standard price next to it.
- **Forgetting output tokens.** At $3.75 per million, output is five times the input rate. Long answers add up.
- **Assuming "fits in the context window" means "works".** Test with a golden set at your real input length.
- **Pricing only the happy path.** Refusals before the model call cost nothing; retries cost double. Read `logs/usage.jsonl` for the real mix.

### Exercise: estimate your capstone

Use about 500 tokens per page of ordinary text.

1. Count your corpus in pages. Multiply by 500. That is your corpus size in tokens.
2. Pick your chat model and verify its price on OpenRouter today. Write the date down.
3. Compute cost per question for Option A (corpus + 150 in, 150 out) and Option B (k × 300 + 150 in, 150 out).
4. Estimate questions per day for your users. Multiply both by 30 days.
5. Put the result in your retrieval spec, with one sentence on which you chose and why.

Example: 40 pages × 500 = 20,000 tokens. With the prices above, Option A is about $0.0157 per question, Option B $0.0018. At 200 questions a day for 30 days that is about $94 against $11.

## Check yourself

1. Using the prices above, what does one stuffed-corpus question cost in input tokens alone, and why is the output cost the same in both options?
2. What does "Lost in the Middle" tell you about where a relevant fact sits in a long prompt?
3. Prompt caching makes the long prompt cheap. Name one reason to still use retrieval for CampusPulse.

<details>
<summary>Answers</summary>

1. 180,150 / 1,000,000 × $0.75 ≈ $0.1351. Output is 150 tokens in both cases, so it costs $0.0005625 either way: retrieval only shrinks the input.
2. Accuracy follows a U shape: facts at the start or end of the context are used more reliably than facts in the middle.
3. Any of: attention still degrades with length (Context Rot); answers must cite a specific source; documents change; per-user access needs filtering at retrieval.

</details>
