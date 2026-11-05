import { expect, type Page, test } from "@playwright/test";

const FINALITY = { timeout: 120_000 };

async function waitForReceipt(page: Page) {
  const receipt = page.locator("details.receipt").last();
  await expect(receipt).toBeVisible(FINALITY);
  await expect(page.locator(".warn-box")).toHaveCount(0);
}

async function createWalletAndFund(page: Page) {
  await page.goto("/");
  await page.getByRole("button", { name: "Create", exact: true }).click();
  const passwords = page.locator('input[type="password"]');
  await passwords.nth(0).fill("write-test-password");
  await passwords.nth(1).fill("write-test-password");
  await page.getByRole("button", { name: "Create wallet" }).click();
  await expect(page.getByRole("button", { name: "Lock" })).toBeVisible();

  // The faucet drips native REV for deploy precharge; premiums and capital come from
  // the r-cash account, so move REV into it before the placement.
  await page.locator(".tabs").getByRole("link", { name: "Me", exact: true }).click();
  await page.getByRole("button", { name: "Request devnet REV" }).click();
  await page.waitForTimeout(15_000);
  await page.locator('input[inputmode="numeric"]').first().fill("20000");
  await page.getByRole("button", { name: "Fund r-cash account" }).click();
  await expect(page.getByText("Funded the r-cash account")).toBeVisible(FINALITY);
}

test("places a risk, binds a policy and settles a claim", async ({ page }) => {
  await createWalletAndFund(page);

  await page.locator(".tabs").getByRole("link", { name: "Syndicates", exact: true }).click();
  await page.getByRole("link", { name: "Create syndicate" }).click();
  await page.getByLabel("Name").fill("E2E Syndicate");
  await page.getByRole("button", { name: "Create syndicate" }).click();
  await expect(page).toHaveURL(/#\/syndicates\/rho%3Aid%3A/, FINALITY);
  const syndicateUri = decodeURIComponent(
    page.url().split("/syndicates/")[1] ?? "",
  );
  expect(syndicateUri).toMatch(/^rho:id:/);

  // Capacity is real capital: contribute before any quote can reserve it.
  await page.locator('input[inputmode="numeric"]').first().fill("6000");
  await page.getByRole("button", { name: "Contribute" }).click();
  await waitForReceipt(page);

  await page.locator(".tabs").getByRole("link", { name: "Brokers", exact: true }).click();
  await page.getByRole("link", { name: "Register broker" }).click();
  await page.getByLabel("Name").fill("E2E Broker");
  await page.getByLabel("Licence hash").fill("e2e-licence");
  await page.getByRole("button", { name: "Register broker" }).click();
  await expect(page).toHaveURL(/#\/brokers\/rho%3Aid%3A/, FINALITY);

  await page.locator(".tabs").getByRole("link", { name: "Risks", exact: true }).click();
  await page.getByRole("link", { name: "Submit risk" }).click();
  await page.getByLabel("Asset hash").fill("asset-e2e");
  await page.getByLabel("Hash", { exact: true }).fill("evidence-e2e");
  await page.getByLabel("Exposure ref").fill("exposure-e2e");
  await page.getByLabel("Consequence ref").fill("consequence-e2e");
  await page.getByRole("button", { name: "Submit risk" }).click();
  await expect(page).toHaveURL(/#\/risks\/rho%3Aid%3A/, FINALITY);
  await expect(page.getByRole("link", { name: "Open slip from this risk" })).toBeVisible();

  await page.getByRole("link", { name: "Open slip from this risk" }).click();
  await page.getByRole("button", { name: "Open slip" }).click();
  await expect(page).toHaveURL(/#\/slips\/rho%3Aid%3A/, FINALITY);
  await expect(page.getByRole("heading", { name: /Slip|slp:/ })).toBeVisible();

  await page.getByLabel("Syndicate URI").fill(syndicateUri);
  await page.getByLabel("Share bps").fill("10000");
  await page.getByRole("button", { name: "Subscribe" }).click();
  await waitForReceipt(page);

  await page.getByRole("button", { name: "Accept", exact: true }).click();
  await waitForReceipt(page);

  await page.getByRole("button", { name: "Fund premium" }).click();
  await waitForReceipt(page);

  await page.getByRole("button", { name: "Bind" }).click();
  await waitForReceipt(page);

  await expect(page.getByRole("link", { name: "Open policy" })).toBeVisible(FINALITY);
  await page.getByRole("link", { name: "Open policy" }).click();
  await expect(page).toHaveURL(/#\/policies\/rho%3Aid%3A/, FINALITY);
  await expect(page.getByRole("heading", { name: /Policy|pol:/ })).toBeVisible();

  // A loss must fall inside the policy period and inside the notice window.
  const status = await page.request.get("http://localhost:40403/api/v1/status");
  const height = (await status.json()).latestBlockNumber as number;
  await page.getByLabel("Loss height").fill(String(height));
  await page.getByRole("button", { name: "Open claim" }).click();
  await waitForReceipt(page);

  await page.getByRole("link", { name: "open", exact: true }).click();
  await expect(page).toHaveURL(/#\/claims\/rho%3Aid%3A/, FINALITY);

  await page.getByRole("button", { name: "Classify" }).click();
  await waitForReceipt(page);
  await page.getByRole("button", { name: "Assess" }).click();
  await waitForReceipt(page);
  await page.getByRole("button", { name: "Agree" }).click();
  await waitForReceipt(page);
  await page.getByRole("button", { name: "Settle" }).click();
  await waitForReceipt(page);
  await page.getByRole("button", { name: "Close" }).click();
  await waitForReceipt(page);
  await expect(page.getByText(/closed/i).first()).toBeVisible(FINALITY);

  await page.locator(".tabs").getByRole("link", { name: "Fund", exact: true }).click();
  await page.locator('input[inputmode="numeric"]').first().fill("100");
  await page.getByPlaceholder("policy id").fill("e2e-fund");
  await page.getByRole("button", { name: "Contribute", exact: true }).click();
  await waitForReceipt(page);
});
