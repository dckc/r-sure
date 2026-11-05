#!/usr/bin/env bash
# Install the built contracts into the node's own in-memory reducer and call a few arms.
#
#   make local-reducer
#
# No devnet, Docker or network. The temporary crate points at the RNodeRust checkout
# (RCHAIN_RUST_DIR, default ../RNodeRust), so this runs the node's reducer, not a model.
# It needs protoc because the node's model crate generates its protobuf bindings.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RCHAIN_RUST_DIR="${RCHAIN_RUST_DIR:-$ROOT/../RNodeRust}"
CRATE="$ROOT/.devnet/local-reducer"

if [[ ! -d "$RCHAIN_RUST_DIR/rholang" ]]; then
  echo "local-reducer: no node checkout at $RCHAIN_RUST_DIR" >&2
  exit 2
fi

mkdir -p "$CRATE/src"
cp "$ROOT/tools/local_reducer/main.rs" "$CRATE/src/main.rs"

cat > "$CRATE/Cargo.toml" <<EOF
[package]
name = "rsure-local-reducer"
version = "0.1.0"
edition = "2021"

[workspace]

[dependencies]
rchain-crypto = { path = "$RCHAIN_RUST_DIR/crypto" }
rchain-models = { path = "$RCHAIN_RUST_DIR/models" }
rchain-rholang = { path = "$RCHAIN_RUST_DIR/rholang" }
rchain-rspace = { path = "$RCHAIN_RUST_DIR/rspace" }
rchain-shared = { path = "$RCHAIN_RUST_DIR/shared" }
tokio = { version = "1", features = ["rt-multi-thread"] }
EOF

cd "$CRATE"
CARGO_TARGET_DIR="${CARGO_TARGET_DIR:-$ROOT/.devnet/local-reducer-target}" \
  cargo run --release --quiet -- "$ROOT/contracts/build"
