#!/usr/bin/env python3
"""Validate every node in nodes/. Exits non-zero if any node fails.

Checks structure, the prerequisite graph, and -- where an exercise declares
how its answer is derived -- recomputes the chemistry instead of trusting it.
"""
import ast
import math
import operator
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).parent
NODES = ROOT / "nodes"
CONVENTIONS = ROOT / "conventions"
INTERACTIVES = ROOT / "src" / "interactives" / "kinds"
MIN_EXERCISES = 3
DEFAULT_TOLERANCE = 0.005  # relative


def convention(name):
    return tomllib.loads((CONVENTIONS / name).read_text())


ATOMIC_MASS = convention("elements.toml")["mass"]
CONSTANTS = convention("constants.toml")["value"]
UNITS = [unit["id"] for unit in convention("units.toml")["unit"]]

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


OPERATORS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow,
}
FUNCTIONS = {"M": molar_mass, "log10": math.log10, "sqrt": math.sqrt, "min": min, "max": max}


def evaluate(expression):
    """Evaluate arithmetic such as "36.0 / M('H2O')".

    Allows numbers, + - * / **, the constants in conventions/constants.toml,
    and M(formula), log10, sqrt, min and max. Nothing else.
    """
    def ev(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float, str)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
            return OPERATORS[type(node.op)](ev(node.left), ev(node.right))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -ev(node.operand)
        if isinstance(node, ast.Name) and node.id in CONSTANTS:
            return CONSTANTS[node.id]
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in FUNCTIONS:
            return FUNCTIONS[node.func.id](*[ev(arg) for arg in node.args])
        raise ValueError(f"not allowed in a derive expression: {ast.unparse(node)}")

    return ev(ast.parse(expression, mode="eval").body)


def derive(spec):
    """Recompute a numeric answer from a declared derivation."""
    if isinstance(spec, str):
        return evaluate(spec)
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


def check_text(ex):
    answers = [ex.get("answer"), *ex.get("accept", [])]
    if not all(isinstance(a, str) and a.strip() for a in answers):
        return ["answer and accept must be non-empty strings"]
    return []


CHECKERS = {"numeric": check_numeric, "balance": check_balance, "choice": check_choice, "text": check_text}

MAX_LESSON_WORDS = 600

# House rules for lesson.md. Each is (message, test that returns True when broken).
# Add a rule here once a STYLE.md guideline is crisp enough to check by machine.
LESSON_RULES = [
    ("must start with a '# ' title", lambda text: not text.startswith("# ")),
    ("no raw HTML or inline styling; presentation belongs in the templates",
     lambda text: re.search(r"<[a-zA-Z/][^>]*>", text) is not None),
    ("write formulas, charges and arrows plainly (H2O, Na^+, ->); the site typesets them",
     lambda text: re.search(r"[⁰-₟²³¹→⇌]", text) is not None),
    (f"longer than {MAX_LESSON_WORDS} words; split it into two nodes",
     lambda text: len(text.split()) > MAX_LESSON_WORDS),
]


def check_node(path):
    errors = []
    node = tomllib.loads((path / "node.toml").read_text())
    for field in ("title", "summary", "unit", "prerequisites"):
        if field not in node:
            errors.append(f"missing field {field!r}")
    if "unit" in node and node["unit"] not in UNITS:
        errors.append(f"unknown unit {node['unit']!r}; see conventions/units.toml")
    lesson = path / "lesson.md"
    if not lesson.exists() or not lesson.read_text().strip():
        errors.append("missing or empty lesson.md")
    else:
        text = lesson.read_text()
        errors += [f"lesson.md: {message}" for message, broken in LESSON_RULES if broken(text)]
    for i, interactive in enumerate(node.get("interactive", []), 1):
        kind = interactive.get("kind")
        if not kind or not (INTERACTIVES / f"{kind}.js").exists():
            errors.append(f"interactive {i}: unknown kind {kind!r}; see INTERACTIVES.md")
        if not interactive.get("title"):
            errors.append(f"interactive {i}: missing title")
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
        except (KeyError, ValueError, TypeError, SyntaxError, ZeroDivisionError) as e:
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
    failed = 0
    graph = {}
    for path in sorted(p for p in NODES.iterdir() if p.is_dir()):
        try:
            node, errors = check_node(path)
        except (OSError, tomllib.TOMLDecodeError) as e:
            node, errors = {}, [str(e)]
        graph[path.name] = node.get("prerequisites", [])
        if errors:
            failed += 1
            print(f"FAIL {path.name}")
            for e in errors:
                print(f"       {e}")

    if cycle := find_cycle(graph):
        print(f"FAIL prerequisite cycle: {' -> '.join(cycle)}")
        failed += 1

    print(f"{len(graph) - failed} of {len(graph)} nodes pass")
    wanted = sorted({p for prereqs in graph.values() for p in prereqs} - graph.keys())
    if wanted:
        print("\nWanted nodes (referenced as prerequisites, not yet written):")
        for w in wanted:
            print(f"  {w}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
