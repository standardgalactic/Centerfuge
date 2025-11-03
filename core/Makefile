
# Top-level Makefile for flyxion-core
# - Uses Rust toolchain if available
# - Falls back to Python-based docs build if Rust/mdBook are not available

CARGO := $(shell command -v cargo 2>/dev/null)
MDBOOK := $(shell command -v mdbook 2>/dev/null)
PYTHON := $(shell command -v python3 2>/dev/null || command -v python 2>/dev/null)

.PHONY: all build fmt test clean docs wheel-sim wheel-ling wheel-sem

all: build

build:
ifdef CARGO
	@echo "[build] Using cargo"
	cd rust && cargo build --workspace
else
	@echo "[build] ⚠️  Rust (cargo) not found. Skipping Rust build."
endif

fmt:
ifdef CARGO
	cd rust && cargo fmt --all && cargo clippy --all-targets -D warnings
else
	@echo "[fmt] ⚠️  Rust (cargo) not found. Skipping fmt/clippy."
endif

test:
ifdef CARGO
	cd rust && cargo test --workspace
else
	@echo "[test] ⚠️  Rust (cargo) not found. Skipping tests."
endif

clean:
	@echo "[clean] Removing build artifacts"
	rm -rf rust/target docs/book docs/_site

# Build docs with mdBook if available, else Python fallback
docs:
ifeq ($(MDBOOK),)
	@echo "[docs] mdBook not found; using Python fallback"
	$(PYTHON) scripts/build_docs.py
else
	@echo "[docs] Building with mdBook"
	cd docs && mdbook build
endif

# Python wheels (require Rust for PyO3)
wheel-sim:
ifdef CARGO
	cd python/simulation_py && $(PYTHON) -m pip install -U pip && $(PYTHON) -m pip install maturin && maturin build --release
else
	@echo "[wheel-sim] ⚠️  Rust not found; PyO3 wheels cannot be built."
endif

wheel-ling:
ifdef CARGO
	cd python/linguistics_py && $(PYTHON) -m pip install -U pip && $(PYTHON) -m pip install maturin && maturin build --release
else
	@echo "[wheel-ling] ⚠️  Rust not found; PyO3 wheels cannot be built."
endif

wheel-sem:
ifdef CARGO
	cd python/semantics_py && $(PYTHON) -m pip install -U pip && $(PYTHON) -m pip install maturin && maturin build --release
else
	@echo "[wheel-sem] ⚠️  Rust not found; PyO3 wheels cannot be built."
endif
