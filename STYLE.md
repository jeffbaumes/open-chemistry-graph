# Style guide

These are the rules a machine cannot check yet. Reviewers, human or AI, enforce them. When one becomes precise enough to test, move it into `LESSON_RULES` in `validate.py` and delete it here.

Any rule can be changed. A change to a rule must update every existing node in the same pull request, so the repository always passes its own rules.

## Audience

- High school students meeting the topic for the first time.
- Define a term the first time it appears, or link the node that teaches it as a prerequisite.

## Lessons

- One concept per node. If a lesson needs two worked examples of different kinds, it is two nodes.
- Include at least one worked example, with every step shown.
- Name one common mistake and show why it is wrong.
- Say what a model leaves out when using a simplified one (for example, the octet rule).

## Presentation

- Lessons describe chemistry, never appearance. Do not name colors, fonts or layout in a lesson; element data lives in `conventions/elements.toml` and everything else in `src/styles/site.css`.
- Write chemistry plainly and let the site typeset it, so every page looks the same:
  - formulas: `H2O`, `Ca(OH)2`
  - charges and exponents with `^`: `Na^+`, `SO4^2-`, `10^-7`, `1s^2`, `cm^3`
  - variable subscripts with `_`: `V_1`, `E_a`
  - arrows: `->` for a reaction, `<->` for equilibrium
- Title a section `## Worked example: ...` or `## Common mistake` to get the matching box. A paragraph that is only a bold line is displayed as a centered result.
- Use the atomic masses in `conventions/elements.toml`, so worked examples match the exercises.

## Interactives

- Add one when changing a quantity and watching the result teaches the idea better than a paragraph. See `INTERACTIVES.md`.
- Use a different example from the node's own exercises.

## Exercises

- Prefer exercises the validator can recompute.
- Each exercise tests the node's own concept, not a prerequisite.
- A wrong multiple-choice option should correspond to a real misconception.
