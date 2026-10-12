import { parse } from 'smol-toml';
import elementsRaw from '../../conventions/elements.toml?raw';
import periodicRaw from '../../conventions/periodic.toml?raw';

// The same convention files the validator and the build read, bundled for the browser.
export const { mass: masses, color: colors } = parse(elementsRaw);

const periodOf = (z) => (z <= 2 ? 1 : z <= 10 ? 2 : z <= 18 ? 3 : 4);
function groupOf(z) {
  if (z === 1) return 1;
  if (z === 2) return 18;
  if (z > 18) return z - 18;
  const place = z <= 10 ? z - 2 : z - 10;
  return place > 2 ? place + 10 : place;
}

/** Elements 1 to 36, in order. elements[z - 1] is the element with atomic number z. */
export const elements = parse(periodicRaw).elements.map(
  ([symbol, name, kind, radius, ionization, electronegativity], i) => ({
    z: i + 1,
    symbol,
    name,
    kind,
    radius,
    ionization,
    electronegativity,
    group: groupOf(i + 1),
    period: periodOf(i + 1),
  }),
);

export const elementOf = (symbol) => elements.find((el) => el.symbol === symbol);

/** Valence electrons of a main-group element. */
export function valenceOf(symbol) {
  const { z, group } = elementOf(symbol);
  return z <= 2 ? z : group <= 2 ? group : group - 10;
}
