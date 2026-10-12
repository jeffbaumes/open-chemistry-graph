import { segments, formulaParts } from './chem.js';

// Turns a plainly written lesson into textbook layout:
//   - chemical formulas get subscripts, "->" becomes an arrow
//   - "Worked example" and "Common mistake" sections become boxes
//   - a paragraph that is only a bold line becomes a displayed result

const el = (tagName, className, children) => ({
  type: 'element',
  tagName,
  properties: className ? { className: [className] } : {},
  children,
});
const text = (value) => ({ type: 'text', value });

const formulaNode = (formula) =>
  el('span', 'formula', formulaParts(formula).map((p) => (typeof p === 'string' ? text(p) : el('sub', null, [text(p.sub)]))));

const plainText = (node) => node.value ?? (node.children ?? []).map(plainText).join('');

const BOXES = [
  [/^worked example/i, 'example'],
  [/^common mistake/i, 'mistake'],
];
const boxClass = (title) => BOXES.find(([pattern]) => pattern.test(title))?.[1];

function typeset(node) {
  if (!node.children || node.tagName === 'code' || node.tagName === 'pre') return;
  const solo = node.children.filter((c) => c.type !== 'text' || c.value.trim());
  if (node.tagName === 'p' && solo.length === 1 && solo[0].tagName === 'strong') {
    node.properties = { ...node.properties, className: ['result'] };
  }
  node.children = node.children.flatMap((child) => {
    if (child.type !== 'text') {
      typeset(child);
      return [child];
    }
    return segments(child.value).map((s) => (typeof s === 'string' ? text(s) : formulaNode(s.formula)));
  });
}

export default function rehypeLesson() {
  return (tree) => {
    const out = [];
    let box = null;
    for (const child of tree.children) {
      if (child.tagName === 'h2') {
        const className = boxClass(plainText(child));
        box = className ? el('section', className, []) : null;
        if (box) out.push(box);
      }
      (box ? box.children : out).push(child);
    }
    tree.children = out;
    typeset(tree);
  };
}
