# Open chemistry graph

An open chemistry curriculum built as a graph of small lessons, written by people and their AI assistants, and checked by machine.

## How it works

Each folder in `nodes/` is one concept:

- `lesson.md` — a short explanation with a worked example and a common mistake
- `node.toml` — title, summary, prerequisites, and exercises with machine-checkable answers

Run the checks, then the site:

```bash
python3 validate.py
```

```bash
npm install && npm run dev
```

Pushing to `main` validates, builds and publishes the site to GitHub Pages.

## Where the rules live

| Rule | Lives in | Enforced by |
|---|---|---|
| Chemistry is correct | `validate.py` | CI |
| Lesson format | `LESSON_RULES` in `validate.py` | CI |
| Atomic masses, element colors | `conventions/elements.toml` | CI and templates |
| Formula typesetting, example boxes | `src/lib/chem.js`, `src/lib/rehype-lesson.js` | templates |
| Page look and layout | `src/styles/site.css`, `src/` | templates |
| Tone, level, pedagogy | `STYLE.md` | reviewers |

Rules are contributions too. Changing one must update every node it affects in the same pull request.

The validator recomputes chemistry where it can. A numeric exercise may declare how its answer is derived (`derive = { kind = "molar_mass", formula = "H2O" }`) and the stated answer must match. Balancing exercises are checked for atom conservation and lowest terms.

## Contributing

1. Run `python3 validate.py` and pick a node from the "Wanted nodes" list, or improve an existing one.
2. Add `nodes/<id>/lesson.md` and `nodes/<id>/node.toml` with at least 3 exercises.
3. Prefer exercises the validator can recompute. If it cannot check your kind of problem yet, adding a new `derive` kind or exercise type to `validate.py` is a welcome contribution.
4. Make sure the validator passes, then open a pull request.

## Exercise types

| Type | Answer | Checked by |
|---|---|---|
| `numeric` | number + unit | recomputed when `derive` is given |
| `balance` | coefficients per side | atom conservation, lowest terms |
| `choice` | index of the correct option | structure only |
