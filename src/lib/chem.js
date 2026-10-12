import { masses } from './elements.js';

// Authors write chemistry plainly ("2 H2 + O2 -> 2 H2O"); these helpers find
// the formulas so templates can typeset them the same way everywhere.

const FORMULA = /(?<![A-Za-z])(?:[A-Z][a-z]?\d*|\((?:[A-Z][a-z]?\d*)+\)\d*)+(?![A-Za-z0-9])/g;

// Needs a subscript to be worth typesetting, and only real element symbols,
// so "B12" or "Q3" in ordinary prose are left alone.
const isFormula = (s) => /\d/.test(s) && s.match(/[A-Z][a-z]?/g).every((el) => el in masses);

/** "36 g of H2O" -> ["36 g of ", { formula: "H2O" }] */
export function segments(text) {
  const out = [];
  let last = 0;
  for (const m of text.matchAll(FORMULA)) {
    if (!isFormula(m[0])) continue;
    if (m.index > last) out.push(text.slice(last, m.index));
    out.push({ formula: m[0] });
    last = m.index + m[0].length;
  }
  if (last < text.length) out.push(text.slice(last));
  return out.map((s) => (typeof s === 'string' ? s.replaceAll('->', '→') : s));
}

/** "Ca(OH)2" -> ["Ca(OH)", { sub: "2" }] */
export const formulaParts = (formula) =>
  [...formula.matchAll(/(\d+)|(\D+)/g)].map(([, num, other]) => (num ? { sub: num } : other));

const escape = (s) => s.replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);

/** Typeset a plain string (exercise prompt, summary) as HTML. */
export const toHtml = (text) =>
  segments(text)
    .map((s) =>
      typeof s === 'string'
        ? escape(s)
        : `<span class="formula">${formulaParts(s.formula).map((p) => (typeof p === 'string' ? p : `<sub>${p.sub}</sub>`)).join('')}</span>`,
    )
    .join('');
