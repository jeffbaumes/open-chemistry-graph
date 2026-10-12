// Energy levels in kJ, drawn one pixel per kJ.
const LEVELS = { exo: { reactants: 50, products: 20 }, endo: { reactants: 20, products: 40 } };
const CATALYST_FACTOR = 0.6;
const Y = (energy) => 185 - energy;

const curve = (start, peak, end) =>
  `M20 ${Y(start)} H70 C110 ${Y(start)} 120 ${Y(peak)} 150 ${Y(peak)} C180 ${Y(peak)} 190 ${Y(end)} 230 ${Y(end)} H280`;

export default function (ui, { catalyst = false } = {}) {
  const { s } = ui;
  const type = ui.select({ label: 'Reaction', options: [['exo', 'Exothermic'], ['endo', 'Endothermic']] });
  const barrier = ui.slider({ label: 'Activation energy', min: 40, max: 100, step: 5, value: 70, unit: 'kJ' });
  const added = catalyst ? ui.select({ label: 'Catalyst', options: [['no', 'None'], ['yes', 'Added']] }) : { value: 'no' };
  const svg = ui.svg(300, 200, 'Energy of the reaction as it goes from reactants to products');

  ui.run(() => {
    const { reactants, products } = LEVELS[type.value];
    const catalyzed = added.value === 'yes';
    const ea = catalyzed ? barrier.value * CATALYST_FACTOR : barrier.value;
    const change = products - reactants;
    svg.replaceChildren(
      catalyzed && s('path', { d: curve(reactants, reactants + barrier.value, products), class: 'i-curve-ghost' }),
      s('path', { d: curve(reactants, reactants + ea, products), class: 'i-curve' }),
      s('line', { x1: 150, y1: Y(reactants), x2: 150, y2: Y(reactants + ea), class: 'i-measure' }),
      s('line', { x1: 70, y1: Y(reactants), x2: 150, y2: Y(reactants), class: 'i-measure' }),
      s('text', { x: 45, y: Y(reactants) + 18, class: 'i-text i-small' }, 'Reactants'),
      s('text', { x: 255, y: Y(products) + 18, class: 'i-text i-small' }, 'Products'),
      s('text', { x: 150, y: Y(reactants + barrier.value) - 8, class: 'i-text i-small' }, 'Activation energy'));
    ui.readout([
      ['Activation energy', `${ea} kJ${catalyzed ? `, lowered from ${barrier.value} kJ` : ''}`],
      ['ΔH', `${change > 0 ? '+' : '−'}${Math.abs(change)} kJ, heat ${change > 0 ? 'absorbed' : 'released'}`],
      ['Products are', `${change > 0 ? 'higher' : 'lower'} in energy than the reactants`],
    ]);
  });
}
