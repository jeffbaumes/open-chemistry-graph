export default function (ui, { mass = 40, volume = 60 } = {}) {
  const { s } = ui;
  const m = ui.slider({ label: 'Mass', min: 5, max: 200, step: 5, value: mass, unit: 'g' });
  const v = ui.slider({ label: 'Volume', min: 10, max: 100, step: 5, value: volume, unit: 'cm^3' });
  const svg = ui.svg(240, 200, 'A block in a tank of water');
  const surface = 70;
  const floor = 190;

  ui.run(() => {
    const density = m.value / v.value;
    const side = 14 * Math.cbrt(v.value);
    // A floating block sits with a fraction of its height under water equal to its density.
    const top = density < 1 ? surface - side * (1 - density) : floor - side;
    svg.replaceChildren(
      s('rect', { x: 30, y: surface, width: 180, height: floor - surface, class: 'i-water' }),
      s('rect', { x: 120 - side / 2, y: top, width: side, height: side, class: 'i-block', 'fill-opacity': Math.min(1, 0.25 + density / 3) }),
      s('path', { d: `M30 15 V${floor} H210 V15`, class: 'i-glass' }));
    ui.readout([
      ['Density', `${m.value} g ÷ ${v.value} cm<sup>3</sup> = <strong>${ui.fmt(density)} g/cm<sup>3</sup></strong>`],
      ['In water, 1.00 g/cm<sup>3</sup>', density < 1 ? 'Floats' : density > 1 ? 'Sinks' : 'Hovers: the same density as water'],
    ]);
  });
}
