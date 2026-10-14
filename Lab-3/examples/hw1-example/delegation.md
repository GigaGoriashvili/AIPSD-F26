# HW1 delegation log · Next three events for a club

**Date:** 2026-10-03 · **Tool:** Claude Code · **Rung on the Autonomy Ladder:** 3 (agent drafts code, I review every diff before anything is kept)

**What I delegated.** "Implement `next_events(club, today)` and the CLI described in `spec.md`. Propose a plan first. Do not write files until I approve the plan." Then, after the plan: "Build it, tests first."

**What the plan got wrong.** The plan proposed loading `events.json` inside the function on every call. Fine for 200 rows, wrong habit; I asked for a module-level load with a `reload()` helper. The plan had no test for the unknown-club case, which is acceptance criterion 4. I added it to the plan before approving.

**What the code got wrong.** (1) Sorting used the string `date` only, so two events on the same day came back in file order; the test `test_same_day_sorted_by_time` caught it. (2) The suggestion list for unknown clubs used `startswith`, so a one-letter typo gave one suggestion; golden question 3 caught it. (3) The agent wrote a test that asserted the exact seed file length (200), which would break the moment anyone adds an event; I deleted that test.

**How I verified.** Read `tests/` before `src/`. Ran `pytest src` myself (7 passed). Ran the three golden questions from the command line and pasted the real outputs into `golden.md`. Checked the diff for any network import; there is none.

**What I would change next time.** Put the unknown-club behaviour in the spec more precisely (how many suggestions, in what order). The agent cannot read a rule I did not write.
