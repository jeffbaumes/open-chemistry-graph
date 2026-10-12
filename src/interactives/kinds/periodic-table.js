import { elements, elementOf } from '../data.js';

const PROPERTIES = {
  none: ['Nothing', ''],
  radius: ['Atomic radius', 'pm'],
  ionization: ['Ionization energy', 'kJ/mol'],
  electronegativity: ['Electronegativity', ''],
};
const KINDS = { m: 'Metal', n: 'Nonmetal', d: 'Metalloid' };

export default function (ui, { property = 'none', selected = 'C' } = {}) {
  const { h } = ui;
  const shade = ui.select({
    label: 'Shade by',
    options: Object.entries(PROPERTIES).map(([key, [label]]) => [key, label]),
    value: property,
  });
  const grid = h('div', { class: 'i-ptable', role: 'group', 'aria-label': 'Periodic table, periods 1 to 4' });
  ui.view.append(h('div', { class: 'i-scroll' }, grid), h('p', { class: 'i-hint' }, 'Scroll sideways to see all 18 groups.'));
  let current = elementOf(selected);

  const draw = () => {
    const key = shade.value;
    const values = elements.map((el) => el[key]).filter(Boolean);
    const [low, high] = [Math.min(...values), Math.max(...values)];
    grid.replaceChildren(...elements.map((el) => {
      const strength = key === 'none' || !el[key] ? 0 : 12 + 78 * ((el[key] - low) / (high - low));
      return h('button', {
        type: 'button',
        class: `i-cell${strength > 55 ? ' i-strong' : ''}`,
        style: `grid-column:${el.group};grid-row:${el.period};--strength:${strength}%`,
        'aria-label': el.name,
        'aria-pressed': String(el === current),
        onclick: () => { current = el; draw(); },
      }, h('small', {}, String(el.z)), el.symbol);
    }));
    ui.readout([
      ['Element', `${current.name} (${current.symbol}), atomic number ${current.z}`],
      ['Position', `Group ${current.group}, period ${current.period}. ${KINDS[current.kind]}`],
      ['Atomic radius', `${current.radius} pm`],
      ['Ionization energy', `${current.ionization} kJ/mol`],
      ['Electronegativity', current.electronegativity ? current.electronegativity.toFixed(2) : 'None assigned'],
    ]);
  };
  ui.run(draw);
}
