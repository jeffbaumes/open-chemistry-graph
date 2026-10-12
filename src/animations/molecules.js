import { parse } from 'smol-toml';
import raw from '../../conventions/molecules.toml?raw';

const layouts = parse(raw).layout;

/** Atoms of a molecule as [symbol, x, y] in atom radii. Unknown formulas become a row. */
export function layoutOf(formula, parseFormula) {
  if (layouts[formula]) return layouts[formula];
  const atoms = Object.entries(parseFormula(formula)).flatMap(([symbol, n]) => Array(n).fill(symbol));
  return atoms.map((symbol, i) => [symbol, (i - (atoms.length - 1) / 2) * 1.7, 0]);
}
