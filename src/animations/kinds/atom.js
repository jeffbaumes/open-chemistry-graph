// One atom or ion as a nucleus with electrons in shells. A step names the
// element and, for an ion, how many electrons it has; the proton count,
// charge and outer-level count are worked out.
//
// state: { symbol, electrons? (defaults to neutral), mass_number?, focus?: "valence" }

import { elementOf } from '../../interactives/data.js';

const SHELLS = [2, 8, 8, 2]; // valid up to calcium
const CX = 320;
const CY = 120;

export function describe({ symbol, electrons }) {
  const element = elementOf(symbol);
  const count = electrons ?? element.z;
  const shells = [];
  let left = count;
  for (const capacity of SHELLS) {
    if (left <= 0) break;
    shells.push(Math.min(capacity, left));
    left -= capacity;
  }
  const net = element.z - count;
  const sign = net > 0 ? '+' : '−';
  return {
    element,
    electrons: count,
    shells,
    net,
    charge: net === 0 ? '0' : `${Math.abs(net)}${sign}`,
    superscript: net === 0 ? '' : `${Math.abs(net) > 1 ? Math.abs(net) : ''}${sign}`,
  };
}

export default {
  render(state) {
    const { element, electrons, shells, net, charge, superscript } = describe(state);
    const mass = state.mass_number;
    const sprites = [];
    shells.forEach((count, i) => {
      const r = 40 + i * 23;
      const outer = i === shells.length - 1;
      sprites.push({ id: `shell${i}`, type: 'ring', x: CX, y: CY, r });
      for (let k = 0; k < count; k++) {
        const angle = (2 * Math.PI * k) / count - Math.PI / 2;
        sprites.push({ id: `e${i}-${k}`, type: 'dot', class: 'i-electron', x: CX + r * Math.cos(angle), y: CY + r * Math.sin(angle), r: 5, dim: state.focus === 'valence' && !outer });
      }
    });
    sprites.push({ id: `nucleus-${element.symbol}`, type: 'atom', symbol: element.symbol, label: `${element.z}+`, x: CX, y: CY, r: 22 });

    const row = (label, value) => `<tr><th>${label}</th><td><span class="i-count">${value}</span></td></tr>`;
    return {
      header: `${element.name}${mass ? `-${mass}` : ''}: ${element.symbol}${superscript ? `<sup>${superscript}</sup>` : ''}`,
      footer: `<table class="i-tally a-tally">${row('Protons', element.z)}${mass ? row('Neutrons', mass - element.z) : ''}${row('Electrons', electrons)}${row('Charge', net === 0 ? '0 (neutral)' : charge)}</table>`,
      sprites,
      vars: {
        name: element.name.toLowerCase(), symbol: element.symbol, protons: element.z, electrons, charge, valence: shells.at(-1) ?? 0, levels: shells.length,
        ...(mass ? { mass_number: mass, neutrons: mass - element.z } : {}),
      },
    };
  },
};
