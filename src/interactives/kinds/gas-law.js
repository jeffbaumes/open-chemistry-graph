const R = 0.08206; // L·atm/(mol·K)

// mode "boyle": change V, see P (T fixed).  "charles": change T, see V (P fixed).
// "ideal": change n, T and V, see P.
export default function (ui, { mode = 'ideal' } = {}) {
  const { s } = ui;
  const n = mode === 'ideal' ? ui.slider({ label: 'Amount of gas', min: 0.5, max: 3, step: 0.5, value: 1, unit: 'mol' }) : { value: 1 };
  const T = mode === 'boyle' ? { value: 300 } : ui.slider({ label: 'Temperature', min: 100, max: 600, step: 10, value: 300, unit: 'K' });
  const V = mode === 'charles' ? null : ui.slider({ label: 'Volume', min: 5, max: 50, value: 25, unit: 'L' });
  const svg = ui.svg(240, 220, 'Gas particles in a cylinder under a piston');
  // Fixed scattered positions, so particles do not jump around when a slider moves.
  const spots = Array.from({ length: 60 }, (_, i) => [((i * 61) % 97) / 97, ((i * 37) % 89) / 89]);

  ui.run(() => {
    const volume = V ? V.value : n.value * R * T.value; // at 1 atm
    const pressure = (n.value * R * T.value) / volume;
    const height = 20 + volume * 3;
    const top = 205 - height;
    svg.replaceChildren(
      s('rect', { x: 60, y: top, width: 120, height, class: 'i-gas' }),
      ...spots.slice(0, n.value * 20).map(([x, y]) =>
        s('circle', { cx: 67 + x * 106, cy: top + 6 + y * (height - 12), r: 3, class: 'i-particle' })),
      s('path', { d: 'M60 10 V205 H180 V10', class: 'i-glass' }),
      s('rect', { x: 116, y: 0, width: 8, height: Math.max(0, top - 8), class: 'i-piston' }),
      s('rect', { x: 62, y: top - 8, width: 116, height: 8, class: 'i-piston' }));

    const rows = [
      ['Pressure', `${ui.fmt(pressure)} atm`],
      ['Volume', `${ui.fmt(volume)} L`],
      ['Temperature', `${T.value} K`],
    ];
    if (mode === 'boyle') rows.push(['P × V', `${ui.fmt(pressure * volume)} L·atm, always the same`]);
    if (mode === 'charles') rows.push(['V ÷ T', `${ui.fmt(volume / T.value)} L/K, always the same`]);
    if (mode === 'ideal') rows.push(['Amount', `${n.value} mol`]);
    ui.readout(rows);
  });
}
