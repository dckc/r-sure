#!/usr/bin/env bash
# Normalize rendered Rholang terms with the target node's own normalizer.
#
#   tools/normalize_check.sh .devnet/rendered/*.rho
#
# `parse_check.sh` only parses. The node's normalizer is stricter: it rejects bundle
# content with free variables or wildcards, top-level free variables, and name/data sort
# errors. Those are the classes that surfaced as deploy failures in the campaign, so this
# gate runs on rendered terms before any deploy.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RCHAIN_RUST_DIR="${RCHAIN_RUST_DIR:-$ROOT/../RNodeRust}"
CRATE="$ROOT/.devnet/normalize-check"
mkdir -p "$CRATE/src"

ARGS=()
for arg in "$@"; do
  ARGS+=("$(cd "$(dirname "$arg")" && pwd)/$(basename "$arg")")
done

cat > "$CRATE/Cargo.toml" <<EOF
[package]
name = "rsure-normalize"
version = "0.1.0"
edition = "2021"

[workspace]

[dependencies]
rchain-rholang = { path = "$(cd "$RCHAIN_RUST_DIR" && pwd)/rholang" }
EOF

cat > "$CRATE/src/main.rs" <<'EOF'
use std::{env, fs};
fn main() {
    let mut bad = 0;
    for path in env::args().skip(1) {
        let text = fs::read_to_string(&path).unwrap();
        match rchain_rholang::normalizer::source_to_adt(&text) {
            Ok(_) => println!("OK   {path}"),
            Err(e) => { bad += 1; println!("FAIL {path}: {e:?}"); }
        }
    }
    std::process::exit(if bad == 0 { 0 } else { 1 });
}
EOF

cd "$CRATE"
RUSTC_BOOTSTRAP=1 CC="${CC:-/usr/bin/gcc}" cargo build --release --quiet
exec "$CRATE/target/release/rsure-normalize" "${ARGS[@]}"
