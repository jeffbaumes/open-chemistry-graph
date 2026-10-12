import { elementOf } from '../data.js';

const CHOICES = ['H', 'Li', 'C', 'N', 'O', 'F', 'Na', 'Mg', 'Al', 'Si', 'P', 'S', 'Cl', 'K', 'Ca', 'Br'];
const SCALE = 3.2; // largest difference shown on the axis
const X = (difference) => 20 + (Math.min(difference, SCALE) / SCALE) * 240;

export default function (ui, { a = 'H', b = 'Cl' } = {}) {
  const { s } = ui;
  const options = CHOICES.map((symbol) => [symbol, `${elementOf(symbol).name} (${symbol})`]);
  const first = ui.select({ label: 'First atom', options, value: a });
  const second = ui.select({ label: 'Second atom', options, value: b });
  const svg = ui.svg(280, 150, 'Two bonded atoms above a scale of electronegativity difference');

  ui.run(() => {
    const [one, two] = [elementOf(first.value), elementOf(second.value)];
    const [x, y] = [one.electronegativity, two.electronegativity];
    const difference = Math.abs(x - y);
    const metallic = one.kind === 'm' && two.kind === 'm';
    const type = metallic ? 'Metallic: both atoms are metals'
      : difference < 0.5 ? 'Nonpolar covalent'
      : difference <= 1.7 ? 'Polar covalent'
      : 'Ionic';
    const partial = (mine, other) =>
      metallic || difference < 0.5 ? '' : `${difference > 1.7 ? '' : 'δ'}${mine > other ? '−' : '+'}`;

    svg.replaceChildren(
      s('line', { x1: 110, y1: 55, x2: 170, y2: 55, class: 'i-bond' }),
      ui.atom(one.symbol, 100, 55, 26),
      ui.atom(two.symbol, 180, 55, 26),
      s('text', { x: 100, y: 16, class: 'i-text' }, partial(x, y)),
      s('text', { x: 180, y: 16, class: 'i-text' }, partial(y, x)),
      s('line', { x1: X(0), y1: 120, x2: X(SCALE), y2: 120, class: 'i-axis' }),
      ...[0.5, 1.7].map((v) => s('line', { x1: X(v), y1: 112, x2: X(v), y2: 128, class: 'i-axis' })),
      ...[['nonpolar', 0.25], ['polar', 1.1], ['ionic', 2.45]].map(([label, v]) => s('text', { x: X(v), y: 144, class: 'i-text i-small' }, label)),
      s('circle', { cx: X(difference), cy: 120, r: 6, class: 'i-marker' }));
    ui.readout([
      ['Electronegativity', `${one.symbol} ${x.toFixed(2)}, ${two.symbol} ${y.toFixed(2)}`],
      ['Difference', difference.toFixed(2)],
      ['Bond type', type],
    ]);
  });
}
