"""Review records and the parts of a lesson they vouch for.

Shared by tasks.py, validate.py and the CI guard, so all three agree on what
a part is, what its fingerprint is, and which reviews count. See TRUST.md.

A review names a fingerprint, not a file or a position. Change a part and its
fingerprint changes, so every review of the old version stops counting.
"""
import hashlib
import json
import math
import re
import tomllib
from pathlib import Path


def load(path):
    return tomllib.loads(Path(path).read_text())


def _fingerprint(*chunks):
    digest = hashlib.sha256()
    for chunk in chunks:
        digest.update(chunk if isinstance(chunk, bytes) else chunk.encode())
    return digest.hexdigest()[:12]


def _canonical(table):
    return json.dumps(table, sort_keys=True, ensure_ascii=False, default=str)


def node_ids(root):
    nodes = Path(root) / "nodes"
    return sorted(p.name for p in nodes.iterdir() if (p / "node.toml").exists()) if nodes.is_dir() else []


def parts(root, nid):
    """Every separately reviewable part of a node, with its current fingerprint."""
    root = Path(root)
    node_dir = root / "nodes" / nid
    node = load(node_dir / "node.toml")
    out = [{"key": "lesson", "label": "Lesson text", "fingerprint": _fingerprint((node_dir / "lesson.md").read_bytes())}]
    for i, ex in enumerate(node.get("exercise", []), 1):
        out.append({
            "key": f"exercise-{i}",
            "label": f"Exercise {i}",
            "fingerprint": _fingerprint(_canonical(ex)),
            "exercise": ex,
            # True when CI itself recalculates the answer on every change.
            "recomputed": ex.get("type") == "balance" or "derive" in ex,
        })
    for i, block in enumerate(node.get("interactive", []), 1):
        source = root / "src" / "interactives" / "kinds" / f"{block.get('kind')}.js"
        code = source.read_bytes() if source.exists() else b""
        out.append({"key": f"interactive-{i}", "label": f"Interactive: {block.get('title', '')}", "fingerprint": _fingerprint(_canonical(block), code)})
    animation = node_dir / "animation.toml"
    if animation.exists():
        kind = load(animation).get("kind")
        code = [root / "src" / "animations" / "kinds" / f"{kind}.js", root / "src" / "animations" / "player.js"]
        out.append({"key": "animation", "label": "Animation", "fingerprint": _fingerprint(animation.read_bytes(), *[f.read_bytes() for f in code if f.exists()])})
    return out


def records(root, nid):
    path = Path(root) / "nodes" / nid / "reviews.toml"
    return load(path).get("review", []) if path.exists() else []


def is_agent(record):
    """A record with a model was made by an AI. One without is a person's."""
    return "model" in record


def identity(record):
    """What makes two records the same review."""
    return (record.get("fingerprint"), str(record.get("by", "")).lower(), record.get("model"))


def people(root):
    """Who may do what, from conventions/reviewers.toml. Logins are lower-cased."""
    data = load(Path(root) / "conventions" / "reviewers.toml")
    return {
        "maintainers": {m.lower() for m in data.get("maintainers", [])},
        "reviewers": {r["github"].lower() for r in data.get("reviewer", [])},
    }


def standing(root, nid):
    """Each part of a node with the reviews that currently count for it."""
    approved = people(root)["reviewers"]
    recs = records(root, nid)
    out = []
    for part in parts(root, nid):
        current = [r for r in recs if r.get("fingerprint") == part["fingerprint"]]
        # A person's review counts only while they are on the reviewer list,
        # so removing someone from the list withdraws everything they signed.
        human = sorted({r["by"] for r in current if not is_agent(r) and r["by"].lower() in approved})
        agent = sorted({(r["by"], r["model"]) for r in current if is_agent(r)})
        out.append({**part, "human": human, "agent": [{"by": by, "model": model} for by, model in agent]})
    return out


def matches_key(ex, answer):
    """Does an independently worked answer agree with the exercise's key?"""
    text = str(answer).strip()
    kind = ex.get("type")
    if kind == "numeric":
        try:
            value = float(text)
        except ValueError:
            return False
        return math.isclose(value, ex["answer"], rel_tol=ex.get("tolerance", 0.01))
    if kind == "choice":
        return text == ex["options"][ex["answer"]]
    if kind == "text":
        normal = lambda s: " ".join(s.lower().split())  # noqa: E731
        return normal(text) in {normal(a) for a in [ex["answer"], *ex.get("accept", [])]}
    if kind == "balance":
        return [int(n) for n in re.findall(r"\d+", text)] == ex["answer"]["reactants"] + ex["answer"]["products"]
    return False
