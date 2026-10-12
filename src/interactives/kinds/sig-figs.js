export default function (ui, { value = '0.004050' } = {}) {
  const { h } = ui;
  const input = ui.text({ label: 'Number', value });
  const digits = h('p', { class: 'i-digits' });
  ui.view.append(digits);

  ui.run(() => {
    const text = input.value.trim().replace(/^[-+]/, '');
    if (!/^(\d+\.?\d*|\.\d+)$/.test(text)) {
      digits.textContent = 'Type a number such as 0.00420 or 1500';
      ui.readout([]);
      return;
    }
    const chars = [...text];
    const hasPoint = text.includes('.');
    const first = chars.findIndex((c) => c >= '1' && c <= '9');
    // Trailing zeros count only when the number has a decimal point.
    const last = chars.findLastIndex((c) => c !== '.' && (hasPoint || c !== '0'));
    const significant = chars.map((c, i) => c !== '.' && first !== -1 && i >= first && i <= last);
    digits.replaceChildren(...chars.map((c, i) => h('span', { class: c === '.' ? '' : significant[i] ? 'i-sig' : 'i-not-sig' }, c)));
    ui.readout([
      ['Significant figures', String(significant.filter(Boolean).length)],
      ['Decimal point', hasPoint ? 'Present, so trailing zeros count' : 'Absent, so trailing zeros do not count'],
    ]);
  });
}
