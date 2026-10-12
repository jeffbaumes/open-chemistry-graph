# Playbook: independent AI review

An AI review is a second opinion from an agent that did not write the part. It is a cheap filter for wrong answer keys, ambiguous questions and factual slips. It does not replace a person. Read `TRUST.md` first.

You may not review anything you wrote or changed in the same pull request. CI rejects it.

## Exercises: solve them blind

1. Print the exercises without their answers:

   ```bash
   python3 tasks.py blind <node-id>
   ```

   **Do not open `node.toml` before you have answered.** The whole value of this review is that your answer is independent.
2. Read the lesson (`nodes/<id>/lesson.md`), then work each exercise as a student would, using only the lesson and `conventions/` for data.
3. Record each one with the answer you reached:

   ```bash
   python3 tasks.py agent-review <node-id> --part exercise-1 --model <your-model-id> --answer 18.02
   ```

   Give a number for numeric exercises, the exact option text for multiple choice, the word or name for text answers, and the coefficients in order (`"2 1 2"`) for balancing.
4. **If the command says your answer disagrees with the key, nothing is recorded. That is the valuable case.** Do not change your answer to match. Work out which is right:
   - If the key is wrong, fix it in a separate pull request.
   - If the question can fairly be read two ways, reword it in a separate pull request.
   - If you were wrong, say nothing and do not record a review of that exercise.
5. Also flag, in the pull request, any exercise you got right but found unclear.

## Lesson text, interactives and videos

1. Read the part closely. Check every factual claim, every number in a worked example, and that each term is explained before it is used.
2. For an interactive, read its source in `src/interactives/kinds/` and check its formulas and data.
3. If you find nothing wrong, record it:

   ```bash
   python3 tasks.py agent-review <node-id> --part lesson --model <your-model-id>
   ```

4. If you find a problem, do not record a review. Open a pull request that fixes it, or an issue that describes it.

## The pull request

- Title starts with the task id, such as `agent-review:molar-mass`.
- At most three lessons per pull request.
- It contains only `reviews.toml` changes. Fixes go in their own pull requests, because a review cannot cover content changed alongside it.
- Say which model you are and list anything you were unsure about.
