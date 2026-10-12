// A chemical equation shown as molecules, with atom counts worked out from
// what is on screen. A step only sets the coefficients (and, optionally, which
// element to focus on); everything else here is derived.
//
// state: { reactants: [formula], products: [formula], coefficients: [n], focus?: symbol }

import { layoutOf } from '../molecules.js';

const WIDTH = 640;
const HEIGHT = 240;
const SIDE = 270; // width of each side of the arrow

export default {
  render(state, ui) {
    const species = [...state.reactants, ...state.products].map((formula, i) => ({
      formula,
      side: i < state.reactants.length ? 'left' : 'right',
      coeff: state.coefficients[i],
      atoms: ui.parseFormula(formula),
    }));
    const sides = { left: species.filter((sp) => sp.side === 'left'), right: species.filter((sp) => sp.side === 'right') };
    const totals = {};
    for (const [side, list] of Object.entries(sides)) {
      for (const sp of list) {
        for (const [el, n] of Object.entries(sp.atoms)) {
          totals[el] ??= { left: 0, right: 0 };
          totals[el][side] += n * sp.coeff;
        }
      }
    }

    const term = (sp) => `${sp.coeff > 1 ? `<b class="a-coefficient">${sp.coeff}</b> ` : ''}${ui.chem(sp.formula)}`;
    const header = `${sides.left.map(term).join(' + ')} → ${sides.right.map(term).join(' + ')}`;

    const footer = `<table class="i-tally a-tally"><tr><th>Atoms</th><th>Reactants</th><th>Products</th></tr>${Object.entries(totals)
      .map(([el, t]) => `<tr class="${t.left === t.right ? 'i-ok' : 'i-off'}${state.focus === el ? ' a-focus' : ''}">
        <th><span class="i-dot" style="background:${ui.colorOf(el)}"></span> ${el}</th>
        <td><span class="i-count">${t.left}</span></td><td><span class="i-count">${t.right}</span></td></tr>`)
      .join('')}</table>`;

    const sprites = [{ id: 'arrow', type: 'text', text: '→', x: WIDTH / 2, y: HEIGHT / 2, size: 44 }];
    for (const [side, list] of Object.entries(sides)) {
      const x0 = side === 'left' ? 10 : WIDTH - 10 - SIDE;
      const column = SIDE / list.length;
      list.forEach((sp, t) => {
        const cx = x0 + column * (t + 0.5);
        if (t > 0) sprites.push({ id: `${side}-plus-${t}`, type: 'text', text: '+', x: x0 + column * t, y: HEIGHT / 2, size: 32 });
        // Shrink the atoms when a term has many molecules or the side has many terms.
        const spacing = Math.min(84, 210 / sp.coeff);
        const r = Math.max(8, Math.min(20, spacing / 3.6, column / 5.5));
        for (let k = 0; k < sp.coeff; k++) {
          const cy = HEIGHT / 2 + (k - (sp.coeff - 1) / 2) * spacing;
          layoutOf(sp.formula, ui.parseFormula).forEach(([symbol, ax, ay], j) => {
            sprites.push({ id: `${side}-${t}-${k}-${j}`, type: 'atom', symbol, x: cx + ax * r, y: cy + ay * r, r, dim: Boolean(state.focus) && symbol !== state.focus });
          });
        }
      });
    }

    // Values a caption can use, so the numbers are never typed by hand:
    // {left.O} and {right.O} for atom counts, {c1}, {c2}, ... for coefficients.
    const vars = Object.fromEntries([
      ...Object.entries(totals).flatMap(([el, t]) => [[`left.${el}`, t.left], [`right.${el}`, t.right]]),
      ...species.map((sp, i) => [`c${i + 1}`, sp.coeff]),
    ]);
    return { header, footer, sprites, vars };
  },
};
