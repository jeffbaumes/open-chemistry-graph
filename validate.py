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
sys.path.insert(0, str(ROOT / "ci"))
import trust  # noqa: E402

NODES = ROOT / "nodes"
CONVENTIONS = ROOT / "conventions"
INTERACTIVES = ROOT / "src" / "interactives" / "kinds"
ANIMATIONS = ROOT / "src" / "animations" / "kinds"
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
PERIODIC = [row[0] for row in convention("periodic.toml")["elements"]]


def atomic_number(symbol):
    return PERIODIC.index(symbol) + 1


def valence(symbol):
    """Valence electrons of a main-group element in periods 1 to 4."""
    z = atomic_number(symbol)
    if z <= 2:
        return z
    if z <= 18:
        return z - 2 if z <= 10 else z - 10
    group = z - 18
    if 3 <= group <= 12:
        raise ValueError(f"valence() does not cover transition metals such as {symbol}")
    return group if group <= 2 else group - 10


def sigfigs(text):
    """Significant figures in a number as written, such as '0.00420'."""
    digits = text.lstrip("+-").replace(".", "").lstrip("0")
    return len(digits) if "." in text else len(digits.rstrip("0"))


FUNCTIONS = {
    "M": molar_mass, "log10": math.log10, "sqrt": math.sqrt, "min": min, "max": max,
    "atoms": lambda formula: sum(parse_formula(formula).values()),
    "count": lambda formula, element: parse_formula(formula).get(element, 0),
    "elements": lambda formula: len(parse_formula(formula)),
    "Z": atomic_number, "valence": valence, "sigfigs": sigfigs,
}


def evaluate(expression):
    """Evaluate arithmetic such as "36.0 / M('H2O')".

    Allows numbers, + - * / **, the constants in conventions/constants.toml,
    and the functions in FUNCTIONS. Nothing else.
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


MAX_CAPTION = 160


def check_equation_animation(scene):
    """An equation animation may only change coefficients, and must end balanced."""
    species = scene["reactants"] + scene["products"]
    atoms = [parse_formula(f) for f in species]
    known = {el for a in atoms for el in a}
    errors = []
    for i, step in enumerate(scene["step"], 1):
        coefficients = step.get("coefficients", [])
        if len(coefficients) != len(species) or not all(isinstance(c, int) and 1 <= c <= 6 for c in coefficients):
            errors.append(f"step {i}: needs one coefficient from 1 to 6 for each of {species}")
            continue
        if "focus" in step and step["focus"] not in known:
            errors.append(f"step {i}: focus {step['focus']!r} is not an element in this equation")
        for side, el in re.findall(r"\{(\w+)\.(\w+)\}", step.get("caption", "")):
            if side not in ("left", "right") or el not in known:
                errors.append(f"step {i}: caption uses {{{side}.{el}}}, which this equation cannot supply")
    if errors:
        return errors
    last = scene["step"][-1]["coefficients"]
    n = len(scene["reactants"])
    totals = [{}, {}]
    for j, (a, c) in enumerate(zip(atoms, last)):
        for el, count in a.items():
            totals[j >= n][el] = totals[j >= n].get(el, 0) + count * c
    if totals[0] != totals[1]:
        errors.append(f"the last step is not balanced: {totals[0]} vs {totals[1]}")
    return errors


ANIMATION_CHECKS = {"equation": check_equation_animation}


def check_animation(path):
    """An optional animation.toml: a kind, a title and captioned steps. See ANIMATIONS.md."""
    file = path / "animation.toml"
    if not file.exists():
        return []
    scene = tomllib.loads(file.read_text())
    kind = scene.get("kind")
    if not kind or not (ANIMATIONS / f"{kind}.js").exists():
        return [f"animation: unknown kind {kind!r}; see ANIMATIONS.md"]
    errors = [] if scene.get("title") else ["animation: missing title"]
    steps = scene.get("step", [])
    if len(steps) < 2:
        errors.append("animation: needs at least 2 steps")
    for i, step in enumerate(steps, 1):
        caption = step.get("caption", "")
        if not caption or len(caption) > MAX_CAPTION or "<" in caption:
            errors.append(f"animation step {i}: needs a plain caption of at most {MAX_CAPTION} characters")
    if not errors and kind in ANIMATION_CHECKS:
        try:
            errors += [f"animation: {e}" for e in ANIMATION_CHECKS[kind](scene)]
        except (KeyError, ValueError, TypeError) as e:
            errors.append(f"animation: {e!r}")
    return errors


def check_reviews(nid):
    """Review records must be well formed. Who may add them is the CI guard's job."""
    errors = []
    approved = trust.people(ROOT)["reviewers"]
    seen = set()
    for i, record in enumerate(trust.records(ROOT, nid), 1):
        allowed = {"part", "fingerprint", "by"} | ({"model", "answer"} if trust.is_agent(record) else set())
        if not all(isinstance(record.get(k), str) and record[k] for k in ("part", "fingerprint", "by")):
            errors.append(f"reviews.toml record {i}: needs part, fingerprint and by")
            continue
        if extra := set(record) - allowed:
            errors.append(f"reviews.toml record {i}: unexpected field {sorted(extra)[0]!r}; records hold only what CI can check")
        if not trust.is_agent(record) and record["by"].lower() not in approved:
            errors.append(f"reviews.toml record {i}: {record['by']} is not on the reviewer list, so this is not a human review")
        if trust.identity(record) in seen:
            errors.append(f"reviews.toml record {i}: duplicate review")
        seen.add(trust.identity(record))
    return errors


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
    errors += check_animation(path)
    for i, interactive in enumerate(node.get("interactive", []), 1):
        kind = interactive.get("kind")
        if not kind or not (INTERACTIVES / f"{kind}.js").exists():
            errors.append(f"interactive {i}: unknown kind {kind!r}; see INTERACTIVES.md")
        if not interactive.get("title"):
            errors.append(f"interactive {i}: missing title")
    errors += check_reviews(path.name)
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

    for unit in convention("units.toml")["unit"]:
        lessons = unit.get("lessons", [])
        for i, nid in enumerate(lessons):
            if nid not in graph:
                print(f"FAIL units.toml: {unit['id']} lists {nid!r}, which does not exist")
                failed += 1
            elif late := [p for p in graph[nid] if p in lessons[i + 1:]]:
                print(f"FAIL units.toml: {unit['id']} lists {nid!r} before its prerequisite {late[0]!r}")
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
