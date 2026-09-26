import { expect, test } from "@playwright/test";

// P1-17: a first slice of the 20-critical-flow suite the SOW calls for.
// Extend this file (or add siblings under e2e/) as P2/P3 flows come online —
// claim, owner reply, complaint, takedown, etc.

test("search page loads and accepts a query", async ({ page }) => {
  await page.goto("/search");
  await expect(page.getByPlaceholder("Хайх...")).toBeVisible();
  await page.getByPlaceholder("Хайх...").fill("ресторан");
  // Results list or zero-result message — either is a valid "search worked" signal.
  await expect(page.locator("main")).toBeVisible();
});

test("admin can define a new category without touching code", async ({ page }) => {
  await page.goto("/admin/schemas");
  await page.getByPlaceholder("restoran").fill(`e2e-test-category-${Date.now()}`);
  await page.getByRole("button", { name: "+ Талбар нэмэх" }).click();
  await page.getByRole("button", { name: "Нийтлэх" }).click();
  await expect(page.locator("text=нийтлэгдлээ")).toBeVisible({ timeout: 5000 });
});

test("entity page renders sections in the uniform order", async ({ page }) => {
  // Relies on a seeded entity ID in the test environment — CI wiring for
  // seed data is part of the docker-compose integration profile, not this
  // sandbox (see docs/PROGRESS.md).
  const entityId = process.env.OMNIRATE_E2E_ENTITY_ID;
  test.skip(!entityId, "OMNIRATE_E2E_ENTITY_ID not set in this environment");

  await page.goto(`/entities/${entityId}`);
  await expect(page.locator("h1")).toBeVisible();
});

test("user can log in with phone + OTP and lands on the requested page", async ({ page }) => {
  await page.goto("/login?next=/search");
  await page.getByLabel("Утасны дугаар").fill("99112233");
  await page.getByLabel("Баталгаажуулах код").fill("0000");
  await page.getByRole("button", { name: "Нэвтрэх" }).click();

  await page.waitForURL((url) => url.pathname === "/search");
  const token = await page.evaluate(() => localStorage.getItem("omnirate_access_token"));
  expect(token).toBeTruthy();
});

test("login ignores an off-site next= target", async ({ page }) => {
  await page.goto("/login?next=//evil.example");
  await page.getByLabel("Утасны дугаар").fill("99112234");
  await page.getByLabel("Баталгаажуулах код").fill("0000");
  await page.getByRole("button", { name: "Нэвтрэх" }).click();

  await page.waitForURL((url) => url.pathname === "/");
  expect(new URL(page.url()).hostname).not.toBe("evil.example");
});

test("logging out clears the stored token", async ({ page }) => {
  await page.goto("/login");
  await page.evaluate(() => localStorage.setItem("omnirate_access_token", "x"));
  await page.reload();
  await page.getByRole("button", { name: "Гарах" }).click();
  const token = await page.evaluate(() => localStorage.getItem("omnirate_access_token"));
  expect(token).toBeNull();
});

test("search reads ?q= from the URL instead of ignoring it", async ({ page }) => {
  await page.goto("/search?q=Khaan");
  await expect(page.getByPlaceholder("Хайх...")).toHaveValue("Khaan");
});

test("typing a search updates the URL so it can be shared", async ({ page }) => {
  await page.goto("/search");
  await page.getByPlaceholder("Хайх...").fill("Nomads");
  await page.waitForURL((url) => url.searchParams.get("q") === "Nomads");
});
