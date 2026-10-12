import { parse } from 'smol-toml';

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
    prerequisites: data.prerequisites ?? [],
    exercises: data.exercise ?? [],
  });
}
for (const [path, mod] of Object.entries(lessons)) {
  const node = byId.get(idOf(path));
  if (node) node.Content = mod.Content;
}

// Depth in the prerequisite graph, so foundations list first.
const depth = (node) => 1 + Math.max(0, ...node.prerequisites.filter((p) => byId.has(p)).map((p) => depth(byId.get(p))));

export const nodes = [...byId.values()].sort((a, b) => depth(a) - depth(b) || a.title.localeCompare(b.title));
export const getNode = (id) => byId.get(id);
export const wanted = [...new Set(nodes.flatMap((n) => n.prerequisites))].filter((p) => !byId.has(p)).sort();
export const base = import.meta.env.BASE_URL.replace(/\/$/, '');
export const titleOf = (id) => id.replaceAll('-', ' ');
