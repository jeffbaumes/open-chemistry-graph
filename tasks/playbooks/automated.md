# Playbook: tasks an agent can do alone

For every task here: read `STYLE.md` first, make the smallest change that completes the task, then run `python3 validate.py && npm run build` and confirm the task has left `python3 tasks.py list`.

Changing a lesson or its exercises voids any recorded review of it. That is intended. Say so in the pull request.

## Make an answer recomputable

Task ids start with `derive:`. A numeric exercise has an answer the validator takes on trust.

1. Add a `derive` expression that computes the answer from the numbers in the prompt:

   ```toml
   answer = 30
   unit = "neutrons"
   derive = "56 - 26"
   ```

2. Expressions may use numbers, `+ - * / **`, the constants in `conventions/constants.toml`, and these functions:

   | Function | Gives |
   |---|---|
   | `M('H2O')` | molar mass |
   | `atoms('C6H12O6')` | total atoms in the formula |
   | `count('Al2(SO4)3', 'O')` | atoms of one element |
   | `elements('Mg(OH)2')` | number of different elements |
   | `Z('P')` | atomic number (elements 1 to 36) |
   | `valence('Cl')` | valence electrons (main-group elements) |
   | `sigfigs('0.00420')` | significant figures in a number as written |
   | `log10`, `sqrt`, `min`, `max` | the usual |

3. If the answer disagrees with the expression, find out which is wrong. Do not adjust the expression to match.
4. If the answer is a fact that no expression can produce (the number of electron groups around an atom, say), mark it `recall = true` instead. That removes it from this queue and flags it for extra care in human review.
5. If a whole family of questions needs a function that does not exist, add it to `FUNCTIONS` in `validate.py` and to the table above.

## Add exercises

Task ids start with `exercises:` (fewer than five) or `variety:` (all one type).

- Test the lesson's own idea, not a prerequisite.
- Do not repeat the numbers or substances of the worked example or the interactive.
- Prefer a numeric exercise with a `derive` expression. Use `text` for names and one-word answers, with `accept` for reasonable alternatives. Use `choice` when each wrong option matches a real misconception.
- For `variety`, add a type the lesson does not have yet.
- Put harder exercises last.

## Write a lesson

Task ids start with `wanted:` or `lesson:`.

1. Create `nodes/<id>/lesson.md` and `nodes/<id>/node.toml`. Copy the shape of a nearby lesson.
2. Set `unit` to an id from `conventions/units.toml` and list the real prerequisites. Check the lesson lands in a sensible place on the contents page.
3. Include a worked example (`## Worked example: ...`) and a common mistake (`## Common mistake`).
4. Write five exercises of at least two types.
5. Keep it under 600 words. If it will not fit, it is two lessons.
6. For a `lesson:` task, delete its entry from `tasks/backlog.toml` in the same pull request.

A new lesson starts unreviewed, which adds a `review:` task for it. That is expected.

## Add an interactive or an animation

Task ids start with `interactive:` or `animation:`. These are optional: skip the task if the idea does not involve a quantity changing or steps worth seeing in motion. Follow `INTERACTIVES.md` or `ANIMATIONS.md`.

## Tooling

Task ids start with `tooling:`. The detail line describes the goal. Keep the change small, add nothing the task does not need, and delete the entry from `tasks/backlog.toml` in the same pull request.
