// A reversible reaction A <-> B settling into equilibrium. Each round, a
// fixed fraction of the reactants turns into products and a fixed fraction of
// the products turns back. The amounts and rates are simulated, not typed.
//
// scene: { forward, reverse, reactants, products?, disturb? }
// step: { rounds, added?, more? }
//   rounds: rounds run so far.  added: then add `disturb` extra reactant.
//   more: then run this many further rounds.

export function simulate(state) {
  let a = state.reactants;
  let b = state.products ?? 0;
  const run = (rounds) => {
    for (let i = 0; i < rounds; i++) {
      const net = state.forward * a - state.reverse * b;
      a -= net;
      b += net;
    }
  };
  run(state.rounds);
  if (state.added) {
    a += state.disturb;
    run(state.more ?? 0);
  }
  return { a, b, forward: state.forward * a, reverse: state.reverse * b };
}

const FLOOR = 202;
const SCALE = 1.25;

export default {
  render(state) {
    const { a, b, forward, reverse } = simulate(state);
    const bar = (id, x, amount) => ({ id, type: 'rect', class: 'i-solution', x, y: FLOOR - amount * SCALE, w: 110, h: amount * SCALE });
    const row = (label, value) => `<tr><th>${label}</th><td><span class="i-count">${value}</span></td></tr>`;
    const equal = Math.abs(forward - reverse) < 0.05;
    return {
      footer: `<table class="i-tally a-tally"><tbody class="${equal ? 'i-ok' : 'i-off'}">${row('Forward rate', forward.toFixed(1))}${row('Reverse rate', reverse.toFixed(1))}</tbody></table>`,
      sprites: [
        bar('reactants', 170, a),
        bar('products', 360, b),
        { id: 'floor', type: 'rect', class: 'i-wall', x: 150, y: FLOOR, w: 340, h: 2 },
        { id: 'label-a', type: 'text', text: 'Reactants', x: 225, y: 224, size: 21 },
        { id: 'label-b', type: 'text', text: 'Products', x: 415, y: 224, size: 21 },
        { id: 'arrows', type: 'text', text: '⇌', x: 320, y: 120, size: 30 },
      ],
      vars: { A: Math.round(a), B: Math.round(b), forward: forward.toFixed(1), reverse: reverse.toFixed(1) },
    };
  },
};
