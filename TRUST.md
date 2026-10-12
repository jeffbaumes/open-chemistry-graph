# Trust

Almost everything here was written by AI. This page explains how a reader can tell what has been checked, by whom, and how far to believe it.

## What the site shows

Every lesson is split into **parts**: the lesson text, each exercise, each interactive and the video. Each part shows three things.

| Signal | Means | How far to trust it |
|---|---|---|
| **Answer recomputed** | CI recalculates this exercise's answer from a formula on every change | Fully verified. No person or AI is taken at their word. |
| **Human reviews** | How many listed reviewers have signed off on this exact version | Accountable, not provable. See below. |
| **AI reviews** | How many independent AI runs have checked this exact version | Weak on its own. A second opinion, not a guarantee. |

The contents page shows, for each lesson, how many of its parts have at least one human review.

## Where reviews live

In the repository, as `nodes/<id>/reviews.toml`. There is no other database. A record is deliberately small:

```toml
[[review]]
part = "exercise-3"
fingerprint = "1c521f17e665"
by = "some-github-login"
```

An AI review also has `model`, and for an exercise the `answer` it worked out.

Nothing else is recorded, because anything else would have to be taken on trust. In particular there is no date, no "I am a teacher" field and no "I checked carefully" field.

## What makes a record count

**It names a fingerprint, not a file.** The fingerprint is a hash of the part's content. Change one word of an exercise and every review of it stops counting, with no one having to remember to reset anything.

**Its author is checked, not claimed.** CI compares `by` with the GitHub account that opened the pull request. You cannot record a review in someone else's name.

**A human review needs a listed reviewer.** `conventions/reviewers.toml` names the people whose reviews count. A maintainer adds someone when they have reason to believe that person is real and knows the chemistry. Remove a name and everything that person signed stops counting at the next build.

**The rules are read from the main branch.** The guard that judges a pull request runs from the target branch, not from the pull request. So a pull request cannot add its own author to the reviewer list, weaken a check, or edit the guard to let itself through.

## What CI enforces

`ci/review_guard.py` runs on every pull request and rejects it if:

- a review is signed by anyone other than the pull request's author
- a human review comes from someone not on the reviewer list
- a review does not match the current content of any part
- an existing review of unchanged content is removed or altered
- an AI review covers a part that the same pull request changed
- an AI review of an exercise lacks its worked answer, or the answer disagrees with the key
- one pull request records human reviews in more than one lesson, or AI reviews in more than three
- someone who is not a maintainer changes the checks, the workflows or the reviewer list

`ci/test_review_guard.py` tests each of these rules and runs in CI too.

## What this does not prove

- **That a listed reviewer really read the lesson.** No system can. What the design gives instead is accountability: every review is tied to a named account that a maintainer chose to trust, limited to one lesson per pull request, and revocable in one line.
- **That an AI review was independent.** An agent is asked to solve each exercise without seeing the key (`python3 tasks.py blind <id>`), but nothing stops it from reading the file. The requirement to state its own answer catches careless runs, not dishonest ones. Treat AI reviews as a filter that catches some errors cheaply.
- **Anything about direct pushes.** Maintainers can push to the main branch without the guard. Until branch protection requires pull requests and the guard to pass, the rules bind everyone except maintainers.

## Turning it up

In order of how much each adds:

1. **Protect the main branch**: require pull requests, the `guard` and `build` checks, and code-owner review. This makes the rules binding instead of advisory.
2. **Require two human reviews** before the site calls a part reviewed.
3. **Run AI reviews in CI** with a project key, so the review is performed by the project's own runner and not reported by a contributor.
4. **Use classroom results**: exercises that many real students miss are flagged regardless of who reviewed them.
