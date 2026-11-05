import { expect, test } from "@playwright/test";

test("boots, creates a wallet and reads the market books", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Overview" })).toBeVisible();

  const unlock = page.getByRole("heading", { name: "Wallet" });
  await expect(unlock).toBeVisible();
  await page.getByRole("button", { name: "Create", exact: true }).click();
  const passwords = page.locator('input[type="password"]');
  await passwords.nth(0).fill("integration-password");
  await passwords.nth(1).fill("integration-password");
  await page.getByRole("button", { name: "Create wallet" }).click();

  await expect(page.getByRole("heading", { name: "Wallet" })).toBeHidden();
  await expect(page.getByRole("button", { name: "Lock" })).toBeVisible();

  await page.locator(".tabs").getByRole("link", { name: "Syndicates", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Syndicates" })).toBeVisible();

  await page.locator(".tabs").getByRole("link", { name: "Risks", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Risks" })).toBeVisible();

  await page.locator(".tabs").getByRole("link", { name: "Claims", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Claims" })).toBeVisible();
});
