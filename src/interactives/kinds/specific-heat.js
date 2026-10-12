// Specific heats in J/(g·°C).
const SUBSTANCES = { Water: 4.184, Aluminum: 0.897, Iron: 0.449, Copper: 0.385 };

export default function (ui) {
  const { h } = ui;
  const mass = ui.slider({ label: 'Mass', min: 10, max: 500, step: 10, value: 100, unit: 'g' });
  const rise = ui.slider({ label: 'Temperature rise', min: 1, max: 80, value: 20, unit: '°C' });
  const bars = h('div', { class: 'i-bars' });
  ui.view.append(bars);

  ui.run(() => {
    const most = mass.value * SUBSTANCES.Water * rise.value;
    bars.replaceChildren(...Object.entries(SUBSTANCES).map(([name, c]) => {
      const q = mass.value * c * rise.value;
      return h('div', { class: 'i-bar-row' },
        h('span', { class: 'i-label' }, name),
        h('span', { class: 'i-track' }, h('span', { class: 'i-bar', style: `width:${(q / most) * 100}%` })),
        h('span', { class: 'i-count', html: `${ui.fmt(q)} J` }));
    }));
    ui.readout([
      ['Heat for water', `${mass.value} g × 4.184 J/(g·°C) × ${rise.value} °C = <strong>${ui.fmt(most)} J</strong>`],
    ]);
  });
}
