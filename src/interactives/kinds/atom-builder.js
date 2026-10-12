import { elements } from '../data.js';

const SHELLS = [2, 8, 8, 2];

export default function (ui, { protons = 6, neutrons = 6, electrons = 6 } = {}) {
  const { s } = ui;
  const p = ui.stepper({ label: 'Protons', min: 1, max: 20, value: protons });
  const n = ui.stepper({ label: 'Neutrons', min: 0, max: 24, value: neutrons });
  const e = ui.stepper({ label: 'Electrons', min: 0, max: 20, value: electrons });
  const svg = ui.svg(240, 240, 'Diagram of the atom: nucleus and electron shells');

  ui.run(() => {
    const element = elements[p.value - 1];
    const parts = [];
    let left = e.value;
    SHELLS.forEach((capacity, i) => {
      const count = Math.min(capacity, left);
      left -= count;
      if (!count) return;
      const r = 48 + i * 22;
      parts.push(s('circle', { cx: 120, cy: 120, r, class: 'i-shell' }));
      for (let k = 0; k < count; k++) {
        const angle = (2 * Math.PI * k) / count - Math.PI / 2;
        parts.push(s('circle', { cx: 120 + r * Math.cos(angle), cy: 120 + r * Math.sin(angle), r: 5, class: 'i-electron' }));
      }
    });
    parts.push(
      s('circle', { cx: 120, cy: 120, r: 28, fill: ui.colorOf(element.symbol), class: 'i-atom' }),
      s('text', { x: 120, y: 113, class: 'i-on-color', 'font-size': 12 }, `${p.value} p`),
      s('text', { x: 120, y: 128, class: 'i-on-color', 'font-size': 12 }, `${n.value} n`));
    svg.replaceChildren(...parts);

    const charge = p.value - e.value;
    const size = Math.abs(charge);
    const sign = charge > 0 ? '+' : '−';
    ui.readout([
      ['Element', `${element.name} (${element.symbol})`],
      ['Mass number', `${p.value} + ${n.value} = ${p.value + n.value}`],
      ['Charge', charge === 0 ? '0, a neutral atom' : `${size}${sign}, ${charge > 0 ? 'a cation' : 'an anion'}`],
      ['Symbol', `<sup>${p.value + n.value}</sup>${element.symbol}${charge ? `<sup>${size > 1 ? size : ''}${sign}</sup>` : ''}`],
    ]);
  });
}
