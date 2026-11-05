// Generate encrypted keystores for the devnet admin keys so the browser can exercise
// the 2-of-3 flow. Reads `.devnet/keys.json`; writes `.demo/keystores-devnet`.
//
// These are devnet-only keys with no value. The keystore password is fixed so the
// Playwright test can import the documents; it is written next to them, not committed.
import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const webDir = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const repoDir = resolve(webDir, "..");
const keysPath = resolve(repoDir, ".devnet/keys.json");
const outDir = resolve(repoDir, ".demo/keystores-devnet");
const binary = resolve(repoDir, "target/debug/rsure");
const PASSWORD = "rsure-devnet-admin";
const NAMES = ["admin1", "admin2", "admin3"];

if (!existsSync(keysPath)) {
  console.error(`devnet-keystores: ${keysPath} is missing; run \`make keys\` first`);
  process.exit(2);
}

// Cargo is a no-op when the binary is current; always call it so a stale `rsure`
// cannot silently lack a subcommand.
execFileSync("cargo", ["build", "-q", "-p", "rsure-cli"], {
  cwd: repoDir,
  stdio: "inherit",
});

mkdirSync(outDir, { recursive: true });
const admins = [];
for (const name of NAMES) {
  const file = resolve(outDir, `${name}.json`);
  const address = execFileSync(
    binary,
    [
      "keystore",
      "encrypt",
      "--keys",
      keysPath,
      "--name",
      name,
      "--password",
      PASSWORD,
      "--out",
      file,
    ],
    { encoding: "utf8" },
  ).trim();
  admins.push({ name, address, file });
}

writeFileSync(
  resolve(outDir, "index.json"),
  `${JSON.stringify({ password: PASSWORD, admins }, null, 2)}\n`,
);
console.log(`devnet-keystores: ${admins.length} keystores in ${outDir}`);
