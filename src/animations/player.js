// Plays an animation described as data. See ANIMATIONS.md.
//
// A scene is a list of steps. A "kind" turns each step into a picture: a list
// of keyed sprites plus some text. The player never needs to be told how to
// get from one step to the next. It compares the sprites by key and moves
// what stayed, fades in what is new and fades out what is gone.

import { h, s, colorOf, chem } from '../interactives/lib.js';

const kinds = import.meta.glob('./kinds/*.js');
const MOVE_MS = 700;
const ease = (t) => (t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2);
const still = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/** Replace {name} in a caption with a value the kind computed. */
export const fill = (caption, vars = {}) => caption.replace(/\{([\w.]+)\}/g, (whole, name) => vars[name] ?? whole);

// --- Sound: synthesized, very quiet, and only after the viewer presses a button.

let audio;
const context = () => (audio ??= new AudioContext());
const soundOn = () => {
  try { return localStorage.getItem('animation-sound') !== 'off'; } catch { return true; }
};

function swoosh() {
  const ctx = context();
  const now = ctx.currentTime;
  const buffer = ctx.createBuffer(1, ctx.sampleRate * 0.45, ctx.sampleRate);
  buffer.getChannelData(0).forEach((_, i, data) => { data[i] = Math.random() * 2 - 1; });
  const noise = new AudioBufferSourceNode(ctx, { buffer });
  const filter = new BiquadFilterNode(ctx, { type: 'lowpass', frequency: 300 });
  filter.frequency.linearRampToValueAtTime(2600, now + 0.2);
  filter.frequency.linearRampToValueAtTime(300, now + 0.45);
  const gain = new GainNode(ctx, { gain: 0 });
  gain.gain.linearRampToValueAtTime(0.05, now + 0.2);
  gain.gain.linearRampToValueAtTime(0, now + 0.45);
  noise.connect(filter).connect(gain).connect(ctx.destination);
  noise.start();
}

function chime() {
  const ctx = context();
  const now = ctx.currentTime;
  for (const [frequency, level] of [[784, 0.05], [1175, 0.03]]) {
    const tone = new OscillatorNode(ctx, { frequency });
    const gain = new GainNode(ctx, { gain: level });
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 1.2);
    tone.connect(gain).connect(ctx.destination);
    tone.start();
    tone.stop(now + 1.2);
  }
}

/** A barely-there chord while the animation plays. Returns a function that fades it out. */
function pad() {
  const ctx = context();
  const gain = new GainNode(ctx, { gain: 0 });
  gain.gain.linearRampToValueAtTime(0.012, ctx.currentTime + 1.5);
  gain.connect(ctx.destination);
  const tones = [196, 293.66, 392].map((frequency) => {
    const tone = new OscillatorNode(ctx, { frequency });
    tone.connect(gain);
    tone.start();
    return tone;
  });
  return () => {
    gain.gain.cancelScheduledValues(ctx.currentTime);
    gain.gain.linearRampToValueAtTime(0, ctx.currentTime + 0.6);
    tones.forEach((tone) => tone.stop(ctx.currentTime + 0.7));
  };
}

// --- Sprites

function create(sprite) {
  if (sprite.type === 'atom') {
    return s('g', {},
      s('circle', { r: sprite.r, fill: colorOf(sprite.symbol), class: 'i-atom' }),
      s('text', { class: 'i-on-color', 'font-size': sprite.r * 0.85 }, sprite.symbol));
  }
  return s('text', { class: 'i-text a-symbol', style: `font-size:${sprite.size ?? 20}px`, 'dominant-baseline': 'central' }, sprite.text);
}

const place = ({ el, at }) => {
  el.setAttribute('transform', `translate(${at.x} ${at.y})`);
  el.style.opacity = at.opacity;
};

// --- Player

function createPlayer(figure, kind, scene) {
  const { step: steps, ...shared } = scene;
  const ui = { chem: chem.toHtml, parseFormula: chem.parseFormula, colorOf };
  const header = h('p', { class: 'a-header' });
  const svg = s('svg', { viewBox: '0 0 640 240', role: 'img', 'aria-label': scene.title });
  const footer = h('div', { class: 'a-footer' });
  const caption = h('p', { class: 'a-caption', 'aria-live': 'polite' });
  const counter = h('span', { class: 'a-counter' });
  const button = (label, onclick) => h('button', { type: 'button', onclick }, label);
  const back = button('Back', () => { stop(); show(index - 1, true); });
  const play = button('Play', () => (playing ? stop() : start()));
  const next = button('Next', () => { stop(); show(index + 1, true); });
  const sound = button('', () => {
    try { localStorage.setItem('animation-sound', soundOn() ? 'off' : 'on'); } catch { /* private mode */ }
    if (!soundOn()) quiet?.();
    label();
  });
  const label = () => { sound.textContent = soundOn() ? 'Sound on' : 'Sound off'; sound.setAttribute('aria-pressed', String(soundOn())); };
  label();
  figure.querySelector('.a-body').replaceChildren(header, svg, footer, caption,
    h('div', { class: 'a-controls' }, back, play, next, counter, sound));

  const shown = new Map(); // sprite id -> { el, at }
  let index = 0;
  let playing = false;
  let timer;
  let frame;
  let settle; // finishes the transition in progress
  let quiet; // stops the pad
  let wasDone = false;

  function move(sprites, animate) {
    cancelAnimationFrame(frame);
    settle?.();
    const wanted = new Map(sprites.map((sprite) => [sprite.id, sprite]));
    const moves = [];
    let entered = false;
    for (const [id, sprite] of wanted) {
      let item = shown.get(id);
      if (!item) {
        item = { el: create(sprite), at: { x: sprite.x, y: sprite.y + 14, opacity: 0 } };
        shown.set(id, item);
        svg.append(item.el);
        entered = true;
      }
      if (sprite.type === 'atom') {
        item.el.firstChild.setAttribute('r', sprite.r);
        item.el.lastChild.setAttribute('font-size', sprite.r * 0.85);
      }
      moves.push({ item, from: { ...item.at }, to: { x: sprite.x, y: sprite.y, opacity: sprite.dim ? 0.22 : 1 } });
    }
    for (const [id, item] of shown) {
      if (!wanted.has(id)) moves.push({ item, from: { ...item.at }, to: { ...item.at, opacity: 0 }, gone: id });
    }
    const apply = (t) => {
      for (const { item, from, to } of moves) {
        for (const key of ['x', 'y', 'opacity']) item.at[key] = from[key] + (to[key] - from[key]) * t;
        place(item);
      }
    };
    settle = () => {
      settle = null;
      apply(1);
      for (const { item, gone } of moves) {
        if (gone) { item.el.remove(); shown.delete(gone); }
      }
    };
    if (!animate || still) return settle(), entered;
    const began = performance.now();
    const tick = (now) => {
      const t = Math.min(1, (now - began) / MOVE_MS);
      apply(ease(t));
      if (t < 1) frame = requestAnimationFrame(tick);
      else settle?.();
    };
    frame = requestAnimationFrame(tick);
    return entered;
  }

  function show(to, animate) {
    index = Math.max(0, Math.min(steps.length - 1, to));
    const view = kind.render({ ...shared, ...steps[index] }, ui);
    header.innerHTML = view.header ?? '';
    footer.innerHTML = view.footer ?? '';
    caption.innerHTML = chem.toHtml(fill(steps[index].caption, view.vars));
    const entered = move(view.sprites ?? [], animate);
    if (animate && soundOn()) {
      if (entered) swoosh();
      if (view.done && !wasDone) chime();
    }
    wasDone = Boolean(view.done);
    counter.textContent = `${index + 1} / ${steps.length}`;
    back.disabled = index === 0;
    next.disabled = index === steps.length - 1;
  }

  // Long enough to read the caption twice.
  const dwell = () => MOVE_MS + Math.max(2600, caption.textContent.length * 60);

  function schedule() {
    timer = setTimeout(() => {
      if (index === steps.length - 1) return stop();
      show(index + 1, true);
      schedule();
    }, dwell());
  }

  function start() {
    playing = true;
    play.textContent = 'Pause';
    if (soundOn()) quiet = pad();
    if (index === steps.length - 1) show(0, true);
    schedule();
  }

  function stop() {
    playing = false;
    play.textContent = 'Play';
    clearTimeout(timer);
    quiet?.();
    quiet = null;
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
