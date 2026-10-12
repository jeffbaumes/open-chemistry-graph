// The energy of a reaction as it goes from reactants, over a barrier, to products.
//
// state: { reactants, products, barrier, catalyst? }  (all in kJ, from 0 to about 200)
// A catalyst lowers the barrier to 60% of its value and changes nothing else.

const CATALYST = 0.6;
const Y = (energy) => 208 - energy * 0.9; // pixels from the top, for an energy in kJ
const LEFT = 130;

export const barrierOf = (state) => state.barrier * (state.catalyst ? CATALYST : 1);

export default {
  render(state) {
    const ea = barrierOf(state);
    const change = state.products - state.reactants;
    const row = (label, value) => `<tr><th>${label}</th><td><span class="i-count">${value}</span></td></tr>`;
    const signed = `${change > 0 ? '+' : '−'}${Math.abs(change)}`;
    return {
      footer: `<table class="i-tally a-tally">${row('Activation energy', `${ea} kJ${state.catalyst ? ' with a catalyst' : ''}`)}${row('ΔH', `${signed} kJ`)}</table>`,
      sprites: [
        { id: 'curve', type: 'curve', x: LEFT, a: Y(state.reactants), b: Y(state.reactants + ea), c: Y(state.products) },
        { id: 'reactants', type: 'text', text: 'Reactants', x: LEFT + 40, y: Y(state.reactants) + 22, size: 21 },
        { id: 'products', type: 'text', text: 'Products', x: LEFT + 340, y: Y(state.products) + 22, size: 21 },
        { id: 'peak', type: 'text', text: 'Activation energy', x: LEFT + 190, y: Y(state.reactants + ea) - 18, size: 21 },
      ],
      vars: { Ea: ea, dH: signed, heat: change > 0 ? 'absorbed' : 'released', type: change > 0 ? 'endothermic' : 'exothermic', size: Math.abs(change) },
    };
  },
};
