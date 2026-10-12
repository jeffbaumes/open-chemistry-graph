// A worked calculation, revealed one quantity at a time. Each quantity has an
// expression that may use the ones before it, so every number shown, and the
// working that leads to it, is computed here and never typed.
//
// scene: { quantity: [{ name, label, expr, unit, sig?, signed? }] }   step: { show: n }

import { parse } from 'smol-toml';
import constantsRaw from '../../../conventions/constants.toml?raw';
import { tokenize, evaluate } from '../../lib/expr.js';
import { elementOf, valenceOf } from '../../interactives/data.js';

const constants = parse(constantsRaw).value;
const SUPERSCRIPT = '⁰¹²³⁴⁵⁶⁷⁸⁹';
const SYMBOLS = { '*': ' × ', '/': ' ÷ ', '+': ' + ', '-': ' − ', '**': '^', ',': ', ' };

/** A number to `sig` significant figures as plain text, in scientific notation when very large or small. */
export function plain(x, sig = 3) {
  if (x === 0) return '0';
  const exponent = Math.floor(Math.log10(Math.abs(x)));
  let text;
  if (exponent >= 5 || exponent < -3) {
    const [mantissa, power] = x.toExponential(sig - 1).split('e');
    text = `${mantissa} × 10${[...String(Number(power))].map((ch) => (ch === '-' ? '⁻' : SUPERSCRIPT[ch])).join('')}`;
  } else {
    text = exponent >= sig - 1 ? String(Math.round(Number(x.toPrecision(sig)))) : x.toPrecision(sig);
  }
  return text.replace(/^-/, '−');
}

export function solve(state, ui) {
  const functions = { M: ui.molarMass, log10: Math.log10, sqrt: Math.sqrt, min: Math.min, max: Math.max, valence: valenceOf, Z: (symbol) => elementOf(symbol).z };
  const values = {};
  const shown = {};
  const inline = (text) => (/^[−+]/.test(text) ? `(${text})` : text);

  // The expression as a student would write it, with every name replaced by its value.
  function working(expr) {
    const tokens = tokenize(expr);
    const out = [];
    for (let i = 0; i < tokens.length; i++) {
      const token = tokens[i];
      if (token.type === 'name' && tokens[i + 1]?.value === '(') {
        if (['M', 'valence', 'Z'].includes(token.value)) {
          out.push(String(Number(functions[token.value](tokens[i + 2].value).toFixed(3))));
          i += 3; // the name, "(", the argument and ")"
        } else {
          out.push(token.value === 'log10' ? 'log' : token.value);
        }
      } else if (token.type === 'name') {
        out.push(inline(shown[token.value] ?? plain(constants[token.value], 4)));
      } else if (token.type === 'num') {
        out.push(token.text);
      } else {
        out.push(SYMBOLS[token.value] ?? token.value);
      }
    }
    return out.join('').trim();
  }

  return state.quantity.map((q) => {
    const given = /^-?[\d.]+$/.test(q.expr.trim());
    const value = evaluate(q.expr, { names: { ...constants, ...values }, functions });
    let text = given ? q.expr.trim().replace(/^-/, '−') : plain(value, q.sig ?? 3);
    if (q.signed && value > 0) text = `+${text}`;
    const result = { ...q, value, text, working: given ? '' : working(q.expr) };
    values[q.name] = value;
    shown[q.name] = text;
    return result;
  });
}

export default {
  render(state, ui) {
    const all = solve(state, ui);
    const visible = all.slice(0, state.show);
    const unit = (q) => (q.unit ? ` ${ui.chem(q.unit)}` : '');
    const box = (q) => `<div class="i-box" data-key="${q.name}"><strong>${q.text}${unit(q)}</strong><span>${ui.chem(q.label)}</span></div>`;
    const last = visible.at(-1);
    const working = !last ? ''
      : `<p class="a-working">${ui.chem(last.label)} = ${last.working ? `${last.working} = ` : ''}<strong>${last.text}${unit(last)}</strong></p>`;
    return {
      footer: `<div class="i-chain">${visible.map(box).join('<span class="a-then">→</span>')}</div>${working}`,
      vars: Object.fromEntries(all.map((q) => [q.name, q.text])),
    };
  },
};
