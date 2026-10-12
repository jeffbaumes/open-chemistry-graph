# Interactives

An interactive is a small model a student can change and watch respond: build an atom, squeeze a gas, balance an equation. Each one is a single file in `src/interactives/kinds/`, built from a shared toolkit so they all look and behave the same.

## Using one in a lesson

Add a block to the node's `node.toml`. It appears between the lesson and the practice problems.

```toml
[[interactive]]
kind = "gas-law"
title = "Squeeze a gas"
caption = "Change the volume and watch the pressure."
params = { mode = "boyle" }
```

| Kind | Shows | Params |
|---|---|---|
| `atom-builder` | Protons, neutrons, electrons and the resulting atom or ion | `protons`, `neutrons`, `electrons` |
| `bond-type` | Electronegativity difference and bond type for two elements | `a`, `b` (symbols) |
| `density` | A block that floats or sinks as mass and volume change | `mass`, `volume` |
| `electron-config` | Orbital filling for elements 1 to 36 | `z` |
| `energy-diagram` | Exothermic and endothermic energy curves | `catalyst = true` adds a catalyst control |
| `equation-balancer` | Atom counts on each side as coefficients change | `reactants`, `products` (formula lists) |
| `gas-law` | A piston model of a gas | `mode`: `boyle`, `charles` or `ideal` |
| `half-life` | 100 atoms decaying over half-lives | `isotope`, `halfLife`, `unit` |
| `isotope-mix` | Average atomic mass from two isotopes | `light`, `heavy`, `natural` |
| `limiting-reactant` | Molecules before and after a reaction | `reactants`, `product`, `start` |
| `molarity` | Concentration from moles and volume | `mode`: `molarity` or `dilution` |
| `mole-converter` | Grams, moles and particles of a substance | `formulas` |
| `periodic-table` | Periods 1 to 4, optionally shaded by a trend | `property`, `selected` |
| `ph-scale` | pH against ion concentrations | `ph` |
| `sig-figs` | Which digits of a typed number are significant | `value` |
| `specific-heat` | Heat needed by different substances | none |
| `vsepr` | Molecular shapes from bonded atoms and lone pairs | `shape` |

## Writing a new kind

Create `src/interactives/kinds/<name>.js`. It exports one function that receives the toolkit and the params:

```js
export default function (ui, { start = 20 } = {}) {
  const mass = ui.slider({ label: 'Mass', min: 1, max: 100, value: start, unit: 'g' });
  const svg = ui.svg(240, 200, 'A short description for screen readers');

  ui.run(() => {
    svg.replaceChildren(ui.s('circle', { cx: 120, cy: 100, r: mass.value / 2, class: 'i-marker' }));
    ui.readout([['Mass', `${mass.value} g`]]);
  });
}
```

`ui.run` takes the one function that redraws everything. It runs once at the start and again whenever a control changes.

### The toolkit (`src/interactives/lib.js`)

| Call | Gives you |
|---|---|
| `ui.slider({ label, min, max, step, value, unit })` | A range slider; read `.value` (number) |
| `ui.stepper({ label, min, max, value })` | Minus and plus buttons; read `.value` |
| `ui.select({ label, options, value })` | A dropdown; read `.value` (string) |
| `ui.text({ label, value })` | A text box; read `.value` |
| `ui.svg(width, height, description)` | An SVG drawing area |
| `ui.view` | The drawing area's container, for HTML drawings |
| `ui.readout([[label, value], ...])` | The results list under the controls |
| `ui.status(message, ok)` | A one-line message, green or red |
| `ui.h(tag, attrs, ...children)`, `ui.s(...)` | Create HTML and SVG elements |
| `ui.atom(symbol, x, y, r)` | An atom in its element's color |
| `ui.colorOf(symbol)` | An element's color |
| `ui.chem(text)` | Typeset formulas and charges as HTML |
| `ui.fmt(number, sigFigs)` | A number with significant figures, as HTML |
| `ui.parseFormula(f)`, `ui.molarMass(f)` | Formula arithmetic |

Element data is in `src/interactives/data.js`, read from the same `conventions/` files the validator uses.

### Rules

1. **Use the toolkit for every control.** Do not create your own sliders, buttons or inputs. That is what keeps touch targets large enough and keyboard use working.
2. **No colors, fonts or sizes in a kind.** Use the classes in `src/styles/interactive.css` (`i-bond`, `i-glass`, `i-marker` and so on). If you need a new look, add a class there using the existing tokens. Element colors come only from `ui.colorOf` and `ui.atom`.
3. **Say it in the readout too.** Everything the picture shows must also appear as text in `ui.readout` or `ui.status`, so it works with a screen reader.
4. **Use real values.** Take constants and element data from `conventions/`. Do not retype an atomic mass.
5. **Work at 320 px wide.** SVGs scale on their own. For wide HTML, wrap it in an element with class `i-scroll`.
6. **No animation loops and no outside libraries.** The picture changes only when a control changes.
7. **Stay within the lesson.** An interactive should not reveal the answers to that node's own exercises. Use a different example.
8. **Add a row to the table above** when you add a kind.

The validator rejects a node that names a kind with no matching file.
