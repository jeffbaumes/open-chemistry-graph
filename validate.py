#!/usr/bin/env python3
"""Validate every node in nodes/. Exits non-zero if any node fails.

Checks structure, the prerequisite graph, and -- where an exercise declares
how its answer is derived -- recomputes the chemistry instead of trusting it.
"""
import math
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).parent
NODES = ROOT / "nodes"
MIN_EXERCISES = 3
DEFAULT_TOLERANCE = 0.005  # relative

ATOMIC_MASS = tomllib.loads((ROOT / "conventions" / "elements.toml").read_text())["mass"]

TOKEN = re.compile(r"([A-Z][a-z]?)|(\()|(\))|(\d+)")


def parse_formula(formula):
    """'Ca(OH)2' -> {'Ca': 1, 'O': 2, 'H': 2}"""
    stack = [{}]
    pos = 0
    last = None  # the group a following number multiplies
    while pos < len(formula):
        m = TOKEN.match(formula, pos)
        if not m:
            raise ValueError(f"cannot parse formula {formula!r} at {formula[pos:]!r}")
        element, open_, close, count = m.groups()
        if element:
            if element not in ATOMIC_MASS:
                raise ValueError(f"unknown element {element!r} in {formula!r}")
            last = {element: 1}
            stack[-1][element] = stack[-1].get(element, 0) + 1
        elif open_:
            stack.append({})
            last = None
        elif close:
            if len(stack) == 1:
                raise ValueError(f"unbalanced parentheses in {formula!r}")
            last = stack.pop()
            for el, n in last.items():
                stack[-1][el] = stack[-1].get(el, 0) + n
        else:
            if last is None:
                raise ValueError(f"misplaced number in {formula!r}")
            for el, n in last.items():
                stack[-1][el] += n * (int(count) - 1)
            last = None
        pos = m.end()
    if len(stack) != 1:
        raise ValueError(f"unbalanced parentheses in {formula!r}")
    return stack[0]


def molar_mass(formula):
    return sum(ATOMIC_MASS[el] * n for el, n in parse_formula(formula).items())


def derive(spec):
    """Recompute a numeric answer from a declared derivation."""
    kind = spec.get("kind")
    if kind == "molar_mass":
        return molar_mass(spec["formula"])
    if kind == "moles_from_mass":
        return spec["mass_g"] / molar_mass(spec["formula"])
    if kind == "mass_from_moles":
        return spec["moles"] * molar_mass(spec["formula"])
    raise ValueError(f"unknown derive kind {kind!r}")


def check_numeric(ex):
    answer = ex["answer"]
    if not isinstance(answer, (int, float)):
        return ["answer must be a number"]
    if not ex.get("unit"):
        return ["numeric exercise needs a unit"]
    if "derive" in ex:
        expected = derive(ex["derive"])
        tol = ex.get("tolerance", DEFAULT_TOLERANCE)
        if not math.isclose(answer, expected, rel_tol=tol):
            return [f"answer {answer} does not match recomputed {expected:.5g}"]
    return []


def check_balance(ex):
    sides = []
    for side in ("reactants", "products"):
        total = {}
        species, coeffs = ex[side], ex["answer"][side]
        if len(species) != len(coeffs):
            return [f"{side}: need one coefficient per species"]
        for formula, c in zip(species, coeffs):
            if not isinstance(c, int) or c < 1:
                return [f"{side}: coefficients must be positive integers"]
            for el, n in parse_formula(formula).items():
                total[el] = total.get(el, 0) + n * c
        sides.append(total)
    if sides[0] != sides[1]:
        return [f"not balanced: {sides[0]} vs {sides[1]}"]
    if math.gcd(*ex["answer"]["reactants"], *ex["answer"]["products"]) != 1:
        return ["coefficients are not in lowest terms"]
    return []


def check_choice(ex):
    options = ex.get("options", [])
    if len(options) < 3:
        return ["choice exercise needs at least 3 options"]
    if len(set(options)) != len(options):
        return ["duplicate options"]
    if not isinstance(ex.get("answer"), int) or not 0 <= ex["answer"] < len(options):
        return ["answer must be the index of an option"]
    return []


CHECKERS = {"numeric": check_numeric, "balance": check_balance, "choice": check_choice}

MAX_LESSON_WORDS = 600

# House rules for lesson.md. Each is (message, test that returns True when broken).
# Add a rule here once a STYLE.md guideline is crisp enough to check by machine.
LESSON_RULES = [
    ("must start with a '# ' title", lambda text: not text.startswith("# ")),
    ("no raw HTML or inline styling; presentation belongs in the templates",
     lambda text: re.search(r"<[a-zA-Z/][^>]*>", text) is not None),
    ("write formulas and arrows plainly (H2O, ->); the site typesets them",
     lambda text: re.search(r"[\u2080-\u2089\u2192]", text) is not None),
    (f"longer than {MAX_LESSON_WORDS} words; split it into two nodes",
     lambda text: len(text.split()) > MAX_LESSON_WORDS),
]


def check_node(path):
    errors = []
    node = tomllib.loads((path / "node.toml").read_text())
    for field in ("title", "summary", "prerequisites"):
        if field not in node:
            errors.append(f"missing field {field!r}")
    lesson = path / "lesson.md"
    if not lesson.exists() or not lesson.read_text().strip():
        errors.append("missing or empty lesson.md")
    else:
        text = lesson.read_text()
        errors += [f"lesson.md: {message}" for message, broken in LESSON_RULES if broken(text)]
    exercises = node.get("exercise", [])
    if len(exercises) < MIN_EXERCISES:
        errors.append(f"needs at least {MIN_EXERCISES} exercises, has {len(exercises)}")
    for i, ex in enumerate(exercises, 1):
        checker = CHECKERS.get(ex.get("type"))
        if not ex.get("prompt"):
            errors.append(f"exercise {i}: missing prompt")
        if checker is None:
            errors.append(f"exercise {i}: unknown type {ex.get('type')!r}")
            continue
        try:
            errors += [f"exercise {i}: {e}" for e in checker(ex)]
        except (KeyError, ValueError, TypeError) as e:
            errors.append(f"exercise {i}: {e!r}")
    return node, errors


def find_cycle(graph):
    state = {}

    def visit(n, trail):
        if state.get(n) == "done" or n not in graph:
            return None
        if state.get(n) == "open":
            return trail[trail.index(n):] + [n]
        state[n] = "open"
        for p in graph[n]:
            if cycle := visit(p, trail + [n]):
                return cycle
        state[n] = "done"
        return None

    for n in graph:
        if cycle := visit(n, []):
            return cycle
    return None


def main():
    failed = False
    graph = {}
    for path in sorted(p for p in NODES.iterdir() if p.is_dir()):
        try:
            node, errors = check_node(path)
        except (OSError, tomllib.TOMLDecodeError) as e:
            node, errors = {}, [str(e)]
        graph[path.name] = node.get("prerequisites", [])
        print(f"{'FAIL' if errors else 'ok  '} {path.name}")
        for e in errors:
            print(f"       {e}")
        failed = failed or bool(errors)

    if cycle := find_cycle(graph):
        print(f"FAIL prerequisite cycle: {' -> '.join(cycle)}")
        failed = True

    wanted = sorted({p for prereqs in graph.values() for p in prereqs} - graph.keys())
    if wanted:
        print("\nWanted nodes (referenced as prerequisites, not yet written):")
        for w in wanted:
            print(f"  {w}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
