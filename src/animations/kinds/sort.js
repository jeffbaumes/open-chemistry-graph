// Examples sorted into named groups, one or more at a time.
//
// scene: { bins: [label], items: [{ text, bin }] }   step: { placed: n }
// `bin` is the index of the group an item belongs to. Items appear in the
// order listed, as `placed` grows.

export default {
  render(state, ui) {
    const chip = (item, i) => `<span class="i-chip" data-key="item${i}">${ui.chem(item.text)}</span>`;
    const rows = state.bins.map((label, b) => {
      const chips = state.items.map((item, i) => (item.bin === b && i < state.placed ? chip(item, i) : '')).join('');
      return `<div class="a-bin"><strong>${label}</strong><div class="i-chips">${chips}</div></div>`;
    });
    return { footer: `<div class="a-sort">${rows.join('')}</div>`, vars: { placed: state.placed, total: state.items.length } };
  },
};
