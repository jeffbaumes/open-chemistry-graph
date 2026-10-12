import { createChem } from './chem-core.js';
import { masses } from './elements.js';

// Build-time typesetting, using the element data on disk.
export const { segments, formulaParts, toHtml, parseFormula } = createChem(masses);
