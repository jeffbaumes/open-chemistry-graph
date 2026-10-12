// Atoms side by side, drawn to scale by atomic radius.
//
// state: { elements: [symbol] }

import { elementOf } from '../../interactives/data.js';

const SCALE = 36 / 227; // pixels per picometer; potassium, the largest here, is 227 pm

export default {
  render(state) {
    const atoms = state.elements.map(elementOf);
    const cell = 640 / atoms.length;
    const bySize = [...atoms].sort((a, b) => a.radius - b.radius);
    const row = (el) => `<td><span class="i-count">${el.radius}</span></td>`;
    return {
      footer: `<table class="i-tally a-tally a-wide"><tr><th>Atom</th>${atoms.map((el) => `<th>${el.symbol}</th>`).join('')}</tr><tr><th>Radius, pm</th>${atoms.map(row).join('')}</tr></table>`,
      sprites: atoms.map((el, i) => ({ id: el.symbol, type: 'atom', symbol: el.symbol, x: cell * (i + 0.5), y: 120, r: el.radius * SCALE })),
      vars: {
        smallest: bySize[0].name.toLowerCase(), largest: bySize.at(-1).name.toLowerCase(),
        ...Object.fromEntries(atoms.flatMap((el) => [[`r.${el.symbol}`, el.radius], [`ie.${el.symbol}`, el.ionization], [`en.${el.symbol}`, el.electronegativity]])),
      },
    };
  },
};
