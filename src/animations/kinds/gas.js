// A gas in a cylinder under a piston, following P × V = n × R × T.
// A step gives any three of pressure, volume, temperature and moles; the
// fourth is worked out, so the numbers shown always obey the gas law.
//
// state: { pressure? (atm), volume? (L), temperature? (K), moles?, max_volume (L) }

const R = 0.08206; // L·atm/(mol·K)
const PARTICLES = 24;
const LEFT = 240;
const WIDTH = 160;
const FLOOR = 228;
const TALLEST = 190; // pixels for max_volume

// Fixed scattered positions, so particles keep their place as the volume changes.
const spots = Array.from({ length: PARTICLES }, (_, i) => [((i * 61) % 97) / 97, ((i * 37) % 89) / 89]);
const show = (x) => x.toPrecision(3);

export function solve({ pressure: P, volume: V, temperature: T, moles: n }) {
  if (P == null) P = (n * R * T) / V;
  else if (V == null) V = (n * R * T) / P;
  else if (T == null) T = (P * V) / (n * R);
  else if (n == null) n = (P * V) / (R * T);
  return { P, V, T, n };
}

export default {
  render(state) {
    const { P, V, T, n } = solve(state);
    const height = (V / state.max_volume) * TALLEST;
    const top = FLOOR - height;
    const sprites = [
      { id: 'gas', type: 'rect', class: 'i-gas', x: LEFT, y: top, w: WIDTH, h: height },
      ...spots.map(([fx, fy], i) => ({ id: `p${i}`, type: 'dot', x: LEFT + 8 + fx * (WIDTH - 16), y: top + 7 + fy * Math.max(0, height - 14), r: 3.5 })),
      { id: 'rod', type: 'rect', class: 'i-piston', x: LEFT + WIDTH / 2 - 4, y: 0, w: 8, h: Math.max(0, top - 10) },
      { id: 'piston', type: 'rect', class: 'i-piston', x: LEFT, y: top - 10, w: WIDTH, h: 10 },
      { id: 'wall-left', type: 'rect', class: 'i-wall', x: LEFT - 4, y: 12, w: 4, h: FLOOR - 8 },
      { id: 'wall-right', type: 'rect', class: 'i-wall', x: LEFT + WIDTH, y: 12, w: 4, h: FLOOR - 8 },
      { id: 'floor', type: 'rect', class: 'i-wall', x: LEFT - 4, y: FLOOR, w: WIDTH + 8, h: 4 },
    ];
    const row = (label, value) => `<tr><th>${label}</th><td><span class="i-count">${value}</span></td></tr>`;
    return {
      header: 'P × V = n × R × T',
      footer: `<table class="i-tally a-tally">${row('Pressure', `${show(P)} atm`)}${row('Volume', `${show(V)} L`)}${row('Temperature', `${show(T)} K`)}</table>`,
      sprites,
      vars: { P: show(P), V: show(V), T: show(T), n: show(n), PV: show(P * V), VT: show(V / T) },
    };
  },
};
