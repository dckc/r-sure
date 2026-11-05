PY ?= .venv/bin/python
MDBOOK ?= mdbook
RCASH_DIR ?= ../Rholphin
RGEN_DIR ?= ../RGen
RHOLO_DIR ?= ../RNodeRust
NODE ?= http://localhost:40403

export RCASH_DIR := $(abspath $(RCASH_DIR))
export RGEN_DIR := $(abspath $(RGEN_DIR))
export RHOLO_DIR := $(abspath $(RHOLO_DIR))

.PHONY: venv build build-check measure measure-check metrics metrics-compare \
        check-arch check-captures check-select check-placeholders check-money \
        check-suites check-docs spec-check parse-check docs docs-serve docs-check \
        devnet devnet-up devnet-wait down status rcash-install rcash-keys \
        rcash-bootstrap rgen-install rgen-keys keys install setup \
        unit-root unit-payments unit-syndicate unit-capital unit-broker unit-risk \
        unit-slip unit-subscription unit-binding unit-line unit-policy unit-distribution \
        unit-premium unit-fund unit-books unit-pause unit-pause-scope unit-admin \
        unit-admin-keys unit-cell-liveness unit-factory-auth unit-replay unit-expiry \
        unit-evidence unit-oracle unit-claim-lifecycle unit-claim-refusals unit-settlement \
        unit-shortfall unit-conservation unit-behavior unit-generality unit-share-reuse \
        integration-rcash integration-rgen integration-rshare unit-all \
        lean-build lean-check vectors check-flows check-flows-strict check-claims \
        formal-check \
        audit-check audit-trace audit-trace-check check-audit check-arm-inventory audit-dynamic \
        check-concurrency-audit check-composition-audit audit-scan \
        client-lint client-test client-wasm client-wasm-smoke client-gates client-check \
        client-fixtures client-journey client-keystores web-install web-test web-build web-e2e \
        check ci clean

venv:
	python3 -m venv .venv
	$(PY) -m pip -q install --upgrade pip
	$(PY) -m pip -q install -r harness/requirements.txt

build:
	$(PY) tools/build_contracts.py

build-check:
	$(PY) tools/build_contracts.py --check

measure:
	$(PY) tools/measure_contracts.py --write

measure-check:
	$(PY) tools/measure_contracts.py --check

metrics:
	$(PY) tools/metrics.py --write contracts/metrics-current.json

metrics-compare:
	$(PY) tools/metrics.py --compare contracts/metrics-baseline.json

check-arch:
	$(PY) tools/check_arch.py

check-captures:
	$(PY) tools/check_captures.py

check-select:
	$(PY) tools/check_select.py

check-placeholders:
	$(PY) tools/check_placeholders.py

check-money:
	$(PY) tools/check_money.py

check-suites:
	$(PY) tools/check_suites.py

check-docs:
	$(PY) tools/check_docs.py

spec-check: build-check measure-check check-arch check-captures check-select \
            check-placeholders check-money check-suites

parse-check:
	$(PY) harness/install.py --dry-run
	tools/parse_check.sh contracts/build/*.rho .devnet/rendered/*.rho

docs:
	$(MDBOOK) build

docs-serve:
	$(MDBOOK) serve --open

docs-check: check-docs
	$(MDBOOK) build

devnet:
	$(MAKE) -C $(RCASH_DIR) devnet RHOLO_DIR=$(RHOLO_DIR)

devnet-up:
	-$(MAKE) -C $(RCASH_DIR) down RHOLO_DIR=$(RHOLO_DIR)
	$(MAKE) -C $(RCASH_DIR) devnet RHOLO_DIR=$(RHOLO_DIR)
	$(PY) harness/preflight.py --wait 300

devnet-wait:
	$(PY) harness/preflight.py --wait 300

down:
	$(MAKE) -C $(RCASH_DIR) down RHOLO_DIR=$(RHOLO_DIR)

status:
	@curl -s $(NODE)/api/v1/status | $(PY) -m json.tool || echo "devnet not running"

rcash-install:
	$(PY) harness/rcash_bootstrap.py --wait

rcash-keys:
	$(PY) tools/keygen.py --out .devnet/keys.json --count 4

rcash-bootstrap:
	$(PY) harness/rcash_bootstrap.py --wait

rgen-install:
	@echo "rgen-install: deploy r-gen at $(RGEN_DIR) and set rgen_root_uri in configs/devnet.json"

rgen-keys:
	@echo "rgen-keys: r-gen uses its own devnet keys; see $(RGEN_DIR)/harness"

keys:
	$(PY) tools/keygen.py --out .devnet/keys.json --count 4

install:
	$(PY) harness/install.py

setup: devnet rcash-keys rcash-bootstrap keys install

unit-%:
	$(PY) harness/run_suites.py $*

integration-rcash:
	$(PY) harness/run_suites.py integration_rcash

integration-rgen:
	$(PY) harness/run_suites.py integration_rgen

integration-rshare:
	$(PY) harness/run_suites.py integration_rshare

unit-all:
	$(PY) harness/run_suites.py --all

lean-build:
	cd spec/lean && lake build

lean-check:
	$(PY) tools/check_lean.py

vectors:
	$(PY) tools/check_vectors.py

check-flows:
	$(PY) tools/check_flows.py

check-flows-strict:
	$(PY) tools/check_flows.py --strict

check-claims:
	$(PY) tools/check_claims.py --check --strict-audit

formal-check: lean-check vectors check-flows check-flows-strict check-claims

audit-check: check-audit check-arm-inventory audit-trace-check check-concurrency-audit check-composition-audit

check-concurrency-audit:
	$(PY) tools/check_concurrency_audit.py

check-composition-audit:
	$(PY) tools/check_composition_audit.py

audit-scan:
	$(PY) tools/check_bundle_closedness.py
	$(PY) tools/check_take_repost.py
	$(PY) tools/check_reply_shapes.py
	$(PY) tools/check_pause_scope.py

audit-trace:
	$(PY) tools/audit_trace.py --write

audit-trace-check:
	$(PY) tools/audit_trace.py --check

check-audit:
	$(PY) tools/check_audit.py

check-arm-inventory:
	$(PY) tools/check_arm_inventory.py

audit-dynamic:
	@echo "audit-dynamic: run the audit reproduction suites on a prepared devnet"

client-lint:
	cargo fmt --all --check
	cargo clippy --workspace --all-targets -- -D warnings

client-test:
	cargo test --workspace

client-wasm:
	cargo check --workspace --target wasm32-unknown-unknown

client-wasm-smoke: web-install
	npm --prefix web run test:wasm

client-gates: client-lint client-test client-wasm web-install

client-check: client-gates client-wasm-smoke

client-fixtures:
	$(PY) harness/run_suites.py --fixtures

client-journey:
	$(PY) harness/run_suites.py unit_journey

client-keystores:
	$(PY) harness/run_suites.py --keystores

web-install:
	npm --prefix web install

web-test: web-install
	npm --prefix web run test

web-build: web-install
	npm --prefix web run build

web-e2e: web-build
	npm --prefix web run test:e2e

check: spec-check parse-check docs-check

ci: check formal-check audit-check client-check web-test web-build

clean:
	rm -rf .devnet/rendered contracts/build docs/book web/dist web/node_modules
