import { expect, test } from "@playwright/test";

test("creates a syndicate and registers a broker", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Create", exact: true }).click();
  const passwords = page.locator('input[type="password"]');
  await passwords.nth(0).fill("write-test-password");
  await passwords.nth(1).fill("write-test-password");
  await page.getByRole("button", { name: "Create wallet" }).click();
  await expect(page.getByRole("button", { name: "Lock" })).toBeVisible();

  // Fund the fresh key so it can precharge a deploy.
  await page.locator(".tabs").getByRole("link", { name: "Me", exact: true }).click();
  await page.getByRole("button", { name: "Request devnet REV" }).click();
  await page.waitForTimeout(15_000);

  await page.locator(".tabs").getByRole("link", { name: "Syndicates", exact: true }).click();
  await page.getByRole("link", { name: "Create syndicate" }).click();
  await page.getByLabel("Name").fill("E2E Syndicate");
  await page.getByRole("button", { name: "Create syndicate" }).click();
  await expect(page).toHaveURL(/#\/syndicates$/, { timeout: 120_000 });
  await expect(page.getByRole("heading", { name: "Syndicates" })).toBeVisible();

  await page.locator(".tabs").getByRole("link", { name: "Brokers", exact: true }).click();
  await page.getByRole("link", { name: "Register broker" }).click();
  await page.getByLabel("Name").fill("E2E Broker");
  await page.getByLabel("Licence hash").fill("e2e-licence");
  await page.getByRole("button", { name: "Register broker" }).click();
  await expect(page).toHaveURL(/#\/brokers$/, { timeout: 120_000 });
  await expect(page.getByRole("heading", { name: "Brokers" })).toBeVisible();

  await page.locator(".tabs").getByRole("link", { name: "Risks", exact: true }).click();
  await page.getByRole("link", { name: "Submit risk" }).click();
  await page.getByLabel("Asset hash").fill("asset-e2e");
  await page.getByLabel("Hash", { exact: true }).fill("evidence-e2e");
  await page.getByLabel("Exposure ref").fill("exposure-e2e");
  await page.getByLabel("Consequence ref").fill("consequence-e2e");
  await page.getByRole("button", { name: "Submit risk" }).click();
  await expect(page).toHaveURL(/#\/risks$/, { timeout: 120_000 });
  await expect(page.getByRole("heading", { name: "Risks" })).toBeVisible();

  await page.locator(".card").filter({ hasText: "Open" }).first().getByRole("link").last().click();
  await expect(page.getByRole("link", { name: "Open slip from this risk" })).toBeVisible();
  await page.getByRole("link", { name: "Open slip from this risk" }).click();
  await page.getByRole("button", { name: "Open slip" }).click();
  await expect(page).toHaveURL(/#\/slips\/rho%3Aid%3A/, { timeout: 120_000 });
  await expect(page.getByRole("heading", { name: /Slip|slp:/ })).toBeVisible();
});
