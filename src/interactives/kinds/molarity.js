// mode "molarity": change moles and volume.  "dilution": moles fixed, add water.
export default function (ui, { mode = 'molarity' } = {}) {
  const { s } = ui;
  const diluting = mode === 'dilution';
  const moles = diluting ? { value: 0.5 } : ui.slider({ label: 'Solute', min: 0.1, max: 2, step: 0.1, value: 0.5, unit: 'mol' });
  const volume = ui.slider({ label: diluting ? 'Total volume' : 'Solution volume', min: 0.25, max: 2, step: 0.25, value: diluting ? 0.25 : 1, unit: 'L' });
  const svg = ui.svg(240, 200, 'Beaker of solution, darker when more concentrated');

  ui.run(() => {
    const molarity = moles.value / volume.value;
    const height = volume.value * 75;
    svg.replaceChildren(
      s('rect', { x: 70, y: 190 - height, width: 100, height, class: 'i-solution', 'fill-opacity': Math.min(1, 0.1 + molarity / 4.5) }),
      s('path', { d: 'M70 25 V190 H170 V25', class: 'i-glass' }));
    ui.readout([
      ['Solute', `${moles.value} mol${diluting ? ', unchanged' : ''}`],
      ['Volume', `${volume.value} L`],
      ['Molarity', `${moles.value} mol ÷ ${volume.value} L = <strong>${ui.fmt(molarity)} M</strong>`],
    ]);
  });
}
