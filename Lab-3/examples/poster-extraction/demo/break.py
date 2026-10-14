"""Live-demo helper: produce the 'first version' of checks.py, the one every
extraction pipeline starts as: no evidence check, and no tests for it.

    python demo/break.py        # removes the no_evidence branch and every test that depends on it
    python -m pytest -q         # all green: the bug is invisible to the tests that are left
    git checkout src/checks.py tests/   # restore everything (33 tests)

Run from the poster-extraction folder. Nothing here is used by the app or the tests.
"""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent

c = (HERE / "src" / "checks.py").read_text()
line = next(l for l in c.splitlines() if "no_evidence" in l and "elif" in l)
(HERE / "src" / "checks.py").write_text(c.replace(line + "\n", ""))

removed = 0
for tf in ("test_checks.py", "test_review.py"):
    path = HERE / "tests" / tf
    src = path.read_text()
    parts = re.split(r"(?=\ndef test_)", src)
    keep = []
    for p in parts:
        if p.startswith("\ndef test_") and ("no_evidence" in p or "evidence=None" in p):
            removed += 1
        else:
            keep.append(p)
    path.write_text("".join(keep))
print(f"evidence branch removed from checks.py · {removed} dependent tests removed · run: python -m pytest -q")
