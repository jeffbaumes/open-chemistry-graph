import { parse } from 'smol-toml';
import unitsRaw from '../../conventions/units.toml?raw';

const tomls = import.meta.glob('/nodes/*/node.toml', { query: '?raw', import: 'default', eager: true });
const lessons = import.meta.glob('/nodes/*/lesson.md', { eager: true });

const idOf = (path) => path.split('/').at(-2);

const byId = new Map();
for (const [path, raw] of Object.entries(tomls)) {
  const data = parse(raw);
  byId.set(idOf(path), {
    id: idOf(path),
    title: data.title,
    summary: data.summary,
    unit: data.unit,
    video: data.video ?? false,
    prerequisites: data.prerequisites ?? [],
    interactives: data.interactive ?? [],
    exercises: data.exercise ?? [],
  });
}
for (const [path, mod] of Object.entries(lessons)) {
  const node = byId.get(idOf(path));
  if (node) node.Content = mod.Content;
}

// Depth in the prerequisite graph, so foundations list first.
const depths = new Map();
function depth(node) {
  if (!depths.has(node.id)) {
    depths.set(node.id, 1 + Math.max(0, ...node.prerequisites.filter((p) => byId.has(p)).map((p) => depth(byId.get(p)))));
  }
  return depths.get(node.id);
}

export const nodes = [...byId.values()].sort((a, b) => depth(a) - depth(b) || a.title.localeCompare(b.title));
export const getNode = (id) => byId.get(id);
export const wanted = [...new Set(nodes.flatMap((n) => n.prerequisites))].filter((p) => !byId.has(p)).sort();
export const base = import.meta.env.BASE_URL.replace(/\/$/, '');
export const titleOf = (id) => id.replaceAll('-', ' ');

/** Units in teaching order, each with its lessons in prerequisite order. */
export const course = parse(unitsRaw)
  .unit.map((unit) => ({ ...unit, nodes: nodes.filter((n) => n.unit === unit.id) }))
  .filter((unit) => unit.nodes.length > 0);

const sequence = course.flatMap((unit) => unit.nodes);
export function neighbors(id) {
  const i = sequence.findIndex((n) => n.id === id);
  return { previous: sequence[i - 1], next: sequence[i + 1] };
}
