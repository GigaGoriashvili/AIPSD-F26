# Golden sets and the Evidence Rule

*Helps with Lab 4, Part 3: golden set.*

## 1. The idea in plain language

You can unit-test `check_citations()`: same input, same output, every time. You cannot unit-test "CampusPulse answers room-booking questions correctly". The model's wording changes, retrieval depends on the whole corpus, and there is no single right string.

A **golden question** is an acceptance criterion for behaviour like that. It is a real question, plus the few things any correct answer must have: did it answer or refuse, which document must it cite, which phrase must it contain. A **golden set** is a small file of these, a pass threshold, and a script that runs them through the real pipeline.

It proves the system has not broken the things you decided matter.

## 2. Why it matters in production

"Membership costs 20 GEL [1]." passes every check in `check_citations()`, because source 1 is real (see `grounding-and-citations.md`). Only a test that knows the expected answer catches it: golden question g1, with `must_mention: [free]`.

Golden sets also catch harmless-looking regressions. "Use k=1 to save tokens" drops the pass rate under the threshold, as we will see.

## 3. Worked example: CampusPulse, step by step

### The file

`evals/golden.yaml` has a `threshold` and a list of `items`. Here is g2:

```yaml
- id: g2
  type: factual
  question: How many days ahead must a club book a room for an evening event?
  expect: answered
  must_cite: [regulations/room-booking]
  must_mention: [five working days]
  why: a rule with a number in it; numbers are where invented answers hurt most
```

- `expect`: `answered` or `refused`.
- `must_cite`: doc ids (path under `data/corpus`, no `.md`) that must be among the cited sources.
- `must_mention`: phrases that must appear in the answer, case-insensitive.
- `why`: one line on what this question protects.

### The composition

Week 4 asks for five questions with `threshold: 0.70`:

| Type | Count | CampusPulse item |
|---|---|---|
| factual | 2 | g1 Robotics fee, g2 booking notice |
| reasoning | 1 | g3 snacks at Open Build Night (needs the club policy, not the event page) |
| edge | 1 | g4 "when does the robtics club meet" (typo, no capitals) |
| refusal | 1 | g5 library Wi-Fi password (not in our sources) |

`test_golden_set_follows_the_week_4_composition` enforces this. In Week 11 the set grows to 10 items: 3 factual, 2 reasoning, 2 edge, 2 refusal and 1 format question.

The refusal item is not optional. A system that answers everything passes every factual question and fails the one that protects users from confident nonsense.

### How `score()` decides

`evals/run_golden.py::score()` collects every reason an item failed, not just the first:

```python
why = []
if result.status != item["expect"]:
    why.append(f"expected {item['expect']}, got {result.status} ({result.reason or 'no reason'})")
if item["expect"] == "answered":
    cited = {s["doc_id"] for s in result.sources}
    why += [f"did not cite {d}" for d in item.get("must_cite", []) if d not in cited]
    text = result.text.lower()
    why += [f"did not mention '{m}'" for m in item.get("must_mention", []) if m.lower() not in text]
return (not why), why
```

An item passes when `why` is empty. The list goes into the results file, so a failure says *what* broke.

### Writing good `must_mention` phrases

`must_mention` is a substring check. Keep phrases short and exact:

- **Good:** `free`, `five working days`, `wednesday`, `not allowed`. These are the facts. Any correct answer must contain them.
- **Too long:** `membership is free and you join at a Wednesday meeting`. A correct answer worded differently fails.
- **Too loose:** `club`. Every answer passes.
- **Watch the wording in the source.** The room-booking rule says "five working days", not "5 days". If the model may write "5 working days", run live and look at the answers before you decide. Either accept the failure as a real wording drift or choose a phrase both forms share.

Use one or two phrases per item. Each phrase is a claim about what a correct answer must say.

### Run it, change one thing, run it again

From the example root, offline (after `python -m src.index`):

```
CAMPUSPULSE_OFFLINE=1 python -m evals.run_golden
CAMPUSPULSE_OFFLINE=1 python -m evals.run_golden --k 1
```

Or run both with `python -m demo.break k`. The committed results files are `evals/results/2026-10-13-2335-offline-k5.json` and `evals/results/2026-10-13-2335-offline-k1.json`:

| Item | k=5 | k=1 |
|---|---|---|
| g1 factual | pass | pass |
| g2 factual | pass | pass |
| g3 reasoning | fail | fail |
| g4 edge | pass | fail |
| g5 refusal | pass | pass |
| **Pass rate** | **4/5 = 0.80** | **3/5 = 0.60** |
| **Exit code** | **0, merge allowed** | **1, merge blocked** |

Why g4 breaks at k=1: the single top chunk for "when does the robtics club meet" is the Robotics Contact section, not Meetings. With only that one source the answer cannot be found, so it is refused ("model: sources do not answer it"). At k=5 the Meetings section is in the set and the answer cites it.

Why g3 fails in **both** runs: offline mode uses the trigram stand-in, which matches letters, not meaning. "snacks" shares no trigrams with "food", so the food-and-drink rule in `regulations/club-policy` is not retrieved in the top 5 (it lands sixth). The extractive offline answerer then answers from the Open Build Night page, and score() reports `did not cite regulations/club-policy` and `did not mention 'not allowed'`. That is a limit of the stand-in. A real embedding model should connect snacks and food.

### Run it live before you trust it

Offline numbers measure retrieval wiring and the citation checks. They say nothing about how well a real model answers. Before you report a pass rate, run with your key set and without `CAMPUSPULSE_OFFLINE`:

```
python -m evals.run_golden
```

The results file records `mode` (`live` or `offline`), `chat_model`, `embed_model` and `k`, so nobody confuses the two.

### Commit the results

`run_golden` writes `evals/results/<timestamp>-<mode>-k<k>.json` and exits 1 below the threshold. Commit the file with the change that produced it: it is the evidence the change did what you said. Two files side by side is how you argue for a setting.

## 4. The Evidence Rule

From Lab 4 on, **every merged feature ships with at least one test and one log entry.**

- **A test:** a unit test, a golden question or an eval case. Something that fails if the feature breaks.
- **A log entry:** a line the running feature writes, so you can see what it did in real use.

For CampusPulse `/ask`:

- Tests: `tests/test_answer.py` covers each route and each citation check, and `evals/golden.yaml` covers behaviour.
- Log entries: every call to `answer()` writes one line to `logs/answers.jsonl` (question, status, reason, k, best_score, retrieved, cited). Every model call, chat or embedding, writes one line to `logs/usage.jsonl` (model, tokens, cost_usd, latency_ms). `test_every_answer_writes_one_log_line` proves the first.

The same idea appears in HW1: `golden.md` holds 3 golden questions for the feature you build alone, in the Lab 3 table format (input · expected · actual · pass or fail · how you ran it; see `Lab-3/examples/hw1-example/golden.md`). It stays a table, not YAML. What carries over from tonight is the habit: write each expected answer precisely enough that a script could check it.

## 5. Common mistakes and how to spot them

- **Only happy-path questions.** No refusal item means the threshold is never tested.
- **`must_mention` copied from the model's last answer.** Write it from the source document first.
- **Editing the golden set to match the system.** Decide whether the system or the item is wrong, and say which in the commit message.
- **Reporting offline numbers as quality.** Check `mode` in the results file.
- **Running once.** Rerun on every change to chunking, k, threshold, prompt or model.

## Check yourself

1. Why can't a unit test replace golden question g1?
2. g4 passes at k=5 and fails at k=1 offline. What does the results file say went wrong at k=1, and what caused it?
3. Under the Evidence Rule, what are the test and the log entry for CampusPulse `/ask`?

<details>
<summary>Answers</summary>

1. g1 checks the behaviour of the whole pipeline (retrieval, a model, the checks) against a known fact: the answer must say "free" and cite `clubs/robotics`. A wrong but properly cited answer passes every unit-tested check.
2. `expected answered, got refused (model: sources do not answer it)`, plus missing citation and mention. With k=1 the only source retrieved was the Robotics Contact section, which does not contain the meeting time.
3. Tests: `tests/test_answer.py` and the golden set in `evals/golden.yaml`. Log entries: one line per answer in `logs/answers.jsonl`, and one usage line per model call in `logs/usage.jsonl`.

</details>
