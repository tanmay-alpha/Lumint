const { chromium } = require("playwright");

const BASE = process.env.BASE_URL || "http://localhost:3000";

async function verify() {
  const browser = await chromium.launch();
  const page = await browser.newPage({
    viewport: { width: 1440, height: 900 },
  });

  console.log(`Using BASE_URL=${BASE}`);

  console.log("=== TEST 1: Homepage hero with globe ===");
  await page.goto(BASE);
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout; // let globe initialize
  await page.screenshot({
    path: "verify-1-homepage.png",
    fullPage: false,
  });
  console.log("Screenshot saved: verify-1-homepage.png");

  // Check for purple (should be NONE)
  const purpleElements = await page
    .locator('[class*="purple"], [class*="violet"], [class*="fuchsia"]')
    .count();
  console.log(`Purple elements found: ${purpleElements} (should be 0)`);

  // Check for Launch Platform buttons (should be 0)
  const launchButtons = await page.locator("text=Launch Platform").count();
  console.log(`"Launch Platform" buttons: ${launchButtons} (should be 0)`);

  // Check for the new buttons
  const launchDemo = await page.locator("text=Launch Demo").count();
  const tryItLive = await page.locator("text=Try It Live").count();
  const viewOnGitHub = await page.locator("text=View on GitHub").count();
  console.log(
    `"Launch Demo" buttons: ${launchDemo}, "Try It Live": ${tryItLive}, "View on GitHub": ${viewOnGitHub}`
  );

  // Check for "Loading Lumint..." (should be 0)
  const loadingText = await page.locator("text=Loading Lumint").count();
  console.log(`"Loading Lumint..." text: ${loadingText} (should be 0)`);

  // Check body background is dark navy
  const bodyBg = await page.evaluate(() => {
    const bg = getComputedStyle(document.body).backgroundColor;
    return bg;
  });
  console.log(`Body background: ${bodyBg} (should be dark navy ~rgb(10, 14, 26))`);

  console.log("\n=== TEST 2: Scroll to modality cards, hover for tilt ===");
  await page.evaluate(() => window.scrollTo(0, 1200));
  await page.waitForTimeout(800);
  await page.screenshot({ path: "verify-2-modality-cards.png" });

  // Try to hover the first card and screenshot
  const firstCard = page
    .locator('[class*="rounded-2xl"][class*="border"]')
    .first();
  if ((await firstCard.count()) > 0) {
    const box = await firstCard.boundingBox();
    if (box) {
      await page.mouse.move(box.x + box.width * 0.7, box.y + box.height * 0.3);
      await page.waitForTimeout(500);
      await page.screenshot({ path: "verify-3-card-hover.png" });
      console.log("Card hover screenshot saved");
    }
  }

  console.log("\n=== TEST 3: Dashboard ===");
  await page.goto(`${BASE}/dashboard`);
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout;
  await page.screenshot({ path: "verify-4-dashboard.png", fullPage: false });

  // Check sidebar for purple
  const sidebarPurple = await page
    .locator('aside [class*="purple"], aside [class*="violet"]')
    .count();
  console.log(`Sidebar purple elements: ${sidebarPurple} (should be 0)`);

  console.log("\n=== TEST 4: UPI Shield page ===");
  await page.goto(`${BASE}/upi-shield`);
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout;
  await page.screenshot({ path: "verify-5-upi-shield.png", fullPage: false });

  console.log("\n=== TEST 5: Settings page ===");
  await page.goto(`${BASE}/settings`);
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout;
  await page.screenshot({ path: "verify-6-settings.png", fullPage: false });

  console.log("\n=== TEST 6: Mobile view ===");
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto(BASE);
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout;
  await page.screenshot({ path: "verify-7-mobile.png", fullPage: false });

  await browser.close();
  console.log("\n=== All verifications complete ===");
  console.log("Screenshots saved in frontend/verify-*.png");
}

verify().catch((err) => {
  console.error("Verification failed:", err);
  process.exit(1);
});
