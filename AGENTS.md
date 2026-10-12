# Instructions for AI agents

This repository is an open high school chemistry course. People donate their AI's time to improve it. If you are an agent that has been asked to help, this file tells you how.

## Find a task

```bash
python3 tasks.py
```

That prints the open tasks, computed from the current state of the repository. Each has an id such as `review:molar-mass` and a mode:

- **ai**: you can finish it alone. The validator decides whether your work is acceptable.
- **human**: a person must take part. Your job is to guide them through it, one step at a time.

```bash
python3 tasks.py list --mode ai          # tasks you can do alone
python3 tasks.py list --mode human       # tasks to do with the person you are working with
python3 tasks.py show <task-id>          # details, files and the playbook to follow
```

If the person you are working with knows chemistry, prefer a `review` task. Human review is the scarcest thing this project has.

Read `TRUST.md` before any review task. It explains what a review record is and what CI will reject.

## Do the task

1. **Check nobody else has it.** `gh pr list --search "<task-id> in:title"`. If a pull request exists, pick another task.
2. **Claim it.** Branch, and open a draft pull request whose title starts with the task id.
3. **Follow the playbook** that `tasks.py show` names. Read `STYLE.md` before writing any lesson text.
4. **One task per pull request.** Small changes get reviewed; large ones do not.
5. **Check your work.**

   ```bash
   python3 validate.py && npm run build
   ```

6. **Confirm the task is gone** from `python3 tasks.py list`, then mark the pull request ready.

## Rules

- **Never record a human review on your own.** `python3 tasks.py review` states that a person checked a lesson. Run it only when a person has gone through it with you and said, in their own words, that they approve it. One lesson per pull request.
- **Never review your own work.** `python3 tasks.py agent-review` is for parts you did not write or change. Solve exercises with `python3 tasks.py blind <id>` before looking at any answer, and if you disagree with a key, report it instead of recording a review.
- **Do not touch the trust files** unless your task is about them and a maintainer asked: `.github/`, `ci/`, `validate.py`, `tasks.py`, `conventions/reviewers.toml`. CI rejects such changes from anyone who is not a maintainer.
- **Never loosen a check to make your work pass.** If the validator rejects a correct answer, fix the validator in its own pull request and explain why.
- **Do not guess at chemistry.** Give every numeric exercise a `derive` expression so its answer is recomputed. If you are unsure whether a statement is true, leave it out or flag it in the pull request.
- **Do not rewrite what works.** Rephrasing a correct lesson is not a task. Change text only to fix an error, fill a gap, or respond to a reviewer.
- **Write chemistry plainly** (`H2O`, `Na^+`, `->`) and never put styling in a lesson. The site typesets it.
- **Say what you did not check.** In the pull request, list anything a person should look at.

## Where things are

| Path | What |
|---|---|
| `nodes/<id>/lesson.md`, `node.toml` | One lesson and its exercises |
| `nodes/<id>/reviews.toml` | Review records for each part, void when that part changes |
| `conventions/` | Element data, constants and course units, shared by everything |
| `validate.py` | The gate: structure, house rules, recomputed answers |
| `tasks.py`, `tasks/backlog.toml` | The task queue |
| `TRUST.md`, `ci/`, `conventions/reviewers.toml` | How reviews are recorded, checked and trusted |
| `tasks/playbooks/` | How to do each kind of task |
| `STYLE.md`, `INTERACTIVES.md`, `videos/README.md` | The guides for lessons, interactives and videos |
| `src/` | The Astro site |
