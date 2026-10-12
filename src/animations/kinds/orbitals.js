// Orbital boxes filling in order as the atomic number rises.
//
// state: { z }

import { elements } from '../../interactives/data.js';

// Sublevels in filling order, with how many orbitals each has.
const ORDER = [['1s', 1], ['2s', 1], ['2p', 3], ['3s', 1], ['3p', 3], ['4s', 1], ['3d', 5], ['4p', 3]];
// Chromium and copper move one 4s electron into 3d.
const EXCEPTIONS = { 24: { '4s': 1, '3d': 5 }, 29: { '4s': 1, '3d': 10 } };
const GAP = 14;

export function configuration(z) {
  let left = z;
  return ORDER.map(([name, orbitals]) => {
    const count = Math.min(orbitals * 2, left);
    left -= count;
    return { name, orbitals, count: EXCEPTIONS[z]?.[name] ?? count };
  }).filter((sublevel) => sublevel.count > 0);
}

export default {
  render(state) {
    const element = elements[state.z - 1];
    const config = configuration(state.z);
    const boxes = config.reduce((sum, sub) => sum + sub.orbitals, 0);
    // As large as fits: a few big boxes for light elements, smaller ones later.
    const BOX = Math.min(64, (610 - (config.length - 1) * GAP) / boxes);
    const width = boxes * BOX + (config.length - 1) * GAP;
    const sprites = [];
    let x = 320 - width / 2;
    for (const { name, orbitals, count } of config) {
      for (let i = 0; i < orbitals; i++) {
        sprites.push({ id: `${name}-box${i}`, type: 'rect', class: 'a-orbital', x: x + i * BOX, y: 110 - BOX * 0.65, w: BOX, h: BOX * 1.3 });
        // Hund's rule: one electron goes in each orbital before any pair up.
        if (count > i) sprites.push({ id: `${name}-${i}-up`, type: 'text', class: 'a-spin', text: '↑', x: x + i * BOX + BOX * 0.32, y: 110, size: BOX * 0.62 });
        if (count > orbitals + i) sprites.push({ id: `${name}-${i}-down`, type: 'text', class: 'a-spin', text: '↓', x: x + i * BOX + BOX * 0.68, y: 110, size: BOX * 0.62 });
      }
      sprites.push({ id: `${name}-label`, type: 'text', text: name, x: x + (orbitals * BOX) / 2, y: 110 + BOX * 0.65 + 20, size: 22 });
      x += orbitals * BOX + GAP;
    }
    const written = config.map((sub) => `${sub.name}^${sub.count}`).join(' ');
    const level = Math.max(...config.map((sub) => Number(sub.name[0])));
    return {
      header: `${element.name}: ${state.z} electron${state.z === 1 ? '' : 's'}`,
      sprites,
      vars: {
        name: element.name.toLowerCase(), symbol: element.symbol, z: state.z, config: written,
        last: config.at(-1).name,
        valence: config.filter((sub) => Number(sub.name[0]) === level).reduce((sum, sub) => sum + sub.count, 0),
      },
    };
  },
};
