# Playbook: review a lesson with a person

A review is a person who knows chemistry reading one lesson closely, solving its exercises, and signing off. You, the agent, run the session. The person supplies the judgment.

This is the most valuable task in the project. Everything else was written by AI, and nothing else can vouch for it.

## Before you start

1. Ask what the person teaches or knows well, and pick a `review` task in that area: `python3 tasks.py list --kind review`.
2. Check they are signed in to GitHub as themselves (`gh api user -q .login`). The review is recorded under that account, and CI checks it.
3. Tell them what to expect: one lesson, about ten minutes, and they can stop at any point.
4. Open the lesson's page for them if you can (`npm run dev`, then `/<node-id>/`), so they see it as a student would.

## How to run the session

Go in this order. **Show one piece, ask, and wait for the answer before moving on.**

1. **The explanation.** Show the text before the first worked example. Ask:
   - Is anything here wrong, or true only with a caveat that is missing?
   - Is it pitched right for a student meeting this for the first time?
   - Is a term used before it is explained?
2. **Each worked example.** Ask them to check the numbers and the steps. Ask whether this is the example they would choose.
3. **The common mistake.** Ask whether students really make this mistake, and whether a more common one is missing.
4. **Each exercise, one at a time.** Show the question **without the answer**. Ask the person to solve it. Then compare with the key.
   - If they disagree with the key, stop and work out which is right. Do not defend the key.
   - Ask whether the wording could be read another way.
   - For multiple choice, ask whether each wrong option is a mistake a student would actually make.
   - Exercises marked `recall = true` have no computed check at all. Take extra care with them.
5. **The interactive and video**, if the lesson has them. Ask whether they show the idea correctly and whether anything is misleading.
6. **What is missing.** Ask what they would add if this were their own handout.

## How to ask

- **Ask before you tell.** "What do you make of this step?" finds problems. "This looks right, agreed?" hides them.
- **Never show an answer key before the person has answered.**
- **Do not argue for the existing text.** You may explain why it says what it says, once, if asked.
- **Write down every objection**, including ones the person talks themselves out of. They go in the pull request.
- **If the person is unsure**, record it as unsure. Do not turn it into approval.

## Making changes

- Make each edit as it comes up and show the person the new text.
- Follow `STYLE.md`. Give any new numeric exercise a `derive` expression.
- Run `python3 validate.py` after editing.

## Signing off

A lesson has parts: the lesson text, each exercise, each interactive and the video. The person signs off on the parts they are satisfied with. It does not have to be all of them.

Ask plainly, part by part or for the whole lesson: **"Are you satisfied that this is correct and suitable for students?"**

Only for what they say yes to, in their own words, record it:

```bash
python3 tasks.py review <node-id>                                  # every part
python3 tasks.py review <node-id> --part lesson --part exercise-2  # only some
```

Run this last, after every edit, because changing a part voids its reviews. Check the result with `python3 tasks.py status <node-id>`.

The command reads the person's GitHub login from `gh`. Two things must be true or CI rejects the pull request (see `TRUST.md`):

- **The person is on the reviewer list** in `conventions/reviewers.toml`. If they are not, open the pull request with the fixes only, and ask a maintainer to add them. They can record the review afterwards.
- **The pull request is opened from the person's own GitHub account.** A review signed by one account and submitted by another is rejected.

Do not record a review if:

- the person skipped the exercises or did not solve them,
- they said "approve everything" or asked to sign off several lessons at once (CI allows one lesson per pull request),
- they have open doubts about that part. Leave it unrecorded and describe the doubt in the pull request.

## The pull request

Title: `review:<node-id>: <one line>`. In the body:

- who reviewed, and what they teach or know,
- each change and why,
- objections raised and how each was settled,
- anything they were unsure about.

It must be opened from the person's own GitHub account.
