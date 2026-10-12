// A radioactive sample as 64 atoms, half of the remainder fading with each
// half-life. A step says only how many half-lives have passed; the time,
// fraction and mass remaining are worked out.
//
// scene: { isotope, half_life, unit, amount? (grams) }   step: { half_lives }

const SIDE = 8;
const TOTAL = SIDE * SIDE;
const GAP = 27;
// A fixed shuffle, so the same atoms stay decayed as time moves forward.
const rank = Array.from({ length: TOTAL }, (_, i) => (i * 37 + 11) % TOTAL);

export default {
  render(state) {
    const passed = state.half_lives;
    const remaining = TOTAL / 2 ** passed;
    const x0 = 320 - (GAP * (SIDE - 1)) / 2;
    const y0 = 120 - (GAP * (SIDE - 1)) / 2;
    const sprites = rank.map((r, i) => ({ id: `atom${i}`, type: 'dot', x: x0 + (i % SIDE) * GAP, y: y0 + Math.floor(i / SIDE) * GAP, r: 9, dim: r >= remaining }));

    const fraction = passed === 0 ? '1' : `1/${2 ** passed}`;
    const elapsed = passed * state.half_life;
    const mass = state.amount == null ? null : (state.amount / 2 ** passed).toPrecision(3);
    const row = (label, value) => `<tr><th>${label}</th><td><span class="i-count">${value}</span></td></tr>`;
    return {
      header: `${state.isotope}: half-life ${state.half_life} ${state.unit}`,
      footer: `<table class="i-tally a-tally">${row('Time elapsed', `${elapsed} ${state.unit}`)}${row('Fraction remaining', fraction)}${mass ? row('Mass remaining', `${mass} g`) : ''}</table>`,
      sprites,
      vars: { half_lives: passed, elapsed, fraction, remaining, total: TOTAL, ...(mass ? { mass } : {}) },
    };
  },
};
