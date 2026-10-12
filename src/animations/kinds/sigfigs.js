// A number with its significant digits picked out.
//
// state: { number } (a string, so trailing zeros are kept)

export function significant(text) {
  const chars = [...text];
  const hasPoint = text.includes('.');
  const first = chars.findIndex((c) => c >= '1' && c <= '9');
  // Trailing zeros count only when the number has a decimal point.
  const last = chars.findLastIndex((c) => c !== '.' && (hasPoint || c !== '0'));
  return chars.map((c, i) => c !== '.' && first !== -1 && i >= first && i <= last);
}

export default {
  render(state) {
    const chars = [...state.number];
    const flags = significant(state.number);
    const spacing = 34;
    const x0 = 320 - (spacing * (chars.length - 1)) / 2;
    const count = flags.filter(Boolean).length;
    return {
      footer: `<table class="i-tally a-tally"><tr><th>Significant figures</th><td><span class="i-count">${count}</span></td></tr></table>`,
      sprites: chars.map((c, i) => ({ id: `${state.number}-${i}`, type: 'text', class: 'a-digit', text: c, x: x0 + i * spacing, y: 120, size: 54, dim: !flags[i] && c !== '.' })),
      vars: { number: state.number, count, point: state.number.includes('.') ? 'a' : 'no' },
    };
  },
};
