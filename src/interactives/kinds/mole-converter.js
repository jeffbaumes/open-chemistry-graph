const AVOGADRO = 6.022e23;

export default function (ui, { formulas = ['H2O', 'CO2', 'NaCl', 'C6H12O6', 'Fe'] } = {}) {
  const { h } = ui;
  const substance = ui.select({ label: 'Substance', options: formulas.map((f) => [f, ui.chemText(f)]) });
  const mass = ui.slider({ label: 'Mass', min: 1, max: 200, value: 18, unit: 'g' });
  const chain = h('div', { class: 'i-chain' });
  ui.view.append(chain);

  const box = (value, unit) => h('div', { class: 'i-box' }, h('strong', { html: value }), h('span', {}, unit));
  const step = (text) => h('div', { class: 'i-step', html: text });

  ui.run(() => {
    const molar = ui.molarMass(substance.value);
    const moles = mass.value / molar;
    chain.replaceChildren(
      box(String(mass.value), 'grams'),
      step(`÷ ${ui.fmt(molar, 4)} g/mol`),
      box(ui.fmt(moles), 'moles'),
      step('× 6.022 × 10<sup>23</sup>'),
      box(ui.fmt(moles * AVOGADRO), 'particles'));
    ui.readout([[`Molar mass of ${ui.chem(substance.value)}`, `${ui.fmt(molar, 4)} g/mol`]]);
  });
}
