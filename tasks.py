#!/usr/bin/env python3
"""The task queue. Start here if you want to help.

Tasks are computed from the state of the repository, plus the hand-written
list in tasks/backlog.toml, so the queue is never out of date: finish a task
and it disappears.

    python3 tasks.py                      summary and the first few of each kind
    python3 tasks.py list --mode ai       everything an agent can do alone
    python3 tasks.py list --kind review   everything of one kind
    python3 tasks.py show review:molar-mass
    python3 tasks.py status molar-mass    reviews of each part of a lesson
    python3 tasks.py blind molar-mass     the exercises without their answers
    python3 tasks.py review molar-mass    record a person's review (see TRUST.md)
    python3 tasks.py agent-review molar-mass --part exercise-1 --model <name> --answer 18.0
    python3 tasks.py --json               the whole queue, for tools
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "ci"))
import trust  # noqa: E402

NODES = ROOT / "nodes"
TARGET_EXERCISES = 5  # the validator's minimum is 3; this is what a finished node has

# kind: (mode, what it asks for, playbook)
# mode "ai": an agent can finish it alone and CI gates the result.
# mode "human": a person must take part; an agent guides them.
KINDS = {
    "review": ("human", "Review a lesson with a teacher", "tasks/playbooks/review.md"),
    "agent-review": ("ai", "Check a lesson independently", "tasks/playbooks/agent-review.md"),
    "wanted": ("ai", "Write a missing prerequisite lesson", "tasks/playbooks/automated.md#write-a-lesson"),
    "derive": ("ai", "Make an answer recomputable", "tasks/playbooks/automated.md#make-an-answer-recomputable"),
    "variety": ("ai", "Add a different type of exercise", "tasks/playbooks/automated.md#add-exercises"),
    "exercises": ("ai", "Add practice problems", "tasks/playbooks/automated.md#add-exercises"),
    "interactive": ("ai", "Add an interactive model", "INTERACTIVES.md"),
    "animation": ("ai", "Add a step-through animation", "ANIMATIONS.md"),
    # The rest come from tasks/backlog.toml, where each task sets its own mode.
    "lesson": ("ai", "Write a new lesson", "tasks/playbooks/automated.md#write-a-lesson"),
    "tooling": ("ai", "Improve the tools", "tasks/playbooks/automated.md#tooling"),
    "classroom": ("human", "Try it in a classroom", None),
}


def course():
    """Nodes in teaching order: by unit, then by depth in the prerequisite graph."""
    nodes = {nid: trust.load(NODES / nid / "node.toml") for nid in trust.node_ids(ROOT)}
    unit_list = trust.load(ROOT / "conventions" / "units.toml")["unit"]
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
    standing = {nid: trust.standing(ROOT, nid) for nid in nodes}
    tasks = []

    for nid, node in nodes.items():
        missing = [p for p in standing[nid] if not p["human"]]
        if missing:
            tasks.append(task("review", nid, f"\"{node['title']}\": {len(missing)} of {len(standing[nid])} parts have no human review."))

    for nid, node in nodes.items():
        missing = [p for p in standing[nid] if not p["agent"]]
        if missing:
            tasks.append(task("agent-review", nid, f"\"{node['title']}\": {len(missing)} of {len(standing[nid])} parts have no independent AI review."))

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
        if not (NODES / nid / "animation.toml").exists():
            tasks.append(task("animation", nid, f"\"{node['title']}\" has no animation. Add one only if seeing the steps in motion helps."))

    for item in trust.load(ROOT / "tasks" / "backlog.toml")["task"]:
        tasks.append(task(item["kind"], item["id"], item["detail"], title=item["title"], mode=item["mode"], playbook=item.get("playbook")))

    # What the site shows: every part of every lesson and who has reviewed it.
    public = {nid: [{k: v for k, v in part.items() if k != "exercise"} for part in parts] for nid, parts in standing.items()}
    every = [part for parts in public.values() for part in parts]
    exercises = [p for p in every if p["key"].startswith("exercise-")]
    totals = {
        "parts": len(every),
        "human": sum(1 for p in every if p["human"]),
        "agent": sum(1 for p in every if p["agent"]),
        "exercises": len(exercises),
        "recomputed": sum(1 for p in exercises if p["recomputed"]),
    }
    return {
        "tasks": tasks,
        "trust": public,
        "totals": totals,
        "kinds": {k: {"mode": v[0], "title": v[1], "playbook": v[2]} for k, v in KINDS.items()},
    }


# --- Commands ----------------------------------------------------------------

def print_task(t):
    print(f"  {t['id']:<44} {t['detail']}")


def cmd_summary(queue):
    tasks, totals = queue["tasks"], queue["totals"]
    print(f"{len(tasks)} open tasks. Modes: ai = an agent alone, human = an agent guiding a person.")
    print(f"{totals['human']} of {totals['parts']} parts reviewed by a person, {totals['agent']} by an independent AI; "
          f"{totals['recomputed']} of {totals['exercises']} exercise answers recomputed by CI.\n")
    for kind in dict.fromkeys(t["kind"] for t in tasks):
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


def need_node(nid):
    if not (NODES / nid / "node.toml").exists():
        sys.exit(f"No node {nid!r}.")


def cmd_status(nid):
    need_node(nid)
    for part in trust.standing(ROOT, nid):
        human = ", ".join(part["human"]) or "none"
        agent = ", ".join(f"{a['by']} ({a['model']})" for a in part["agent"]) or "none"
        computed = "  answer recomputed by CI" if part.get("recomputed") else ""
        print(f"{part['key']:<16} human: {human:<20} AI: {agent}{computed}")


def cmd_blind(nid):
    """Print the exercises without their answers, for working them independently."""
    need_node(nid)
    for part in trust.parts(ROOT, nid):
        ex = part.get("exercise")
        if not ex:
            continue
        print(f"{part['key']} ({ex['type']}): {ex['prompt']}")
        if ex["type"] == "choice":
            print("    options: " + " | ".join(ex["options"]))
        elif ex["type"] == "balance":
            print(f"    {' + '.join(ex['reactants'])} -> {' + '.join(ex['products'])}   (answer as coefficients in order, such as \"2 1 2\")")
        elif ex["type"] == "numeric":
            print(f"    answer in: {ex['unit']}")


def login(given):
    """The GitHub account recording the review. CI checks it against the pull request's author."""
    if given:
        return given
    try:
        return subprocess.run(["gh", "api", "user", "-q", ".login"], capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        sys.exit("Could not read your GitHub login from `gh`. Sign in with `gh auth login`, or pass --by <login>.")


def append(nid, part, by, model=None, answer=None):
    lines = ["", "[[review]]", f"part = {json.dumps(part['key'])}", f"fingerprint = {json.dumps(part['fingerprint'])}", f"by = {json.dumps(by)}"]
    if model:
        lines.append(f"model = {json.dumps(model)}")
    if answer is not None:
        lines.append(f"answer = {json.dumps(str(answer))}")
    path = NODES / nid / "reviews.toml"
    header = "" if path.exists() else "# Reviews of the parts of this lesson. Written by tasks.py and checked by CI.\n# A review stops counting when the part it names changes. See TRUST.md.\n"
    with open(path, "a") as f:
        f.write(header + "\n".join(lines) + "\n")


def cmd_review(nid, wanted, by):
    need_node(nid)
    by = login(by)
    if by.lower() not in trust.people(ROOT)["reviewers"]:
        sys.exit(f"{by} is not on the reviewer list in conventions/reviewers.toml, so this review would not count and CI would reject it.\n"
                 "Ask a maintainer to add you (in its own pull request), then record the review.")
    standing = trust.standing(ROOT, nid)
    chosen = [p for p in standing if not wanted or p["key"] in wanted]
    if wanted and len(chosen) != len(set(wanted)):
        sys.exit(f"Unknown part. This lesson has: {', '.join(p['key'] for p in standing)}")
    added = [p for p in chosen if by not in p["human"]]
    for part in added:
        append(nid, part, by)
    print(f"Recorded {by}'s review of {len(added)} part(s) of {nid}: {', '.join(p['key'] for p in added) or 'nothing new'}.")
    print(f"Commit nodes/{nid}/reviews.toml and open the pull request from {by}'s own account.")


def cmd_agent_review(nid, key, model, answer, by):
    need_node(nid)
    by = login(by)
    part = next((p for p in trust.standing(ROOT, nid) if p["key"] == key), None)
    if part is None:
        sys.exit(f"Unknown part {key!r}. See: python3 tasks.py status {nid}")
    if "exercise" in part:
        if answer is None:
            sys.exit("An AI review of an exercise needs --answer: the answer you worked out without looking at the key.")
        if not trust.matches_key(part["exercise"], answer):
            sys.exit(f"Your answer {answer!r} does not agree with the key for {key}.\n"
                     "Nothing was recorded. Work out which is right and report it: a wrong key or an ambiguous question is worth more than a review.")
    if any(a["by"] == by and a["model"] == model for a in part["agent"]):
        sys.exit(f"{by} has already recorded a {model} review of {key}.")
    append(nid, part, by, model=model, answer=answer if "exercise" in part else None)
    print(f"Recorded an AI review of {nid} {key} by {by} using {model}.")


def main():
    parser = argparse.ArgumentParser(description="The task queue for this course.")
    parser.add_argument("--json", action="store_true", help="print the whole queue as JSON")
    commands = parser.add_subparsers(dest="command")
    listing = commands.add_parser("list", help="list open tasks")
    listing.add_argument("--kind")
    listing.add_argument("--mode", choices=["ai", "human"])
    commands.add_parser("show", help="describe one task").add_argument("task_id")
    commands.add_parser("status", help="reviews of each part of a lesson").add_argument("node")
    commands.add_parser("blind", help="a lesson's exercises without their answers").add_argument("node")
    review = commands.add_parser("review", help="record a person's review of a lesson")
    review.add_argument("node")
    review.add_argument("--part", action="append", help="review only this part; repeat for several (default: all)")
    review.add_argument("--by", help="GitHub login (default: read from gh)")
    agent = commands.add_parser("agent-review", help="record an AI's independent review of one part")
    agent.add_argument("node")
    agent.add_argument("--part", required=True)
    agent.add_argument("--model", required=True, help="the model that did the review")
    agent.add_argument("--answer", help="for an exercise: the answer worked out without the key")
    agent.add_argument("--by", help="GitHub login (default: read from gh)")
    args = parser.parse_args()

    if args.command == "review":
        return cmd_review(args.node, args.part, args.by)
    if args.command == "agent-review":
        return cmd_agent_review(args.node, args.part, args.model, args.answer, args.by)
    if args.command == "status":
        return cmd_status(args.node)
    if args.command == "blind":
        return cmd_blind(args.node)
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
