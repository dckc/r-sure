// Smoke test for the wasm facade. The scaffold skips cleanly when wasm-pack output is absent.
import { existsSync } from "node:fs";

const pkg = new URL("../src/wasm/pkg/rsure_wasm.js", import.meta.url);
if (!existsSync(pkg)) {
  console.log("wasm-smoke: not_run (build the wasm facade first)");
  process.exit(0);
}
const module = await import(pkg.href);
if (typeof module.Rsure !== "function") {
  console.error("wasm-smoke: Rsure export missing");
  process.exit(1);
}
console.log("wasm-smoke: ok");
