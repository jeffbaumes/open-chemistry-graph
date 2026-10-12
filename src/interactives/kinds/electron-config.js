import { elements } from '../data.js';

// Sublevels in filling order, with how many orbitals each has.
const ORDER = [['1s', 1], ['2s', 1], ['2p', 3], ['3s', 1], ['3p', 3], ['4s', 1], ['3d', 5], ['4p', 3]];
// Chromium and copper move one 4s electron into 3d.
const EXCEPTIONS = { 24: { '4s': 1, '3d': 5 }, 29: { '4s': 1, '3d': 10 } };

function configuration(z) {
  let left = z;
  const filled = ORDER.map(([name, orbitals]) => {
    const count = Math.min(orbitals * 2, left);
    left -= count;
    return { name, orbitals, count: EXCEPTIONS[z]?.[name] ?? count };
  });
  return filled.filter((sublevel) => sublevel.count > 0);
}

export default function (ui, { z = 11 } = {}) {
  const { h } = ui;
  const atomic = ui.slider({ label: 'Atomic number', min: 1, max: 36, value: z });
  const diagram = h('div', { class: 'i-orbitals' });
  ui.view.append(diagram);

  ui.run(() => {
    const element = elements[atomic.value - 1];
    const config = configuration(atomic.value);
    diagram.replaceChildren(...config.map(({ name, orbitals, count }) =>
      h('div', { class: 'i-sublevel' },
        h('div', { class: 'i-boxes' }, Array.from({ length: orbitals }, (_, i) => {
          // Hund's rule: one electron goes in each orbital before any pair up.
          const inBox = (count > i ? 1 : 0) + (count > orbitals + i ? 1 : 0);
          return h('span', { class: 'i-orbital' }, '↑↓'.slice(0, inBox));
        })),
        h('span', { class: 'i-label' }, name))));

    const level = Math.max(...config.map((sublevel) => Number(sublevel.name[0])));
    const outer = config.filter((sublevel) => Number(sublevel.name[0]) === level).reduce((sum, sublevel) => sum + sublevel.count, 0);
    ui.readout([
      ['Element', `${element.name} (${element.symbol})`],
      ['Configuration', config.map((sublevel) => `${sublevel.name}<sup>${sublevel.count}</sup>`).join(' ')],
      ['Outer level', `${outer} electron${outer === 1 ? '' : 's'} in level ${level}`],
    ]);
  });
}
