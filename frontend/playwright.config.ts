import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright config — intentionally minimal.
 *
 * Purpose: catch a broken `/upi-shield` page module after we refactor it.
 * We don't run the dev server automatically (CI is offline / network-restricted
 * on this machine). Run `npm run dev` in another terminal, then `npm run test:e2e`.
 *
 * Tests live under `./tests/`.
 */
export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: [["list"]],
  timeout: 30_000,
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000",
    trace: "off",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});