# Evidence Rule · two lines for your pull request template

*From Lab 4 on, every feature you merge carries at least one test and one log entry. Your `.github/pull_request_template.md` (from Lab 2) already has the line "From Week 4 (Evidence Rule): this feature has at least one test and writes one log entry when it runs". Replace that one line with the two below, so a reviewer can see which test and which log line. The repo keeper makes the change, because it touches `.github/`.*

```markdown
### Evidence Rule
- [ ] **Test:** this change adds or updates at least one test that would fail if the feature broke (unit test in `tests/`, golden question in `evals/golden.yaml`, or eval case). Name it: ...
- [ ] **Log entry:** the running feature writes a line we can read later (usage, cost, latency, or what it decided and why). Where: ...
```

**What counts.** A test that cannot fail does not count (`assert len(r) >= 0` from Week 2 is the classic). A `print()` while debugging does not count; a line written to a log file by the feature, every time it runs, does.

**Docs-only and config-only pull requests** tick neither box and say "docs only" in the description.

**Reviewers:** if a box is ticked and you cannot find the test or the log line in the diff, do not approve. Ask.
