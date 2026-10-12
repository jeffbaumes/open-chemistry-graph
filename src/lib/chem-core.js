// Chemistry typesetting and formula arithmetic. Pure functions with no file or
// DOM access, so the build (Node) and the interactives (browser) share them.
//
// Authors write plainly and these helpers find what to typeset:
//   H2O, Ca(OH)2      formulas get subscripts
//   Na^+, 10^-7, 3s^2 "^" starts a superscript
//   V_1, E_a          "_" starts a subscript
//   ->, <->           arrows

const FORMULA = /(?<![A-Za-z])(?:[A-Z][a-z]?\d*|\((?:[A-Z][a-z]?\d*)+\)\d*)+(?![A-Za-z0-9])/g;
const SCRIPT = /\^(\d*[+-](?!\d)|-?(?:\d+|[a-z]))|(?<=[A-Za-z])_([A-Za-z0-9]+)/g;
const TOKEN = /([A-Z][a-z]?)|(\()|(\))|(\d+)/g;

const escape = (s) => s.replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]);
const arrows = (s) => s.replaceAll('<->', '⇌').replaceAll('->', '→');

/** "Ca(OH)2" -> ["Ca(OH)", { sub: "2" }] */
export const formulaParts = (formula) =>
  [...formula.matchAll(/(\d+)|(\D+)/g)].map(([, num, other]) => (num ? { sub: num } : other));

/** "Ca(OH)2" -> { Ca: 1, O: 2, H: 2 } */
export function parseFormula(formula) {
  const stack = [{}];
  let last = null;
  for (const [, element, open, close, count] of formula.matchAll(TOKEN)) {
    const top = stack.at(-1);
    if (element) {
      last = { [element]: 1 };
      top[element] = (top[element] ?? 0) + 1;
    } else if (open) {
      stack.push({});
      last = null;
    } else if (close) {
      last = stack.pop();
      for (const [el, n] of Object.entries(last)) stack.at(-1)[el] = (stack.at(-1)[el] ?? 0) + n;
    } else if (last) {
      for (const [el, n] of Object.entries(last)) top[el] += n * (Number(count) - 1);
      last = null;
    }
  }
  return stack[0];
}

export function createChem(masses) {
  // Needs a subscript to be worth typesetting, and only real element symbols,
  // so "B12" or "Q3" in ordinary prose are left alone.
  const isFormula = (s) => /\d/.test(s) && s.match(/[A-Z][a-z]?/g).every((el) => el in masses);

  function scripts(text) {
    const out = [];
    let last = 0;
    for (const m of text.matchAll(SCRIPT)) {
      if (m.index > last) out.push(arrows(text.slice(last, m.index)));
      out.push(m[1] != null ? { sup: m[1].replace('-', '−') } : { sub: m[2] });
      last = m.index + m[0].length;
    }
    if (last < text.length) out.push(arrows(text.slice(last)));
    return out;
  }

  /** Split prose into strings and { formula } / { sup } / { sub } pieces. */
  function segments(text) {
    const out = [];
    let last = 0;
    for (const m of text.matchAll(FORMULA)) {
      if (!isFormula(m[0])) continue;
      out.push(...scripts(text.slice(last, m.index)), { formula: m[0] });
      last = m.index + m[0].length;
    }
    out.push(...scripts(text.slice(last)));
    return out;
  }

  const formulaHtml = (formula) =>
    `<span class="formula">${formulaParts(formula).map((p) => (typeof p === 'string' ? p : `<sub>${p.sub}</sub>`)).join('')}</span>`;

  /** Typeset a plain string as HTML. */
  const toHtml = (text) =>
    segments(String(text))
      .map((s) =>
        typeof s === 'string' ? escape(s)
        : s.formula ? formulaHtml(s.formula)
        : s.sup != null ? `<sup>${s.sup}</sup>`
        : `<sub>${s.sub}</sub>`,
      )
      .join('');

  /** A formula as plain text with Unicode subscripts, for places HTML cannot go. */
  const toText = (formula) => formula.replace(/\d/g, (d) => '₀₁₂₃₄₅₆₇₈₉'[d]);

  const molarMass = (formula) =>
    Object.entries(parseFormula(formula)).reduce((sum, [el, n]) => sum + masses[el] * n, 0);

  return { segments, formulaParts, parseFormula, toHtml, toText, molarMass };
}
