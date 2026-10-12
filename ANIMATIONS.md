# Animations

An animation is a short, captioned sequence a student steps through with Previous, Next and Restart, at their own pace. It is not a video file. It is a small data file, `nodes/<id>/animation.toml`, that the page plays live.

Checking in the description instead of a rendering means:

- **It can be reviewed.** A change is a readable diff of steps and captions.
- **It can be checked.** CI reads the steps and tests the chemistry in them.
- **It cannot state a wrong count.** Numbers on screen are worked out from what is drawn.
- **It is accessible.** Captions are real text, the steps are listed for screen readers and print, and it respects the reduced-motion setting.
- **It weighs nothing.** No rendering step, no media files, and it follows the site's colors and dark mode.

## Writing one

A scene names a **kind**, gives the kind's settings, then lists **steps**. Each step is a state plus a caption. You do not describe the motion: the player compares each step with the one before, moves what stayed, fades in what is new and fades out what is gone.

```toml
kind = "equation"
title = "Balancing by adding coefficients"
reactants = ["H2", "O2"]
products = ["H2O"]

[[step]]
coefficients = [1, 1, 1]
caption = "Count the atoms of each element on both sides."

[[step]]
coefficients = [1, 1, 2]
focus = "O"
caption = "Two water molecules. Oxygen now matches: {left.O} and {right.O}."
```

Captions follow the same plain-chemistry rules as lessons (`H2O`, `Na^+`, `->`).

Steps can also be written compactly, one per line:

```toml
step = [
  { coefficients = [1, 1, 1], caption = "Count the atoms of each element on both sides." },
  { coefficients = [1, 1, 2], focus = "O", caption = "Oxygen now matches: {left.O} and {right.O}." },
]
```

## Kinds

### `equation`

A chemical equation drawn as molecules, with a table of atom counts.

| Setting | Where | Meaning |
|---|---|---|
| `reactants`, `products` | scene | Lists of formulas. They never change during the scene. |
| `coefficients` | step | One whole number from 1 to 6 for each formula, reactants first |
| `focus` | step, optional | An element to highlight; the others fade |

Captions can use `{left.X}` and `{right.X}` for the number of atoms of element X on each side, and `{c1}`, `{c2}`, ... for the coefficients in order. Use these for every count, so a caption can never disagree with the picture.

CI checks that every formula is valid, that only coefficients change (a scene cannot alter a subscript), and that **the last step is balanced**.

Molecules are drawn from `conventions/molecules.toml`. A formula without a layout there is drawn as a row of atoms.

### `gas`

A gas in a cylinder under a piston, obeying P × V = n × R × T.

| Setting | Where | Meaning |
|---|---|---|
| `pressure` (atm), `volume` (L), `temperature` (K), `moles` | scene or step | Give exactly three in total; the fourth is worked out |
| `max_volume` | scene | The largest volume shown, in liters, which sets the scale |

Put what stays constant in the scene and what changes in the steps. Captions can use `{P}`, `{V}`, `{T}`, `{n}`, `{PV}` and `{VT}` (V ÷ T).

### `atom`

One atom or ion: a nucleus with electrons in shells. Works for the first 20 elements.

| Setting | Where | Meaning |
|---|---|---|
| `symbol` | step | The element |
| `electrons` | step, optional | For an ion. Leave out for a neutral atom |
| `mass_number` | step, optional | For an isotope; adds the neutron count |
| `focus = "valence"` | step, optional | Fade everything but the outer level |

Captions can use `{name}`, `{symbol}`, `{protons}`, `{electrons}`, `{charge}`, `{valence}` (electrons in the outer level), `{levels}` and, with a mass number, `{neutrons}`.

### `decay`

A radioactive sample as 64 atoms, half of the remainder fading each half-life.

| Setting | Where | Meaning |
|---|---|---|
| `isotope`, `half_life`, `unit` | scene | Such as `"Iodine-131"`, `8`, `"days"` |
| `amount` | scene, optional | Starting mass in grams |
| `half_lives` | step | Whole number of half-lives passed, never decreasing |

Captions can use `{elapsed}`, `{fraction}`, `{remaining}`, `{total}`, `{half_lives}` and, if `amount` is set, `{mass}`.

### `calculation`

A worked calculation, revealed one quantity at a time as a chain of boxes, with the working shown underneath.

| Setting | Where | Meaning |
|---|---|---|
| `quantity` | scene | Up to 6 of `{ name, label, expr, unit }`, plus optional `sig` (significant figures, default 3) and `signed` (show a + sign) |
| `show` | step | How many quantities are revealed |

`expr` is arithmetic that may use the names of earlier quantities, the constants in `conventions/constants.toml`, and the same functions as an exercise's `derive` (`M`, `valence`, `Z`, `log10`, `sqrt`, `min`, `max`). A plain number is a given value and is shown as typed. Everything else, including the written-out working, is computed. Captions use `{name}` for any quantity.

### `sort`

Examples placed into named groups.

| Setting | Where | Meaning |
|---|---|---|
| `bins` | scene | 2 to 5 group names |
| `items` | scene | `{ text, bin }` for each example, where `bin` is the index of its group |
| `placed` | step | How many items are shown, in the order listed |

Nothing here is computed, so the groupings rest on review alone.

### `formula`

One formula drawn as atoms, with a count of each element.

| Setting | Where | Meaning |
|---|---|---|
| `formula` | step | The formula |
| `coefficient` | step, optional | 1 to 4 copies |

Captions can use `{count.X}` (atoms of X in all), `{each.X}` (in one formula), `{prefix.X}` (mono, di, tri, ...), `{total}`, `{elements}` and `{mass}`.

### `ionic`

Ions of a metal and a nonmetal with their charges added up. Charges come from each element's group.

| Setting | Where | Meaning |
|---|---|---|
| `metal`, `nonmetal` | step | A metal from groups 1, 2 or 13 and a nonmetal from groups 15 to 17 |
| `metals`, `nonmetals` | step, optional | 1 to 4 of each (default 1) |

Captions can use `{formula}`, `{plus}`, `{minus}`, `{net}`, `{metal_charge}`, `{nonmetal_charge}`, `{metal}` and `{nonmetal}`. CI requires the last step to be neutral.

### `orbitals`

Orbital boxes filling in order. Step: `z` (1 to 36). Captions can use `{name}`, `{symbol}`, `{z}`, `{config}`, `{last}` and `{valence}`.

### `sizes`

Atoms side by side, drawn to scale by atomic radius. Step: `elements`, a list of 2 to 8 symbols. Captions can use `{r.X}` (radius), `{ie.X}` (ionization energy), `{en.X}` (electronegativity), `{largest}` and `{smallest}`.

### `sigfigs`

A number with its significant digits picked out. Step: `number`, as a string so trailing zeros are kept. Captions can use `{number}` and `{count}`.

### `energy`

An energy curve from reactants over a barrier to products.

| Setting | Where | Meaning |
|---|---|---|
| `reactants`, `products`, `barrier` | scene or step | Energies in kJ |
| `catalyst` | step, optional | `true` lowers the barrier to 60% |

Captions can use `{Ea}`, `{dH}`, `{heat}` (released or absorbed), `{type}` and `{size}`.

### `equilibrium`

A reversible reaction settling down, as two bars with the forward and reverse rates. The amounts are simulated.

| Setting | Where | Meaning |
|---|---|---|
| `forward`, `reverse` | scene | Fraction converted each round, between 0 and 1 |
| `reactants`, `products` | scene | Starting amounts |
| `disturb` | scene, optional | Extra reactant that a step can add |
| `rounds` | step | Rounds run so far |
| `added`, `more` | step, optional | Add the disturbance, then run `more` rounds |

Captions can use `{A}`, `{B}`, `{forward}` and `{reverse}`.

### `ph`

A marker on the pH scale. Step: `ph` (0 to 14). Captions can use `{H}`, `{OH}`, `{kind}` and `{ph}`.

## Rules

1. **One idea, about four steps.** CI allows at most ten.
2. **Every step has a caption** of at most 160 characters, and the captions alone tell the story.
3. **Never type a number the kind can supply.** Use the placeholders.
4. **Match the lesson.** Use the same example as the worked example it sits beside.
5. **No styling or timing in the scene.** The player decides those, so every animation feels the same.
6. **Animations are silent.** The player has no audio. Do not add any.

## Writing a new kind

Create `src/animations/kinds/<name>.js`. A kind is one pure function from a step's state to a picture:

```js
export default {
  render(state, ui) {
    return {
      header: '...',   // HTML shown above the drawing
      sprites: [       // what is drawn; the 640 by 240 stage
        { id: 'a', type: 'atom', symbol: 'O', x: 100, y: 120, r: 12, dim: false },
        { id: 'plus', type: 'text', text: '+', x: 160, y: 120, size: 26 },
      ],
      footer: '...',   // HTML shown below the drawing
      vars: { total: 4 },  // values captions may use as {total}
    };
  },
};
```

Sprite types:

| Type | Draws | Fields besides `id`, `x`, `y`, `dim` |
|---|---|---|
| `atom` | A labelled circle in the element's color | `symbol`, `r`, optional `label` |
| `dot` | A small filled circle | `r`, optional `class` |
| `ring` | An outlined circle | `r` |
| `rect` | A rectangle from its top-left corner | `w`, `h`, `class` |
| `text` | A symbol or short label | `text`, `size`, optional `class` |
| `curve` | An energy curve | `a`, `b`, `c`: the y positions of its start, peak and end |

`dim` fades a sprite to draw attention elsewhere. Positions, sizes and fading are all animated between steps.

The drawing is 640 units wide and shrinks to about half that on a phone, so keep text in it large (20 units or more) and short. Anything wordy belongs in `header` or `footer`, which are ordinary HTML and wrap. Give an HTML element a `data-key` and it fades in on the step where it first appears. A kind may return no sprites at all; the drawing is then hidden.

- **Give every sprite a stable `id`.** The same thing must keep the same id from step to step, or it will fade out and in instead of moving.
- **Derive, do not accept.** Take the smallest possible state and compute counts, labels and positions from it.
- **Stay pure.** No DOM access, timers or randomness: the same function runs at build time to produce the text version of the scene.
- `ui` provides `chem(text)`, `parseFormula(formula)` and `colorOf(symbol)`. Use the classes in `src/styles/interactive.css` for any HTML.
- Add a check for the kind to `ANIMATION_CHECKS` in `validate.py`. It returns the problems it finds and the names captions may use. A kind without a check is rejected.
- Add a section to this file.
