// One formula drawn as atoms, with its atoms counted.
//
// state: { formula, coefficient? }

import { layoutOf } from '../molecules.js';

const PREFIXES = ['', 'mono', 'di', 'tri', 'tetra', 'penta', 'hexa'];

export default {
  render(state, ui) {
    const n = state.coefficient ?? 1;
    const each = ui.parseFormula(state.formula);
    const layout = layoutOf(state.formula, ui.parseFormula);
    const xs = layout.map(([, x]) => x);
    const extent = Math.max(...xs) - Math.min(...xs) + 2; // width of one copy, in atom radii
    // As large as fits across the stage.
    const R = Math.min(26, 600 / (n * extent + (n - 1) * 1.6));
    const spacing = (extent + 1.6) * R;
    const middle = (Math.max(...xs) + Math.min(...xs)) / 2;
    const sprites = [];
    for (let k = 0; k < n; k++) {
      const cx = 320 + (k - (n - 1) / 2) * spacing;
      layout.forEach(([symbol, x, y], j) => sprites.push({ id: `${state.formula}-${k}-${j}`, type: 'atom', symbol, x: cx + (x - middle) * R, y: 120 + y * R, r: R }));
    }
    const total = Object.values(each).reduce((sum, count) => sum + count, 0) * n;
    const rows = Object.entries(each).map(([el, count]) =>
      `<tr><th><span class="i-dot" style="background:${ui.colorOf(el)}"></span> ${el}</th><td><span class="i-count">${count * n}</span></td></tr>`);
    return {
      header: `${n > 1 ? `<b class="a-coefficient">${n}</b> ` : ''}${ui.chem(state.formula)}`,
      footer: `<table class="i-tally a-tally"><tr><th>Atoms</th><th>Count</th></tr>${rows.join('')}</table>`,
      sprites,
      vars: {
        total,
        elements: Object.keys(each).length,
        mass: Number(ui.molarMass(state.formula).toFixed(2)),
        ...Object.fromEntries(Object.entries(each).flatMap(([el, count]) => [[`count.${el}`, count * n], [`each.${el}`, count], [`prefix.${el}`, PREFIXES[count] ?? '']])),
      },
    };
  },
};
