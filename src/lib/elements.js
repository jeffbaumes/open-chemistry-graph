import fs from 'node:fs';
import path from 'node:path';
import { parse } from 'smol-toml';

// Read from disk (not a Vite import) so astro.config.mjs can use this too.
const data = parse(fs.readFileSync(path.join(process.cwd(), 'conventions/elements.toml'), 'utf8'));

export const masses = data.mass;
export const colors = data.color;
