const DEFAULT = {
  reactants: [{ formula: 'H2', coeff: 2 }, { formula: 'O2', coeff: 1 }],
  product: { formula: 'H2O', coeff: 2 },
  start: [4, 4],
};

export default function (ui, params = {}) {
  const { reactants, product, start } = { ...DEFAULT, ...params };
  const { h } = ui;
  const amounts = reactants.map((r, i) => ui.stepper({ label: r.formula, min: 0, max: 10, value: start[i] }));
  const term = ({ formula, coeff }) => `${coeff > 1 ? `${coeff} ` : ''}${ui.chem(formula)}`;
  const before = h('div', { class: 'i-chips' });
  const after = h('div', { class: 'i-chips' });
  ui.view.append(
    h('p', { class: 'i-equation', html: `${reactants.map(term).join(' + ')} → ${term(product)}` }),
    h('p', { class: 'i-label' }, 'Before the reaction'), before,
    h('p', { class: 'i-label' }, 'After the reaction'), after);

  const chips = (formula, n, kind = '') => Array.from({ length: n }, () => h('span', { class: `i-chip ${kind}`, html: ui.chem(formula) }));
  const list = (items) => items.join(' and ') || 'nothing';

  ui.run(() => {
    const have = amounts.map((a) => a.value);
    const runs = Math.min(...reactants.map((r, i) => Math.floor(have[i] / r.coeff)));
    const left = reactants.map((r, i) => have[i] - runs * r.coeff);
    before.replaceChildren(...reactants.flatMap((r, i) => chips(r.formula, have[i])));
    after.replaceChildren(
      ...chips(product.formula, runs * product.coeff, 'i-product'),
      ...reactants.flatMap((r, i) => chips(r.formula, left[i], 'i-leftover')));

    const ratios = reactants.map((r, i) => have[i] / r.coeff);
    const lowest = Math.min(...ratios);
    const limiting = ratios.every((x) => x === lowest) ? [] : reactants.filter((_, i) => ratios[i] === lowest);
    ui.readout([
      ['Limiting reactant', limiting.length ? list(limiting.map((r) => ui.chem(r.formula))) : 'Neither: they are in the exact ratio'],
      ['Product formed', `${runs * product.coeff} ${ui.chem(product.formula)}`],
      ['Left over', list(reactants.flatMap((r, i) => (left[i] ? [`${left[i]} ${ui.chem(r.formula)}`] : [])))],
    ]);
  });
}
