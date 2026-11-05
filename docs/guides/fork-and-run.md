# Fork and run

> **Status:** Implemented; the full suite passes on devnet. See
> [Project status](../orientation/project-status.md).

Prerequisites: Docker, Python 3.12+, Node 22 (for the web client), an r-cash checkout at
`~/Rholphin` and r-gen at `~/RGen`.

```sh
git clone git@github.com:rhovision-org/r-sure.git
cd r-sure
make venv
make build-check measure-check spec-check parse-check
make devnet
make rcash-keys rcash-bootstrap
make keys install
make unit-all
make web-install web-build
```

The web client is described in [Use the web client](use-the-web-client.md).

`RCASH_DIR`, `RGEN_DIR`, `RHOLO_DIR` and `NODE` override the defaults. The install order is in
`configs/devnet.json` and `reference/install-order-and-keys.md`.

To run against r-gen as well, deploy r-gen on the same devnet first, then set `rgen_root_uri`
in `configs/devnet.json`. `RgenAdapter` remains disabled until the admins enable it.
