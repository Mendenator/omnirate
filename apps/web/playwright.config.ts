import { defineConfig } from "@playwright/test";

// P1-17 acceptance: 20 critical flows running in CI. This config targets a
// locally-run `next dev`/`next start` — CI wires webServer once apps/web has
// a working build pipeline (blocked on `npm install`, not yet run in this
// sandbox — see docs/PROGRESS.md).
export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  retries: process.env.CI ? 2 : 0,
  use: {
    baseURL: process.env.OMNIRATE_WEB_URL ?? "http://localhost:3000",
    screenshot: "only-on-failure",
  },
});
