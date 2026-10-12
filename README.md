# Open chemistry graph

An open high school chemistry course built as a graph of small lessons, written by people and their AI assistants, and checked by machine. It currently has 49 lessons in 12 units, with 17 kinds of interactive model.

## How it works

Each folder in `nodes/` is one concept:

- `lesson.md` — a short explanation with a worked example and a common mistake
- `node.toml` — title, summary, unit, prerequisites, any interactives, and exercises with machine-checkable answers
- `animation.toml` — optionally, a step-through animation written as data and played in the browser

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
| Physical constants | `conventions/constants.toml` | CI |
| Units of the course and their order | `conventions/units.toml` | CI and templates |
| How interactives look and behave | `INTERACTIVES.md`, `src/interactives/lib.js`, `src/styles/interactive.css` | shared toolkit |
| How animations are written and played | `ANIMATIONS.md`, `src/animations/` | CI and shared player |
| How molecules are drawn | `conventions/molecules.toml` | templates |
| Who is trusted, and what a review is | `TRUST.md`, `conventions/reviewers.toml`, `ci/review_guard.py` | CI guard |
| Tone, level, pedagogy | `STYLE.md` | reviewers |

Rules are contributions too. Changing one must update every node it affects in the same pull request.

The validator recomputes chemistry where it can. A numeric exercise may declare how its answer is derived, as an arithmetic expression, and the stated answer must match:

```toml
[[exercise]]
type = "numeric"
prompt = "How many moles are in 36.0 g of H2O?"
answer = 2.0
unit = "mol"
derive = "36.0 / M('H2O')"
```

Expressions may use numbers, `+ - * / **`, `M(formula)` for molar mass, `log10`, `sqrt`, `min`, `max`, and the constants in `conventions/constants.toml`. Balancing exercises are checked for atom conservation and lowest terms.

## Task queue

Open tasks are computed from the repository itself, so the list is never stale:

```bash
python3 tasks.py
```

Each task is either for an AI agent alone or for an agent guiding a person. Agents start from [AGENTS.md](AGENTS.md); the same queue is published on the site's Contribute page.

## Trust

Every part of every lesson (the text, each exercise, each interactive, the animation) shows how many people and how many independent AI runs have reviewed that exact version, and whether CI recomputes its answer. Reviews are small records in `nodes/<id>/reviews.toml`. A review stops counting when its part changes, its author is checked against the pull request's GitHub account, and a human review counts only from someone on the reviewer list. [TRUST.md](TRUST.md) explains the rules and what they do not prove.

## Contributing

1. Pick a task with `python3 tasks.py`, or improve any lesson you know well.
2. Add `nodes/<id>/lesson.md` and `nodes/<id>/node.toml` with at least 3 exercises. Follow `STYLE.md`.
3. Prefer exercises the validator can recompute. If it cannot check your kind of problem yet, adding a new `derive` kind or exercise type to `validate.py` is a welcome contribution.
4. Make sure the validator passes, then open a pull request.

## Exercise types

| Type | Answer | Checked by |
|---|---|---|
| `numeric` | number + unit | recomputed when `derive` is given |
| `balance` | coefficients per side | atom conservation, lowest terms |
| `choice` | index of the correct option | structure only |
| `text` | a word or name, with optional `accept` alternatives | structure only |
