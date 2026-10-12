import { defineConfig } from 'astro/config';
import { unified } from '@astrojs/markdown-remark';
import rehypeLesson from './src/lib/rehype-lesson.js';

// SITE and BASE are set by the GitHub Pages workflow; local dev serves from /.
export default defineConfig({
  site: process.env.SITE,
  base: process.env.BASE || '/',
  markdown: { processor: unified({ rehypePlugins: [rehypeLesson] }) },
});
