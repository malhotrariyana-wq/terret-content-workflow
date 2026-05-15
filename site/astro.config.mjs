import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://terret-content-workflow.vercel.app',
  integrations: [sitemap()],
});