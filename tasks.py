#!/usr/bin/env python3
"""The task queue. Start here if you want to help.

Tasks are computed from the state of the repository, plus the hand-written
list in tasks/backlog.toml, so the queue is never out of date: finish a task
and it disappears.

    python3 tasks.py                      summary and the first few of each kind
    python3 tasks.py list --mode ai       everything an agent can do alone
    python3 tasks.py list --kind review   everything of one kind
    python3 tasks.py show review:molar-mass
    python3 tasks.py review molar-mass --by <github-handle>   record a human review
    python3 tasks.py --json               the whole queue, for tools
"""
import argparse
import datetime
import hashlib
import json
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).parent
NODES = ROOT / "nodes"

TARGET_EXERCISES = 5  # the validator's minimum is 3; this is what a finished node has

# kind: (mode, what it asks for, playbook)
# mode "ai": an agent can finish it alone and the validator gates the result.
# mode "human": a person must take part; an agent guides them.
KINDS = {
    "review": ("human", "Review a lesson with a teacher", "tasks/playbooks/review.md"),
    "wanted": ("ai", "Write a missing prerequisite lesson", "tasks/playbooks/automated.md#write-a-lesson"),
    "derive": ("ai", "Make an answer recomputable", "tasks/playbooks/automated.md#make-an-answer-recomputable"),
    "variety": ("ai", "Add a different type of exercise", "tasks/playbooks/automated.md#add-exercises"),
    "exercises": ("ai", "Add practice problems", "tasks/playbooks/automated.md#add-exercises"),
    "interactive": ("ai", "Add an interactive model", "INTERACTIVES.md"),
    "video": ("ai", "Add a short video", "videos/README.md"),
    # The rest come from tasks/backlog.toml, where each task sets its own mode.
    "lesson": ("ai", "Write a new lesson", "tasks/playbooks/automated.md#write-a-lesson"),
    "tooling": ("ai", "Improve the tools", "tasks/playbooks/automated.md#tooling"),
    "classroom": ("human", "Try it in a classroom", None),
}


def load(path):
    return tomllib.loads(path.read_text())


def fingerprint(node_dir):
    """Changes whenever the lesson or its exercises change, which voids a review."""
    digest = hashlib.sha256()
    for name in ("lesson.md", "node.toml"):
        digest.update((node_dir / name).read_bytes())
    return digest.hexdigest()[:12]


def course():
    """Nodes in teaching order: by unit, then by depth in the prerequisite graph."""
    nodes = {p.name: load(p / "node.toml") for p in sorted(NODES.iterdir()) if p.is_dir()}
    unit_list = load(ROOT / "conventions" / "units.toml")["unit"]
    units = [u["id"] for u in unit_list]
    listed = {nid: i for u in unit_list for i, nid in enumerate(u.get("lessons", []))}
    depths = {}

    def depth(nid):
        if nid not in depths:
            depths[nid] = 1 + max([depth(p) for p in nodes[nid]["prerequisites"] if p in nodes], default=0)
        return depths[nid]

    # A unit may list its lessons in order; any it leaves out follow, by depth.
    order = sorted(nodes, key=lambda n: (units.index(nodes[n]["unit"]), listed.get(n, len(nodes)), depth(n), nodes[n]["title"]))
    return {nid: nodes[nid] for nid in order}


def review_of(nid):
    """The recorded human review of a node, with whether it still applies."""
    path = NODES / nid / "review.toml"
    if not path.exists():
        return None
    record = load(path)
    return {"by": record["by"], "on": str(record["on"]), "current": record["fingerprint"] == fingerprint(NODES / nid)}


def task(kind, node, detail, title=None, mode=None, playbook=None):
    default_mode, action, default_playbook = KINDS.get(kind, ("ai", "", None))
    return {
        "id": f"{kind}:{node}",
        "kind": kind,
        "mode": mode or default_mode,
        "node": node if (NODES / node).is_dir() else None,
        "title": title or action,
        "detail": detail,
        "playbook": playbook or default_playbook,
    }


def build():
    nodes = course()
    tasks = []

    for nid, node in nodes.items():
        review = review_of(nid)
        if review is None:
            tasks.append(task("review", nid, f"\"{node['title']}\" has never been reviewed by a person."))
        elif not review["current"]:
            tasks.append(task("review", nid, f"\"{node['title']}\" changed after {review['by']} reviewed it on {review['on']}."))

    wanted = sorted({p for node in nodes.values() for p in node["prerequisites"]} - nodes.keys())
    tasks += [task("wanted", w, f"Lessons list \"{w}\" as a prerequisite but it does not exist.") for w in wanted]

    for nid, node in nodes.items():
        exercises = node.get("exercise", [])
        loose = [i for i, ex in enumerate(exercises, 1) if ex["type"] == "numeric" and "derive" not in ex and not ex.get("recall")]
        if loose:
            which = ", ".join(str(i) for i in loose)
            tasks.append(task("derive", nid, f"\"{node['title']}\": numeric exercise {which} has an answer the validator cannot recompute."))

    for nid, node in nodes.items():
        types = {ex["type"] for ex in node.get("exercise", [])}
        if len(types) == 1:
            tasks.append(task("variety", nid, f"\"{node['title']}\": every exercise is of type \"{types.pop()}\"."))

    for nid, node in nodes.items():
        have = len(node.get("exercise", []))
        if have < TARGET_EXERCISES:
            tasks.append(task("exercises", nid, f"\"{node['title']}\" has {have} exercises; a finished lesson has {TARGET_EXERCISES}."))

    for nid, node in nodes.items():
        if not node.get("interactive"):
            tasks.append(task("interactive", nid, f"\"{node['title']}\" has no interactive. Add one only if changing a quantity teaches the idea."))

    for nid, node in nodes.items():
        if not node.get("video"):
            tasks.append(task("video", nid, f"\"{node['title']}\" has no video. Add one only if motion helps."))

    for item in load(ROOT / "tasks" / "backlog.toml")["task"]:
        tasks.append(task(item["kind"], item["id"], item["detail"], title=item["title"], mode=item["mode"], playbook=item.get("playbook")))

    reviews = {nid: r for nid in nodes if (r := review_of(nid))}
    return {"tasks": tasks, "reviews": reviews, "kinds": {k: {"mode": v[0], "title": v[1], "playbook": v[2]} for k, v in KINDS.items()}}


def print_task(t):
    print(f"  {t['id']:<44} {t['detail']}")


def cmd_summary(queue):
    tasks = queue["tasks"]
    print(f"{len(tasks)} open tasks. Modes: ai = an agent alone, human = an agent guiding a person.\n")
    kinds = list(dict.fromkeys(t["kind"] for t in tasks))
    for kind in kinds:
        group = [t for t in tasks if t["kind"] == kind]
        modes = "/".join(sorted({t["mode"] for t in group}))
        print(f"{kind} ({len(group)}, {modes}) — {KINDS[kind][1]}")
        for t in group[:3]:
            print_task(t)
        if len(group) > 3:
            print(f"  ... {len(group) - 3} more: python3 tasks.py list --kind {kind}")
        print()
    print("Details and the playbook for one task: python3 tasks.py show <task-id>")


def cmd_list(queue, kind, mode):
    for t in queue["tasks"]:
        if (kind is None or t["kind"] == kind) and (mode is None or t["mode"] == mode):
            print_task(t)


def cmd_show(queue, task_id):
    match = [t for t in queue["tasks"] if t["id"] == task_id]
    if not match:
        sys.exit(f"No open task {task_id!r}. It may already be done.")
    t = match[0]
    print(f"{t['id']}\n  {t['title']}\n  {t['detail']}\n  mode: {t['mode']}")
    if t["playbook"]:
        print(f"  playbook: {t['playbook']}")
    if t["node"]:
        print(f"  files: nodes/{t['node']}/lesson.md, nodes/{t['node']}/node.toml")
    print(f"  claim it: open a draft pull request whose title starts with \"{t['id']}\"")


def cmd_review(nid, by):
    node_dir = NODES / nid
    if not node_dir.is_dir():
        sys.exit(f"No node {nid!r}.")
    (node_dir / "review.toml").write_text(
        "# A person's sign-off on this lesson and its exercises. Written by\n"
        "# `python3 tasks.py review`; void as soon as the lesson changes.\n"
        f"by = {json.dumps(by)}\non = {datetime.date.today().isoformat()}\nfingerprint = {json.dumps(fingerprint(node_dir))}\n"
    )
    print(f"Recorded: {by} reviewed {nid}. Commit nodes/{nid}/review.toml with the changes.")


def main():
    parser = argparse.ArgumentParser(description="The task queue for this course.")
    parser.add_argument("--json", action="store_true", help="print the whole queue as JSON")
    commands = parser.add_subparsers(dest="command")
    listing = commands.add_parser("list", help="list open tasks")
    listing.add_argument("--kind")
    listing.add_argument("--mode", choices=["ai", "human"])
    commands.add_parser("show", help="describe one task").add_argument("task_id")
    review = commands.add_parser("review", help="record that a person reviewed a node")
    review.add_argument("node")
    review.add_argument("--by", required=True, help="the reviewer's GitHub handle")
    args = parser.parse_args()

    if args.command == "review":
        return cmd_review(args.node, args.by)
    queue = build()
    if args.json:
        print(json.dumps(queue, indent=1))
    elif args.command == "list":
        cmd_list(queue, args.kind, args.mode)
    elif args.command == "show":
        cmd_show(queue, args.task_id)
    else:
        cmd_summary(queue)


if __name__ == "__main__":
    main()
