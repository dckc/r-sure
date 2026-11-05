// Offline smoke test for the wasm boundary. No devnet, no network.
// Build first: npm run wasm:build
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const webDir = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const repoDir = resolve(webDir, "..");
const pkgDir = resolve(webDir, "src/wasm/pkg");
const { default: init, Rsure, version, classes } = await import(
  pathToFileURL(resolve(pkgDir, "rsure_wasm.js")).href
);

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

const wasm = readFileSync(resolve(pkgDir, "rsure_wasm_bg.wasm"));
await init({ module_or_path: wasm });

assert(version() === "0.1.0", `unexpected version ${version()}`);
assert(classes().split(",").includes("engineering"), "missing risk classes");

const manifest = readFileSync(resolve(repoDir, "deployments/devnet.json"), "utf8");
const wallet = new Rsure("http://127.0.0.1:40403", manifest);
const document = wallet.create_wallet("smoke-test-password");
const address = wallet.address();
assert(address && address.startsWith("1111"), `bad address ${address}`);
assert(document.includes('"version":3'), "keystore is not v3");
assert(!document.includes("secret"), "keystore leaked a secret field");
assert(wallet.is_unlocked(), "wallet did not unlock");

const exported = wallet.export_keystore("second-password");
assert(exported.includes('"crypto"'), "export is not a keystore");
assert(!exported.includes("secret"), "export leaked a secret field");

const opId = wallet.new_op_id("claim", 1_700_000_000_000n);
assert(/^claim-1700000000000-[0-9a-f]{32}$/.test(opId), `bad opId ${opId}`);
const digest = wallet.hash_text("evidence");
assert(/^[0-9a-f]{64}$/.test(digest), `bad digest ${digest}`);

wallet.lock();
assert(!wallet.is_unlocked(), "lock did not clear the key");

let rejected = false;
try {
  wallet.unlock(document, "wrong-password");
} catch {
  rejected = true;
}
assert(rejected, "wrong password was accepted");

const unlocked = wallet.unlock(document, "smoke-test-password");
assert(unlocked === address, "unlock returned a different address");

console.log("WASM SMOKE: PASS");
