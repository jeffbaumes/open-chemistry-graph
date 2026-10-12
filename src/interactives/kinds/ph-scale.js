// Approximate pH of familiar substances.
const EXAMPLES = [
  [1, 'stomach acid'], [2, 'lemon juice'], [3, 'vinegar'], [5, 'black coffee'], [7, 'pure water'],
  [8, 'sea water'], [9, 'baking soda solution'], [11, 'household ammonia'], [13, 'bleach'], [14, 'drain cleaner'],
];

export default function (ui, { ph = 7 } = {}) {
  const { h } = ui;
  const value = ui.slider({ label: 'pH', min: 0, max: 14, step: 0.5, value: ph });
  const marker = h('div', { class: 'i-ph-marker' });
  ui.view.append(
    h('div', { class: 'i-ph' }, marker),
    h('div', { class: 'i-ph-ends' }, h('span', {}, '0 · acidic'), h('span', {}, '7 · neutral'), h('span', {}, 'basic · 14')));

  ui.run(() => {
    const p = value.value;
    marker.style.left = `${(p / 14) * 100}%`;
    const nearest = EXAMPLES.reduce((a, b) => (Math.abs(b[0] - p) < Math.abs(a[0] - p) ? b : a));
    ui.readout([
      ['[H<sup>+</sup>]', `${ui.fmt(10 ** -p, 2)} M`],
      ['[OH<sup>−</sup>]', `${ui.fmt(10 ** (p - 14), 2)} M`],
      ['Solution', p < 7 ? 'Acidic' : p > 7 ? 'Basic' : 'Neutral'],
      ['Similar to', nearest[1]],
    ]);
  });
}
