# Videos

A lesson can have a short animated video, written as a [Manim](https://www.manim.community) scene. The scene file is the source: it is reviewed like any other code, and the rendered `.mp4` is committed next to the site so the page can play it.

## Adding one

1. Write `videos/<node-id>.py` with a class named `Lesson` that extends `LessonScene`. Start from `videos/balancing-equations.py`.
2. Render it:

   ```bash
   videos/render.sh <node-id>
   ```

   This writes `public/videos/<node-id>.mp4` at 720p.
3. Add `video = true` to the node's `node.toml`. The validator checks that both the scene file and the video exist.

## Setup

```bash
python3 -m venv .venv && .venv/bin/pip install manim
```

No LaTeX or ffmpeg is needed. Text is drawn with Pango, so use `equation()` and `chem()` for formulas, not `MathTex`.

## The toolkit (`videos/lib.py`)

| Call | Does |
|---|---|
| `self.title_card(title)` | Opening card, shown from the first frame |
| `self.enter(*things)` | Fade things in with a soft swoosh |
| `self.caption(text)` | Replace the line of narration at the bottom |
| `self.swoosh()`, `self.chime()` | Play a sound at this moment |
| `self.finish()` | Hold, fade out, and add the background pad |
| `atom(symbol)`, `molecule(formula)` | Atoms and molecules in the element colors |
| `equation(reactants, products)` | A typeset equation; coefficients are highlighted |
| `tally(title, counts, other)` | Atom counts, green where the two sides match |

## Rules

1. **Colors and fonts come from the toolkit.** It reads `src/styles/site.css` and `conventions/elements.toml`, so videos match the pages. Do not hard-code a color.
2. **Sound stays very light.** Use only the synthesized swoosh, chime and pad in the toolkit, at their default levels. No downloaded music, so there is nothing to license.
3. **Everything said is on screen.** There is no voice-over. Captions carry the explanation, so the video works muted.
4. **Under 45 seconds, one idea.** A video shows one worked example in motion. The lesson text does the rest.
5. **Hold each caption long enough to read twice.**
6. **Match the lesson.** Use the same numbers and wording as the worked example it accompanies.
7. **Commit the scene with the video.** A video with no source cannot be reviewed or fixed.

Keep rendered files small. At around 1 MB each a handful is fine in this repository, but a full set for every lesson should move to release assets or a video host.
