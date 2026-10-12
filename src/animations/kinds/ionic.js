// Ions of a metal and a nonmetal, with their charges added up. The charges
// come from each element's group, so a step only says how many of each ion.
//
// state: { metal, nonmetal, metals?, nonmetals? }

import { elementOf, valenceOf } from '../../interactives/data.js';

export function charges({ metal, nonmetal, metals = 1, nonmetals = 1 }) {
  const up = valenceOf(metal); // a metal loses its valence electrons
  const down = 8 - valenceOf(nonmetal); // a nonmetal gains enough to reach 8
  return { up, down, plus: up * metals, minus: down * nonmetals, metals, nonmetals };
}

const signed = (n, sign) => `${n === 1 ? '' : n}${sign}`;

export default {
  render(state, ui) {
    const { up, down, plus, minus, metals, nonmetals } = charges(state);
    const column = (symbol, count, x, label, side) =>
      Array.from({ length: count }, (_, k) => ({ id: `${side}-${symbol}-${k}`, type: 'atom', symbol, label, x, y: 120 + (k - (count - 1) / 2) * 54, r: 23 }));
    const net = plus - minus;
    const formula = `${state.metal}${metals > 1 ? metals : ''}${state.nonmetal}${nonmetals > 1 ? nonmetals : ''}`;
    const row = (label, value) => `<tr><th>${label}</th><td><span class="i-count">${value}</span></td></tr>`;
    return {
      header: net === 0 ? ui.chem(formula) : `${elementOf(state.metal).name} and ${elementOf(state.nonmetal).name.toLowerCase()}`,
      footer: `<table class="i-tally a-tally">${row('Positive charge', `${plus}+`)}${row('Negative charge', `${minus}−`)}
        <tr class="${net === 0 ? 'i-ok' : 'i-off'}"><th>Overall</th><td><span class="i-count">${net === 0 ? '0, neutral' : `${Math.abs(net)}${net > 0 ? '+' : '−'}`}</span></td></tr></table>`,
      sprites: [
        ...column(state.metal, metals, 250, `${state.metal}${signed(up, '+')}`, 'metal'),
        ...column(state.nonmetal, nonmetals, 390, `${state.nonmetal}${signed(down, '−')}`, 'nonmetal'),
      ],
      vars: {
        formula, plus, minus, metals, nonmetals,
        net: net === 0 ? '0' : `${Math.abs(net)}${net > 0 ? '+' : '−'}`,
        metal_charge: `${up}+`, nonmetal_charge: `${down}−`,
        metal: elementOf(state.metal).name.toLowerCase(), nonmetal: elementOf(state.nonmetal).name.toLowerCase(),
      },
    };
  },
};
