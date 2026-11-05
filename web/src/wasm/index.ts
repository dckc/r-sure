// Typed re-export of the wasm-pack output. The generated module is in src/wasm/pkg.
import init, { Rsure, classes, version } from "./pkg/rsure_wasm.js";

let ready: Promise<unknown> | null = null;

export async function initWasm(): Promise<void> {
  if (!ready) ready = init();
  await ready;
}

export { Rsure, classes, version };
