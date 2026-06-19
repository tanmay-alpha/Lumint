import { test, expect } from "@playwright/test";

/**
 * Smoke test for /upi-shield.
 *
 * Purpose: catch a broken module after we split page.tsx into feature
 * components. Deliberately tiny — just navigation + a few anchor assertions
 * that depend on the page module successfully importing and rendering.
 *
 * Run with:
 *   npm run dev   # in another terminal
 *   npm run test:e2e
 */

test("upi-shield page renders without error", async ({ page }) => {
  const consoleErrors: string[] = [];
  const pageErrors: string[] = [];

  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });
  page.on("pageerror", (err) => {
    pageErrors.push(err.message);
  });

  await page.goto("/upi-shield", { waitUntil: "domcontentloaded" });

  // Header anchor — only present if the page module loaded.
  await expect(
    page.getByRole("heading", { name: /UPI Shield/i, level: 1 })
  ).toBeVisible();

  // Upload section anchor — proves HeroPanel + UploaderPanel are wired up.
  await expect(
    page.getByText(/Upload Payment Screenshot/i)
  ).toBeVisible();

  // Empty-state anchor — proves the right column's ResultsPanel branch renders
  // when there's no result yet.
  await expect(page.getByText(/No analysis yet/i)).toBeVisible();

  // Module errors are the real signal — even if anchors render, a runtime
  // throw during hydration would invalidate the smoke test.
  expect(pageErrors, `pageerror during load: ${pageErrors.join("\n")}`).toEqual([]);
  expect(
    consoleErrors.filter((m) => !/Download the React DevTools/i.test(m)),
    `console errors: ${consoleErrors.join("\n")}`
  ).toEqual([]);
});