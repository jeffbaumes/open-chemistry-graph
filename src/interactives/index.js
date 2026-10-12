import { createUI } from './lib.js';

// Each file in ./kinds is one interactive, loaded only on pages that use it.
const kinds = import.meta.glob('./kinds/*.js');

export function mountAll() {
  for (const figure of document.querySelectorAll('.interactive:not([data-mounted])')) {
    figure.dataset.mounted = '';
    const load = kinds[`./kinds/${figure.dataset.kind}.js`];
    if (!load) continue;
    load().then((kind) => kind.default(createUI(figure.querySelector('.i-body')), JSON.parse(figure.dataset.params)));
  }
}
