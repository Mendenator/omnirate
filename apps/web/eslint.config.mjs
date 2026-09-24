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
    // eslint-config-next sets settings.react.version: "detect", which makes
    // eslint-plugin-react call context.getFilename() to resolve a basedir
    // for auto-detecting the installed React version. ESLint 10 removed
    // getFilename() from the rule context, so with "detect" left in place
    // every rule that needs the React version (react/display-name,
    // react/prop-types, etc.) crashes with "contextOrFilename.getFilename
    // is not a function" on the first file linted. Pinning the version
    // explicitly skips that detection path entirely — this isn't
    // suppressing anything, it's giving the plugin the answer directly
    // instead of routing through the now-broken auto-detect code path.
    settings: {
      react: {
        version: "19.3.0",
      },
    },
  },
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
