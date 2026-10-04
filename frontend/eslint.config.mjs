import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const { FlatCompat } = require('@eslint/eslintrc');
const compat = new FlatCompat({ baseDirectory: import.meta.dirname });
export default [
  { ignores: ['.next/**', 'node_modules/**', 'next-env.d.ts'] },
  ...compat.extends('next/core-web-vitals', 'next/typescript'),
  { rules: { '@typescript-eslint/no-unused-vars': 'off', '@typescript-eslint/no-explicit-any': 'off', '@next/next/no-img-element': 'off' } },
];
