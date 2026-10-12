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
ELEMENT_KIND = {row[0]: row[2] for row in convention("periodic.toml")["elements"]}


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


def evaluate(expression, names=None):
    """Evaluate arithmetic such as "36.0 / M('H2O')". `names` adds values an
    expression may use, such as earlier steps of a calculation.

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
        if isinstance(node, ast.Name) and node.id in (names or {}):
            return names[node.id]
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
    names = {f"{side}.{el}" for side in ("left", "right") for el in known} | {f"c{i}" for i in range(1, len(species) + 1)}
    errors = []
    for i, step in enumerate(scene["step"], 1):
        coefficients = step.get("coefficients", [])
        if len(coefficients) != len(species) or not all(isinstance(c, int) and 1 <= c <= 6 for c in coefficients):
            errors.append(f"step {i}: needs one coefficient from 1 to 6 for each of {species}")
        if "focus" in step and step["focus"] not in known:
            errors.append(f"step {i}: focus {step['focus']!r} is not an element in this equation")
    if errors:
        return errors, names
    n = len(scene["reactants"])
    totals = [{}, {}]
    for j, (a, c) in enumerate(zip(atoms, scene["step"][-1]["coefficients"])):
        for el, count in a.items():
            totals[j >= n][el] = totals[j >= n].get(el, 0) + count * c
    if totals[0] != totals[1]:
        errors.append(f"the last step is not balanced: {totals[0]} vs {totals[1]}")
    return errors, names


def check_gas_animation(scene):
    """Each step must fix exactly three of pressure, volume, temperature and moles."""
    quantities = ("pressure", "volume", "temperature", "moles")
    limit = scene.get("max_volume")
    errors = [] if isinstance(limit, (int, float)) and limit > 0 else ["needs max_volume, the largest volume shown, in liters"]
    for i, step in enumerate(scene["step"], 1):
        state = {**scene, **step}
        given = {q: state[q] for q in quantities if q in state}
        if len(given) != 3 or not all(isinstance(v, (int, float)) and v > 0 for v in given.values()):
            errors.append(f"step {i}: give exactly three positive values out of {', '.join(quantities)}; the fourth is worked out")
            continue
        volume = given.get("volume") or given["moles"] * CONSTANTS["R"] * given["temperature"] / given["pressure"]
        if not errors and volume > limit:
            errors.append(f"step {i}: the volume is {volume:.3g} L, more than max_volume")
    return errors, {"P", "V", "T", "n", "PV", "VT"}


def check_atom_animation(scene):
    """Atoms up to calcium, with a sensible number of electrons."""
    errors = []
    for i, step in enumerate(scene["step"], 1):
        symbol = step.get("symbol")
        if symbol not in PERIODIC[:20]:
            errors.append(f"step {i}: symbol must be one of the first 20 elements")
            continue
        if not isinstance(step.get("electrons", 1), int) or not 0 <= step.get("electrons", 1) <= 20:
            errors.append(f"step {i}: electrons must be a whole number from 0 to 20")
        if step.get("focus", "valence") != "valence":
            errors.append(f"step {i}: the only focus is \"valence\"")
        mass = step.get("mass_number", atomic_number(symbol))
        if not isinstance(mass, int) or mass < atomic_number(symbol):
            errors.append(f"step {i}: mass_number cannot be less than the number of protons")
    names = {"name", "symbol", "protons", "electrons", "charge", "valence", "levels"}
    return errors, lambda step: names | ({"mass_number", "neutrons"} if "mass_number" in step else set())


def check_decay_animation(scene):
    """Half-lives must be whole numbers that never go backwards."""
    errors = []
    for field in ("isotope", "half_life", "unit"):
        if not scene.get(field):
            errors.append(f"needs {field}")
    passed = [step.get("half_lives") for step in scene["step"]]
    if not all(isinstance(n, int) and 0 <= n <= 6 for n in passed) or passed != sorted(passed):
        errors.append("each step needs half_lives, a whole number from 0 to 6 that does not decrease")
    names = {"half_lives", "elapsed", "fraction", "remaining", "total"} | ({"mass"} if "amount" in scene else set())
    return errors, names


def check_calculation_animation(scene):
    """Every quantity's expression must evaluate, using only the ones before it."""
    errors, values = [], {}
    quantities = scene.get("quantity", [])
    if not 1 <= len(quantities) <= 6:
        errors.append("needs 1 to 6 quantities")
    for q in quantities:
        name = q.get("name", "")
        if not re.fullmatch(r"[a-z]\w*", name) or name in values or name in CONSTANTS or not q.get("label") or "expr" not in q:
            errors.append(f"quantity {name!r}: needs a unique lower-case name, a label and an expr")
            continue
        try:
            values[name] = evaluate(q["expr"], values)
        except (ValueError, SyntaxError, TypeError, KeyError, ZeroDivisionError) as e:
            errors.append(f"quantity {name!r}: {e}")
    shown = [step.get("show") for step in scene["step"]]
    if not all(isinstance(n, int) and 1 <= n <= len(quantities) for n in shown) or shown != sorted(shown):
        errors.append("each step needs show, how many quantities are revealed, never decreasing")
    return errors, set(values)


def check_sort_animation(scene):
    bins, items = scene.get("bins", []), scene.get("items", [])
    errors = [] if 2 <= len(bins) <= 5 and all(isinstance(b, str) for b in bins) else ["needs 2 to 5 bins"]
    if not items or not all(i.get("text") and isinstance(i.get("bin"), int) and 0 <= i["bin"] < len(bins) for i in items):
        errors.append("each item needs text and the index of its bin")
    placed = [step.get("placed") for step in scene["step"]]
    if not all(isinstance(n, int) and 0 <= n <= len(items) for n in placed) or placed != sorted(placed):
        errors.append("each step needs placed, how many items are shown, never decreasing")
    return errors, {"placed", "total"}


def check_sigfigs_animation(scene):
    errors = [f"step {i}: number must be a string of digits such as \"0.0052\""
              for i, step in enumerate(scene["step"], 1) if not re.fullmatch(r"\d+\.?\d*|\.\d+", str(step.get("number", "")))
              or not isinstance(step.get("number"), str)]
    return errors, {"number", "count", "point"}


def check_orbitals_animation(scene):
    errors = [f"step {i}: z must be a whole number from 1 to 36" for i, step in enumerate(scene["step"], 1)
              if not isinstance(step.get("z"), int) or not 1 <= step["z"] <= 36]
    return errors, {"name", "symbol", "z", "config", "last", "valence"}


def check_sizes_animation(scene):
    errors = [f"step {i}: elements must list 2 to 8 of the first 36 elements" for i, step in enumerate(scene["step"], 1)
              if not 2 <= len(step.get("elements", [])) <= 8 or not all(el in PERIODIC for el in step["elements"])]
    return errors, lambda step: {"smallest", "largest"} | {f"{p}.{el}" for p in ("r", "ie", "en") for el in step.get("elements", [])}


def check_ionic_animation(scene):
    """A main-group metal and nonmetal; the last step must be neutral."""
    errors, net = [], None
    for i, step in enumerate(scene["step"], 1):
        metal, nonmetal = step.get("metal"), step.get("nonmetal")
        try:
            ok = ELEMENT_KIND[metal] == "m" and valence(metal) <= 3 and ELEMENT_KIND[nonmetal] == "n" and 5 <= valence(nonmetal) <= 7
        except (KeyError, ValueError):
            ok = False
        counts = [step.get("metals", 1), step.get("nonmetals", 1)]
        if not ok or not all(isinstance(c, int) and 1 <= c <= 4 for c in counts):
            errors.append(f"step {i}: needs a main-group metal, a nonmetal from groups 15 to 17, and 1 to 4 of each")
            continue
        net = valence(metal) * counts[0] - (8 - valence(nonmetal)) * counts[1]
    if not errors and net != 0:
        errors.append("the last step is not neutral")
    return errors, {"formula", "plus", "minus", "metals", "nonmetals", "net", "metal_charge", "nonmetal_charge", "metal", "nonmetal"}


def check_formula_animation(scene):
    errors = []
    for i, step in enumerate(scene["step"], 1):
        parse_formula(step["formula"])
        if not isinstance(step.get("coefficient", 1), int) or not 1 <= step.get("coefficient", 1) <= 4:
            errors.append(f"step {i}: coefficient must be a whole number from 1 to 4")
    return errors, lambda step: {"total", "elements", "mass"} | {f"{p}.{el}" for p in ("count", "each", "prefix") for el in parse_formula(step["formula"])}


def check_energy_animation(scene):
    errors = []
    for i, step in enumerate(scene["step"], 1):
        state = {**scene, **step}
        levels = [state.get(k) for k in ("reactants", "products", "barrier")]
        if not all(isinstance(v, (int, float)) and v >= 0 for v in levels):
            errors.append(f"step {i}: needs reactants, products and barrier, in kJ")
            continue
        barrier = levels[2] * (0.6 if state.get("catalyst") else 1)
        if barrier <= max(0, levels[1] - levels[0]) or levels[0] + levels[2] > 200:
            errors.append(f"step {i}: the barrier must rise above both the reactants and the products, and peak at 200 kJ or less")
    return errors, {"Ea", "dH", "heat", "type", "size"}


def check_equilibrium_animation(scene):
    errors = []
    if not all(isinstance(scene.get(k), (int, float)) and 0 < scene[k] < 1 for k in ("forward", "reverse")) or not scene.get("reactants", 0) > 0:
        errors.append("needs forward and reverse fractions between 0 and 1, and a starting amount of reactants")
    for i, step in enumerate(scene["step"], 1):
        if not isinstance(step.get("rounds"), int) or step["rounds"] < 0 or (step.get("added") and "disturb" not in scene):
            errors.append(f"step {i}: needs rounds; a step with added needs disturb in the scene")
    return errors, {"A", "B", "forward", "reverse"}


def check_ph_animation(scene):
    errors = [f"step {i}: ph must be a number from 0 to 14" for i, step in enumerate(scene["step"], 1)
              if not isinstance(step.get("ph"), (int, float)) or not 0 <= step["ph"] <= 14]
    return errors, {"ph", "H", "OH", "kind"}


ANIMATION_CHECKS = {
    "equation": check_equation_animation,
    "gas": check_gas_animation,
    "atom": check_atom_animation,
    "decay": check_decay_animation,
    "calculation": check_calculation_animation,
    "sort": check_sort_animation,
    "sigfigs": check_sigfigs_animation,
    "orbitals": check_orbitals_animation,
    "sizes": check_sizes_animation,
    "ionic": check_ionic_animation,
    "formula": check_formula_animation,
    "energy": check_energy_animation,
    "equilibrium": check_equilibrium_animation,
    "ph": check_ph_animation,
}


def check_animation(path):
    """An optional animation.toml: a kind, a title and captioned steps. See ANIMATIONS.md."""
    file = path / "animation.toml"
    if not file.exists():
        return []
    scene = tomllib.loads(file.read_text())
    kind = scene.get("kind")
    if kind not in ANIMATION_CHECKS or not (ANIMATIONS / f"{kind}.js").exists():
        return [f"animation: unknown kind {kind!r}; see ANIMATIONS.md"]
    errors = [] if scene.get("title") else ["animation: missing title"]
    steps = scene.get("step", [])
    if not 2 <= len(steps) <= 10:
        errors.append("animation: needs 2 to 10 steps")
    for i, step in enumerate(steps, 1):
        caption = step.get("caption", "")
        if not caption or len(caption) > MAX_CAPTION or "<" in caption:
            errors.append(f"animation step {i}: needs a plain caption of at most {MAX_CAPTION} characters")
    if errors:
        return errors
    try:
        problems, names = ANIMATION_CHECKS[kind](scene)
    except (KeyError, ValueError, TypeError) as e:
        return [f"animation: {e!r}"]
    errors += [f"animation: {problem}" for problem in problems]
    names_for = names if callable(names) else (lambda step: names)
    for i, step in enumerate(steps, 1):
        if problems:
            break
        for name in re.findall(r"\{([\w.]+)\}", step["caption"]):
            if name not in names_for(step):
                errors.append(f"animation step {i}: caption uses {{{name}}}, which a {kind} scene cannot supply")
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
