#!/usr/bin/env python3
"""Tests for the review guard. Each case builds a fake pull request against a
tiny repository and checks the guard accepts or rejects it for the right reason.
"""
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import trust  # noqa: E402
from review_guard import check  # noqa: E402

NODE = '''title = "T"
summary = "S"
unit = "matter"
prerequisites = []

[[exercise]]
type = "numeric"
prompt = "What is 2 + 2?"
answer = 4
unit = "things"
derive = "2 + 2"

[[exercise]]
type = "choice"
prompt = "Pick b."
options = ["a", "b", "c"]
answer = 1
'''
PEOPLE = 'maintainers = ["owner"]\n\n[[reviewer]]\ngithub = "teacher"\n'


def repo(root):
    for nid in ("one", "two", "three", "four"):
        d = root / "nodes" / nid
        d.mkdir(parents=True)
        (d / "node.toml").write_text(NODE)
        (d / "lesson.md").write_text(f"# {nid}\n\nText.\n")
    (root / "conventions").mkdir()
    (root / "conventions" / "reviewers.toml").write_text(PEOPLE)
    (root / "validate.py").write_text("# checks\n")


def record(root, nid, key, by, model=None, answer=None, fingerprint=None):
    part = next(p for p in trust.parts(root, nid) if p["key"] == key)
    lines = ["", "[[review]]", f'part = "{key}"', f'fingerprint = "{fingerprint or part["fingerprint"]}"', f'by = "{by}"']
    if model:
        lines.append(f'model = "{model}"')
    if answer is not None:
        lines.append(f'answer = "{answer}"')
    with open(root / "nodes" / nid / "reviews.toml", "a") as f:
        f.write("\n".join(lines) + "\n")


def case(name, author, change, expect, setup=None):
    with tempfile.TemporaryDirectory() as tmp:
        base, head = Path(tmp) / "base", Path(tmp) / "head"
        repo(base)
        if setup:
            setup(base)
        shutil.copytree(base, head)
        change(head)
        problems = check(base, head, author)
        ok = (not problems) if expect is None else any(expect in p for p in problems)
        print(f"{'ok  ' if ok else 'FAIL'} {name}")
        if not ok:
            print(f"       wanted {expect!r}, got {problems}")
        return ok


def edit_lesson(root):
    (root / "nodes" / "one" / "lesson.md").write_text("# one\n\nNew text.\n")


results = [
    case("a listed reviewer records their own review", "teacher",
         lambda h: record(h, "one", "lesson", "teacher"), None),
    case("a reviewer may fix a lesson and review the result", "Teacher",
         lambda h: (edit_lesson(h), record(h, "one", "lesson", "teacher")), None),
    case("someone not on the list cannot record a human review", "stranger",
         lambda h: record(h, "one", "lesson", "stranger"), "not on the reviewer list"),
    case("nobody can sign as someone else", "stranger",
         lambda h: record(h, "one", "lesson", "teacher"), "only record your own"),
    case("adding yourself to the list in the same pull request does not work", "stranger",
         lambda h: ((h / "conventions" / "reviewers.toml").write_text(PEOPLE + '\n[[reviewer]]\ngithub = "stranger"\n'),
                    record(h, "one", "lesson", "stranger")), "not on the reviewer list"),
    case("only a maintainer may change the checks", "teacher",
         lambda h: (h / "validate.py").write_text("# nothing\n"), "Only a maintainer"),
    case("a maintainer may change the checks", "owner",
         lambda h: (h / "validate.py").write_text("# better\n"), None),
    case("a review must match the current content", "teacher",
         lambda h: record(h, "one", "lesson", "teacher", fingerprint="000000000000"), "does not match the current content"),
    case("one lesson per pull request for human reviews", "teacher",
         lambda h: (record(h, "one", "lesson", "teacher"), record(h, "two", "lesson", "teacher")), "per pull request"),
    case("an AI review with the right answer is accepted", "anyone",
         lambda h: record(h, "one", "exercise-1", "anyone", model="some-model", answer="4.0"), None),
    case("an AI review needs its worked answer", "anyone",
         lambda h: record(h, "one", "exercise-1", "anyone", model="some-model"), "must include the answer"),
    case("an AI review that disagrees with the key is rejected", "anyone",
         lambda h: record(h, "one", "exercise-2", "anyone", model="some-model", answer="c"), "does not agree with the key"),
    case("an AI cannot review what the same pull request wrote", "anyone",
         lambda h: (edit_lesson(h), record(h, "one", "lesson", "anyone", model="some-model")), "its own work"),
    case("AI reviews are limited per pull request", "anyone",
         lambda h: [record(h, n, "exercise-1", "anyone", model="m", answer="4") for n in ("one", "two", "three", "four")], "limit is"),
    case("a current review cannot be deleted", "stranger",
         lambda h: (h / "nodes" / "one" / "reviews.toml").unlink(), "can only be added",
         setup=lambda b: record(b, "one", "lesson", "teacher")),
    case("a review of content that has since changed may be cleared", "stranger",
         lambda h: (edit_lesson(h), (h / "nodes" / "one" / "reviews.toml").unlink()), None,
         setup=lambda b: record(b, "one", "lesson", "teacher")),
    case("the same review cannot be recorded twice", "teacher",
         lambda h: (record(h, "one", "lesson", "teacher"), record(h, "one", "lesson", "teacher")), "more than once"),
]
print(f"{sum(results)} of {len(results)} guard tests pass")
sys.exit(0 if all(results) else 1)
