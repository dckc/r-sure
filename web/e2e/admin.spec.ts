import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { expect, test } from "@playwright/test";

interface AdminKeystore {
  name: string;
  address: string;
  file: string;
}

interface AdminBundle {
  password: string;
  admins: AdminKeystore[];
}

const index = resolve(process.cwd(), "..", ".demo/keystores-devnet/index.json");
const bundle: AdminBundle | null = existsSync(index)
  ? (JSON.parse(readFileSync(index, "utf8")) as AdminBundle)
  : null;

test("pauses and resumes with two of three admin signatures", async ({ page }) => {
  test.skip(!bundle, "run `make web-admin-keystores` first");
  if (!bundle) return;
  const [first, second] = bundle.admins;
  if (!first || !second) throw new Error("the keystore bundle needs two admins");

  const importWallet = async (file: string) => {
    await page.getByRole("button", { name: "Import", exact: true }).click();
    await page.getByLabel("Keystore JSON").fill(readFileSync(file, "utf8"));
    await page.getByLabel("Password").fill(bundle.password);
    await page.getByRole("button", { name: "Import and unlock" }).click();
    await expect(page.getByRole("button", { name: "Lock" })).toBeVisible();
  };

  await page.goto("/");
  await test.step("import the first admin", () => importWallet(first.file));
  await test.step("import the second admin", async () => {
    // Locking reopens the wallet overlay, so import straight from it.
    await page.getByRole("button", { name: "Lock" }).click();
    await importWallet(second.file);
  });

  await test.step("fund the submitting admin", async () => {
    // The submitting admin pays the deploy precharge from its native vault.
    await page.locator(".tabs").getByRole("link", { name: "Me", exact: true }).click();
    await page.getByRole("button", { name: "Request devnet REV" }).click();
    await page.waitForTimeout(15_000);
  });

  const submit = async () => {
    await page.getByRole("button", { name: "Submit 2-of-3" }).click();
    await expect(page.locator("details.receipt")).toBeVisible({ timeout: 120_000 });
    await expect(page.locator(".warn-box")).toHaveCount(0);
  };

  await test.step("collect signatures and pause", async () => {
    await page.locator(".tabs").getByRole("link", { name: "Admin", exact: true }).click();
    const passwords = page.locator('input[type="password"]');
    await expect(passwords).toHaveCount(2);
    await passwords.nth(0).fill(bundle.password);
    await passwords.nth(1).fill(bundle.password);
    const noncePill = page.locator(".pill", { hasText: /^nonce \d+$/ });
    await expect(noncePill).toBeVisible();
    const nonce = Number((await noncePill.textContent())?.replace("nonce ", ""));
    await submit();
    await expect(page.getByText("paused", { exact: true })).toBeVisible({ timeout: 60_000 });
    // The next submission signs the next nonce; wait for the re-read before rebuilding.
    await expect(
      page.locator(".pill", { hasText: `nonce ${nonce + 1}` }),
    ).toBeVisible({ timeout: 60_000 });
  });

  await test.step("pause again", async () => {
    await page.getByLabel("Action").selectOption("resumeAll");
    await submit();
    await expect(page.getByText("active", { exact: true }).first()).toBeVisible({
      timeout: 60_000,
    });
  });
});
