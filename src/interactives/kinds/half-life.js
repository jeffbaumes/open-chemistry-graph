export default function (ui, { isotope = 'Carbon-14', halfLife = 5730, unit = 'years' } = {}) {
  const { h } = ui;
  const elapsed = ui.slider({ label: 'Half-lives elapsed', min: 0, max: 7, value: 0 });
  const grid = h('div', { class: 'i-grid', role: 'img' });
  ui.view.append(grid);
  // A fixed shuffle, so the same atoms stay decayed as time moves forward.
  const rank = Array.from({ length: 100 }, (_, i) => (i * 37 + 11) % 100);
  const cells = rank.map(() => h('span', { class: 'i-dot' }));
  grid.append(...cells);

  ui.run(() => {
    const remaining = Math.round(100 * 0.5 ** elapsed.value);
    rank.forEach((r, i) => cells[i].classList.toggle('i-decayed', r >= remaining));
    grid.setAttribute('aria-label', `${remaining} of 100 atoms have not decayed`);
    ui.readout([
      ['Isotope', `${isotope}, half-life ${halfLife.toLocaleString('en-US')} ${unit}`],
      ['Time elapsed', `${(elapsed.value * halfLife).toLocaleString('en-US')} ${unit}`],
      ['Fraction remaining', elapsed.value === 0 ? '1' : `1/${2 ** elapsed.value}`],
      ['Atoms remaining', `${remaining} of 100`],
    ]);
  });
}
