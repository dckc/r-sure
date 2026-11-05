#!/usr/bin/env bash
# Normalize every Rholang term the SDK and web client generate.
#
#   tools/check_client_terms.sh
#
# The rendered contract terms have a parser and normalizer gate. The client builds its
# own terms (reads, writes, funding and payment calls), and a free variable or sort error
# there only surfaces as a rejected deploy. This runs the node's own normalizer over the
# exact bytes those builders produce.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/.devnet/client-terms"

rm -rf "$OUT"
cargo run -q --manifest-path "$ROOT/Cargo.toml" -p rsure-sdk \
  --example term_preview -- "$OUT"
"$ROOT/tools/normalize_check.sh" "$OUT"/*.rho
