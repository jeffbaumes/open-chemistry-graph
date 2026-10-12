#!/usr/bin/env python3
"""Guard the review records in a pull request. See TRUST.md.

Run by .github/workflows/review-guard.yml with two checkouts:

    review_guard.py --base <trusted checkout of the target branch>
                    --head <the pull request's files, never executed>
                    --author <GitHub login that opened the pull request>

The rules come from the BASE checkout, so a pull request cannot loosen them,
add its own author to the reviewer list, or edit this script to pass itself.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import trust  # noqa: E402

HUMAN_NODES_PER_PR = 1  # a person reviews one lesson per pull request
AGENT_NODES_PER_PR = 3

# Changing these changes who is trusted or what is checked.
PROTECTED = [".github", "ci", "validate.py", "tasks.py", "conventions/reviewers.toml"]


def tree(root, relative):
    """{path: bytes} for a file or directory, relative to root."""
    path = Path(root) / relative
    if path.is_file():
        return {relative: path.read_bytes()}
    return {str(f.relative_to(root)): f.read_bytes() for f in sorted(path.rglob("*")) if f.is_file()} if path.is_dir() else {}


def check(base, head, author):
    problems = []
    author = author.lower()
    rules = trust.people(base)  # from the target branch, not from the pull request

    changed = sorted(p for p in PROTECTED if tree(base, p) != tree(head, p))
    if changed and author not in rules["maintainers"]:
        problems.append(f"changes {', '.join(changed)}, which decide who is trusted and what is checked. Only a maintainer may change them.")

    human_nodes, agent_nodes = set(), set()
    for nid in sorted(set(trust.node_ids(base)) | set(trust.node_ids(head))):
        in_head = nid in trust.node_ids(head)
        head_parts = {p["fingerprint"]: p for p in trust.parts(head, nid)} if in_head else {}
        base_prints = {p["fingerprint"] for p in trust.parts(base, nid)} if nid in trust.node_ids(base) else set()
        before = trust.records(base, nid)
        after = trust.records(head, nid) if in_head else []
        seen = [trust.identity(r) for r in after]

        for record in before:
            if trust.identity(record) not in seen and record.get("fingerprint") in head_parts:
                problems.append(f"{nid}: removes or alters {record.get('by')}'s review of a part that has not changed. Reviews can only be added.")
        for identity in {i for i in seen if seen.count(i) > 1}:
            problems.append(f"{nid}: the same review of {identity[0]} by {identity[1]} appears more than once.")

        known = [trust.identity(r) for r in before]
        for record in after:
            if trust.identity(record) in known:
                continue
            where = f"{nid}: new review of {record.get('part', '?')}"
            by = str(record.get("by", "")).lower()
            if by != author:
                problems.append(f"{where} is signed {record.get('by')!r}, but this pull request was opened by {author!r}. You can only record your own review.")
            part = head_parts.get(record.get("fingerprint"))
            if part is None:
                problems.append(f"{where} does not match the current content of any part. Record reviews after the last edit.")
                continue
            if trust.is_agent(record):
                agent_nodes.add(nid)
                if record["fingerprint"] not in base_prints:
                    problems.append(f"{where}: an AI review cannot cover a part changed in the same pull request. That would be reviewing its own work.")
                if "exercise" in part:
                    if "answer" not in record:
                        problems.append(f"{where}: an AI review of an exercise must include the answer it worked out.")
                    elif not trust.matches_key(part["exercise"], record["answer"]):
                        problems.append(f"{where}: the recorded answer {record['answer']!r} does not agree with the key. A disagreement is a bug report, not a review.")
            else:
                human_nodes.add(nid)
                if by not in rules["reviewers"]:
                    problems.append(f"{where}: {record.get('by')} is not on the reviewer list, so this cannot count as a person's review. A maintainer adds reviewers in conventions/reviewers.toml, in a separate pull request.")

    if len(human_nodes) > HUMAN_NODES_PER_PR:
        problems.append(f"records human reviews in {len(human_nodes)} lessons. Review {HUMAN_NODES_PER_PR} lesson per pull request.")
    if len(agent_nodes) > AGENT_NODES_PER_PR:
        problems.append(f"records AI reviews in {len(agent_nodes)} lessons. The limit is {AGENT_NODES_PER_PR} per pull request.")
    return problems


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--author", required=True)
    args = parser.parse_args()
    problems = check(args.base, args.head, args.author)
    for problem in problems:
        print(f"FAIL {problem}")
    print("Review guard: " + (f"{len(problems)} problem(s)" if problems else "ok"))
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
