// A marker on the pH scale, with the ion concentrations that go with it.
//
// state: { ph } (0 to 14)

const LEFT = 60;
const WIDTH = 520;
const X = (ph) => LEFT + (ph / 14) * WIDTH;

// 10^-p as "3.2 × 10^-4", written the plain way so captions typeset it.
function concentration(p) {
  const [mantissa, power] = (10 ** -p).toExponential(1).split('e');
  return `${mantissa} × 10^${Number(power)}`;
}

export default {
  render(state, ui) {
    const ph = state.ph;
    const kind = ph < 7 ? 'acidic' : ph > 7 ? 'basic' : 'neutral';
    const row = (label, value) => `<tr><th>${label}</th><td><span class="i-count">${value}</span></td></tr>`;
    const label = (id, text, at, y, size = 21) => ({ id, type: 'text', text, x: X(at), y, size });
    return {
      header: `pH ${ph}`,
      footer: `<table class="i-tally a-tally">${row('[H<sup>+</sup>]', `${ui.chem(concentration(ph))} M`)}${row('[OH<sup>−</sup>]', `${ui.chem(concentration(14 - ph))} M`)}${row('Solution', kind)}</table>`,
      sprites: [
        { id: 'axis', type: 'rect', class: 'i-piston', x: LEFT, y: 128, w: WIDTH, h: 4 },
        ...[0, 7, 14].map((tick) => ({ id: `tick${tick}`, type: 'rect', class: 'i-piston', x: X(tick) - 1, y: 118, w: 2, h: 24 })),
        ...[0, 7, 14].map((tick) => label(`n${tick}`, String(tick), tick, 164, 23)),
        label('acid', 'acidic', 3, 92), label('neutral', 'neutral', 7, 92), label('base', 'basic', 11, 92),
        { id: 'marker', type: 'dot', class: 'i-marker', x: X(ph), y: 130, r: 11 },
      ],
      vars: { ph, H: concentration(ph), OH: concentration(14 - ph), kind },
    };
  },
};
