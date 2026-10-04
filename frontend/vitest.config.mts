import { defineConfig } from 'vitest/config';
import { fileURLToPath } from 'node:url';
export default defineConfig({
  resolve: { alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) } },
  oxc: { jsx: { runtime: 'automatic' } },
  test: { environment: 'jsdom', setupFiles: ['./tests/setup.ts'], pool: 'threads', maxWorkers: 1, testTimeout: 12000 },
});

