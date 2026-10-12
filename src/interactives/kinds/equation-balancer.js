export default function (ui, { reactants = ['H2', 'O2'], products = ['H2O'] } = {}) {
  const { h } = ui;
  const sides = [reactants, products].map((side) =>
    side.map((formula) => ({
      formula,
      atoms: ui.parseFormula(formula),
      coeff: ui.stepper({ label: formula, min: 1, max: 9, value: 1 }),
    })));
  const equation = h('p', { class: 'i-equation' });
  const tally = h('table', { class: 'i-tally' });
  ui.view.append(equation, tally);

  const count = (side) => {
    const total = {};
    for (const { atoms, coeff } of side) {
      for (const [el, n] of Object.entries(atoms)) total[el] = (total[el] ?? 0) + n * coeff.value;
    }
    return total;
  };
  const cell = (el, n) =>
    h('td', {},
      h('span', { class: 'i-dots' }, Array.from({ length: Math.min(n, 24) }, () => h('span', { class: 'i-dot', style: `background:${ui.colorOf(el)}` }))),
      h('span', { class: 'i-count' }, String(n)));

  ui.run(() => {
    const [left, right] = sides.map(count);
    const term = ({ formula, coeff }) => `${coeff.value > 1 ? `${coeff.value} ` : ''}${ui.chem(formula)}`;
    equation.innerHTML = sides.map((side) => side.map(term).join(' + ')).join(' → ');
    tally.replaceChildren(
      h('tr', {}, h('th', {}, 'Element'), h('th', {}, 'Reactants'), h('th', {}, 'Products')),
      ...Object.keys(left).map((el) =>
        h('tr', { class: left[el] === right[el] ? 'i-ok' : 'i-off' }, h('th', {}, el), cell(el, left[el]), cell(el, right[el] ?? 0))));
    const balanced = Object.keys(left).every((el) => left[el] === right[el]);
    ui.status(balanced ? 'Balanced: every element has the same count on both sides.' : 'Not balanced yet.', balanced);
  });
}
