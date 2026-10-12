// Plays an animation described as data. See ANIMATIONS.md.
//
// A scene is a list of steps. A "kind" turns each step into a picture: a list
// of keyed sprites plus some text. The player never needs to be told how to
// get from one step to the next. It compares the sprites by key and moves
// what stayed, fades in what is new and fades out what is gone.
//
// Animations are silent, and the viewer steps through them at their own pace.

import { h, s, colorOf, chem } from '../interactives/lib.js';

const kinds = import.meta.glob('./kinds/*.js');
const MOVE_MS = 700;
const DIM = 0.22;
const ease = (t) => (t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2);
const still = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/** Replace {name} in a caption with a value the kind computed. */
export const fill = (caption, vars = {}) => caption.replace(/\{([\w.]+)\}/g, (whole, name) => vars[name] ?? whole);

// --- Sprites: how each type is created and positioned.

const translate = (el, at) => el.setAttribute('transform', `translate(${at.x} ${at.y})`);
const circle = (el, at) => { el.setAttribute('cx', at.x); el.setAttribute('cy', at.y); el.setAttribute('r', Math.max(0, at.r)); };

const TYPES = {
  // An atom in its element's color, labelled with its symbol.
  atom: {
    create: (sprite) => s('g', {},
      s('circle', { fill: colorOf(sprite.symbol), class: 'i-atom' }),
      s('text', { class: 'i-on-color' }, sprite.label ?? sprite.symbol)),
    place: (el, at) => {
      translate(el, at);
      el.firstChild.setAttribute('r', Math.max(0, at.r));
      el.lastChild.setAttribute('font-size', at.r * 0.85);
    },
    rises: true,
  },
  // A small filled circle: an electron, a gas particle, one atom of many.
  dot: { create: (sprite) => s('circle', { class: sprite.class ?? 'i-particle' }), place: circle, rises: true },
  // An outlined circle, such as an electron shell.
  ring: { create: (sprite) => s('circle', { class: sprite.class ?? 'i-shell' }), place: circle },
  // A rectangle from its top-left corner.
  rect: {
    create: (sprite) => s('rect', { class: sprite.class }),
    place: (el, at) => {
      el.setAttribute('x', at.x);
      el.setAttribute('y', at.y);
      el.setAttribute('width', Math.max(0, at.w));
      el.setAttribute('height', Math.max(0, at.h));
    },
  },
  // A symbol or short label.
  text: {
    create: (sprite) => s('text', { class: `i-text ${sprite.class ?? 'a-symbol'}`, style: `font-size:${sprite.size ?? 20}px`, 'dominant-baseline': 'central' }, sprite.text),
    place: translate,
    rises: true,
  },
  // An energy curve from level a, over a peak at b, down to level c (all in y pixels).
  curve: {
    create: () => s('path', { class: 'i-curve' }),
    place: (el, at) => {
      translate(el, { x: at.x, y: 0 });
      el.setAttribute('d', `M0 ${at.a} H80 C130 ${at.a} 140 ${at.b} 190 ${at.b} C240 ${at.b} 250 ${at.c} 300 ${at.c} H380`);
    },
  },
};

const KEYS = ['x', 'y', 'r', 'w', 'h', 'a', 'b', 'c', 'opacity'];
const target = (sprite) => ({
  x: sprite.x, y: sprite.y ?? 0, r: sprite.r ?? 0, w: sprite.w ?? 0, h: sprite.h ?? 0,
  a: sprite.a ?? 0, b: sprite.b ?? 0, c: sprite.c ?? 0, opacity: sprite.dim ? DIM : 1,
});

// --- Player

function createPlayer(figure, kind, scene) {
  const { step: steps, ...shared } = scene;
  const ui = { chem: chem.toHtml, parseFormula: chem.parseFormula, molarMass: chem.molarMass, colorOf };
  const header = h('p', { class: 'a-header' });
  const svg = s('svg', { viewBox: '0 0 640 240', role: 'img', 'aria-label': scene.title });
  const footer = h('div', { class: 'a-footer' });
  const caption = h('p', { class: 'a-caption', 'aria-live': 'polite' });
  const counter = h('span', { class: 'a-counter' });
  const button = (label, onclick) => h('button', { type: 'button', onclick }, label);
  const previous = button('Previous', () => show(index - 1));
  const next = button('Next', () => show(index + 1));
  const restart = button('Restart', () => show(0));
  figure.querySelector('.a-body').replaceChildren(header, svg, footer, caption,
    h('div', { class: 'a-controls' }, previous, next, counter, restart));

  const shown = new Map(); // sprite id -> { el, type, at }
  let keys = new Set(); // data-key values in the text of the step before
  let index = 0;
  let frame;
  let settle; // finishes the transition in progress

  function move(sprites, animate) {
    cancelAnimationFrame(frame);
    settle?.();
    const wanted = new Map(sprites.map((sprite) => [sprite.id, sprite]));
    const moves = [];
    for (const [id, sprite] of wanted) {
      const to = target(sprite);
      let item = shown.get(id);
      if (!item) {
        const type = TYPES[sprite.type];
        item = { el: type.create(sprite), type, at: { ...to, y: to.y + (type.rises ? 14 : 0), opacity: 0 } };
        shown.set(id, item);
        svg.append(item.el);
      }
      moves.push({ item, from: { ...item.at }, to });
    }
    for (const [id, item] of shown) {
      if (!wanted.has(id)) moves.push({ item, from: { ...item.at }, to: { ...item.at, opacity: 0 }, gone: id });
    }
    const apply = (t) => {
      for (const { item, from, to } of moves) {
        for (const key of KEYS) item.at[key] = from[key] + (to[key] - from[key]) * t;
        item.type.place(item.el, item.at);
        item.el.style.opacity = item.at.opacity;
      }
    };
    settle = () => {
      settle = null;
      apply(1);
      for (const { item, gone } of moves) {
        if (gone) { item.el.remove(); shown.delete(gone); }
      }
    };
    if (!animate || still) return settle();
    apply(0); // place new sprites at once, before the first frame
    const began = performance.now();
    const tick = (now) => {
      const t = Math.min(1, (now - began) / MOVE_MS);
      apply(ease(t));
      if (t < 1) frame = requestAnimationFrame(tick);
      else settle?.();
    };
    frame = requestAnimationFrame(tick);
  }

  function show(to, animate = true) {
    index = Math.max(0, Math.min(steps.length - 1, to));
    const view = kind.render({ ...shared, ...steps[index] }, ui);
    header.innerHTML = view.header ?? '';
    footer.innerHTML = view.footer ?? '';
    caption.innerHTML = chem.toHtml(fill(steps[index].caption, view.vars));
    // The same idea as for sprites: anything keyed that was not there before fades in.
    const keyed = [...figure.querySelectorAll('[data-key]')];
    if (animate) keyed.filter((el) => !keys.has(el.dataset.key)).forEach((el) => el.classList.add('a-new'));
    keys = new Set(keyed.map((el) => el.dataset.key));
    svg.style.display = view.sprites?.length ? '' : 'none';
    move(view.sprites ?? [], animate);
    counter.textContent = `${index + 1} / ${steps.length}`;
    previous.disabled = restart.disabled = index === 0;
    next.disabled = index === steps.length - 1;
  }

  show(0, false);
}

export function mountAnimations() {
  for (const figure of document.querySelectorAll('.animation:not([data-mounted])')) {
    figure.dataset.mounted = '';
    const scene = JSON.parse(figure.dataset.scene);
    kinds[`./kinds/${scene.kind}.js`]?.().then((kind) => createPlayer(figure, kind.default, scene));
  }
}
