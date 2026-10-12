const CHLORINE = {
  light: { label: 'Cl-35', mass: 34.97 },
  heavy: { label: 'Cl-37', mass: 36.97 },
  natural: 75.8, // percent of the lighter isotope found in nature
};

export default function (ui, params = {}) {
  const { light, heavy, natural } = { ...CHLORINE, ...params };
  const { h } = ui;
  const share = ui.slider({ label: `Abundance of ${light.label}`, min: 0, max: 100, value: 50, unit: '%' });
  const [a, b] = [h('span', { class: 'i-split-a' }), h('span', { class: 'i-split-b' })];
  ui.view.append(h('div', { class: 'i-split' }, a, b));
  const average = (percent) => (light.mass * percent + heavy.mass * (100 - percent)) / 100;

  ui.run(() => {
    const percent = share.value;
    a.style.width = `${percent}%`;
    a.textContent = percent >= 15 ? light.label : '';
    b.textContent = percent <= 85 ? heavy.label : '';
    ui.readout([
      ['Average atomic mass', `(${light.mass} × ${(percent / 100).toFixed(2)}) + (${heavy.mass} × ${(1 - percent / 100).toFixed(2)}) = <strong>${average(percent).toFixed(2)} amu</strong>`],
      ['In nature', `${natural}% ${light.label}, which gives ${average(natural).toFixed(2)} amu`],
    ]);
  });
}
