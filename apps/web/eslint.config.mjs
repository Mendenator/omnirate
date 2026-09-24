import nextCoreWebVitals from "eslint-config-next/core-web-vitals";
import nextTypescript from "eslint-config-next/typescript";

// eslint-config-next 16 ships native flat config (plain arrays) — the
// FlatCompat bridge this used under eslint-config-next 15/ESLint 9 no
// longer applies (eslint-config-next 16 doesn't even ship the legacy
// eslintrc-style entry points FlatCompat needs).
const eslintConfig = [
  ...nextCoreWebVitals,
  ...nextTypescript,
  {
    ignores: [
      ".next/**",
      "node_modules/**",
      "playwright-report/**",
      "test-results/**",
      "next-env.d.ts",
    ],
  },
];

export default eslintConfig;
