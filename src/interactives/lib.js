// Shared toolkit for interactives. Every kind in ./kinds builds its controls,
// drawing and readout through the `ui` object made here, so they all look and
// behave the same. See INTERACTIVES.md.

import { createChem } from '../lib/chem-core.js';
import { masses, colors } from './data.js';

const chem = createChem(masses);
const SVG = 'http://www.w3.org/2000/svg';

function make(ns, tag, attrs, children) {
  const el = ns ? document.createElementNS(ns, tag) : document.createElement(tag);
  for (const [key, value] of Object.entries(attrs ?? {})) {
    if (value === false || value == null) continue;
    if (key === 'html') el.innerHTML = value;
    else if (key.startsWith('on')) el.addEventListener(key.slice(2), value);
    else el.setAttribute(key, value);
  }
  el.append(...children.flat(Infinity).filter((c) => c != null && c !== false));
  return el;
}

/** Create an HTML element: h('p', { class: 'x' }, 'text', child). `html` sets innerHTML. */
export const h = (tag, attrs, ...children) => make(null, tag, attrs, children);
/** Create an SVG element the same way. */
export const s = (tag, attrs, ...children) => make(SVG, tag, attrs, children);

/** The color for an element, from conventions/elements.toml. */
export const colorOf = (symbol) => colors[symbol] ?? colors.default;

/** A number to `sig` significant figures as HTML, in scientific notation when very large or small. */
export function fmt(x, sig = 3) {
  if (!Number.isFinite(x)) return '—';
  if (x === 0) return '0';
  const exp = Math.floor(Math.log10(Math.abs(x)));
  if (exp >= 5 || exp < -3) {
    const [mantissa, power] = x.toExponential(sig - 1).split('e');
    return `${mantissa} × 10<sup>${String(Number(power)).replace('-', '−')}</sup>`;
  }
  return exp >= sig - 1 ? String(Math.round(Number(x.toPrecision(sig)))) : x.toPrecision(sig);
}

/** An atom drawn as a labelled circle in its element's color. */
export function atom(symbol, cx, cy, r = 16) {
  return s('g', {},
    s('circle', { cx, cy, r, fill: colorOf(symbol), class: 'i-atom' }),
    s('text', { x: cx, y: cy, class: 'i-on-color', 'font-size': r * 0.85 }, symbol));
}

export function createUI(root) {
  const view = h('div', { class: 'i-view' });
  const controls = h('div', { class: 'i-controls' });
  const statusLine = h('p', { class: 'i-status', role: 'status' });
  const out = h('dl', { class: 'i-readout', 'aria-live': 'polite' });
  root.replaceChildren(view, controls, statusLine, out);

  let update = () => {};
  const changed = () => update();
  const field = (label, ...parts) =>
    h('label', { class: 'i-field' }, h('span', { class: 'i-label', html: chem.toHtml(label) }), parts);

  return {
    view, h, s, fmt, atom, colorOf,
    chem: chem.toHtml,
    chemText: chem.toText,
    parseFormula: chem.parseFormula,
    molarMass: chem.molarMass,

    /** A range slider. Returns { value } (a number). */
    slider({ label, min, max, step = 1, value = min, unit = '' }) {
      const input = h('input', { type: 'range', min, max, step, value });
      const shown = h('output');
      const show = () => { shown.innerHTML = `${input.value} ${chem.toHtml(unit)}`; };
      input.addEventListener('input', () => { show(); changed(); });
      show();
      controls.append(field(label, input, shown));
      return { get value() { return Number(input.value); } };
    },

    /** Minus and plus buttons around a whole number. Returns { value }. */
    stepper({ label, min = 0, max = 99, value = min }) {
      let current = value;
      const shown = h('output', {}, String(current));
      const set = (next) => {
        current = Math.min(max, Math.max(min, next));
        shown.textContent = current;
        changed();
      };
      const button = (text, delta, name) =>
        h('button', { type: 'button', 'aria-label': `${name} ${label}`, onclick: () => set(current + delta) }, text);
      controls.append(h('div', { class: 'i-field i-stepper', role: 'group', 'aria-label': label },
        h('span', { class: 'i-label', html: chem.toHtml(label) }),
        button('−', -1, 'Decrease'), shown, button('+', 1, 'Increase')));
      return { get value() { return current; } };
    },

    /** A dropdown. Options are strings or [value, label] pairs. Returns { value } (a string). */
    select({ label, options, value }) {
      const input = h('select', { onchange: changed }, options.map((option) => {
        const [key, text] = Array.isArray(option) ? option : [option, option];
        return h('option', { value: key, selected: key === value }, text);
      }));
      controls.append(field(label, input));
      return { get value() { return input.value; } };
    },

    /** A text box. Returns { value } (a string). */
    text({ label, value = '' }) {
      const input = h('input', { type: 'text', value, autocomplete: 'off', oninput: changed });
      controls.append(field(label, input));
      return { get value() { return input.value; } };
    },

    /** Add an SVG drawing area with the given coordinate size and description. */
    svg(width, height, description) {
      const el = s('svg', { viewBox: `0 0 ${width} ${height}`, role: 'img', 'aria-label': description });
      view.append(el);
      return el;
    },

    /** Replace the readout with [label, value] rows. Both may contain HTML. */
    readout(rows) {
      out.replaceChildren(...rows.flatMap(([label, value]) => [h('dt', { html: label }), h('dd', { html: value })]));
    },

    /** Show a one-line message. Pass ok true or false to color it. */
    status(message, ok) {
      statusLine.innerHTML = message;
      statusLine.dataset.ok = ok ?? '';
    },

    /** Register the function that redraws everything, and run it once. */
    run(fn) {
      update = fn;
      fn();
    },
  };
}
