// Bond and lone-pair directions are drawing angles in degrees, counterclockwise from the right.
const SHAPES = [
  { key: '2-0', label: '2 bonded atoms, no lone pairs', shape: 'Linear', angle: '180°', example: 'CO2', center: 'C', outer: 'O', bonds: [180, 0], lone: [] },
  { key: '3-0', label: '3 bonded atoms, no lone pairs', shape: 'Trigonal planar', angle: '120°', example: 'BF3', center: 'B', outer: 'F', bonds: [90, 210, 330], lone: [] },
  { key: '4-0', label: '4 bonded atoms, no lone pairs', shape: 'Tetrahedral', angle: '109.5°', example: 'CH4', center: 'C', outer: 'H', bonds: [90, 200, 340, 270], lone: [] },
  { key: '3-1', label: '3 bonded atoms, 1 lone pair', shape: 'Trigonal pyramidal', angle: 'about 107°', example: 'NH3', center: 'N', outer: 'H', bonds: [200, 340, 270], lone: [90] },
  { key: '2-2', label: '2 bonded atoms, 2 lone pairs', shape: 'Bent', angle: 'about 104.5°', example: 'H2O', center: 'O', outer: 'H', bonds: [218, 322], lone: [55, 125] },
];

const at = (degrees, r) => [120 + r * Math.cos((degrees * Math.PI) / 180), 105 - r * Math.sin((degrees * Math.PI) / 180)];

export default function (ui, { shape = '4-0' } = {}) {
  const { s } = ui;
  const pick = ui.select({ label: 'Central atom has', options: SHAPES.map((x) => [x.key, x.label]), value: shape });
  const svg = ui.svg(240, 210, 'Flat drawing of the molecule');

  ui.run(() => {
    const m = SHAPES.find((x) => x.key === pick.value);
    const ends = m.bonds.map((degrees) => at(degrees, 68));
    svg.replaceChildren(
      ...ends.map(([x, y]) => s('line', { x1: 120, y1: 105, x2: x, y2: y, class: 'i-bond' })),
      ...m.lone.flatMap((degrees) => [-9, 9].map((offset) => {
        const [x, y] = at(degrees + offset, 40);
        return s('circle', { cx: x, cy: y, r: 4, class: 'i-electron' });
      })),
      ...ends.map(([x, y]) => ui.atom(m.outer, x, y, 17)),
      ui.atom(m.center, 120, 105, 23));
    ui.readout([
      ['Shape', m.shape],
      ['Bond angle', m.angle],
      ['Electron groups', String(m.bonds.length + m.lone.length)],
      ['Example', ui.chem(m.example)],
    ]);
  });
}
