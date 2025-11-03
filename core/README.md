# flyxion-core

A unified, **synchronous-first** multi-project infrastructure with **separated Rust and Python trees**.

- `rust/` — Cargo workspace containing shared crates and 15 project stubs.
- `python/` — Python packages (PyO3-backed) that depend on Rust crates via relative paths, built with `maturin`.
- CI, Docker, and reproducible builds included.

## Build (Rust)
```bash
cd rust
cargo build
```

## Python wheels (per package)
```bash
# Example for simulation bindings
cd python/simulation_py
pip install maturin
maturin develop  # builds a local wheel backed by Rust code
python -c "import simulation_py as sp; print(sp.__doc__)"
```

## Layout
- `rust/crates`: core libraries (core_types, simulation, linguistics, tiling, semantics, io)
- `rust/projects`: 15 project stubs (SGA, λ-Arabic, Earth Cube, Zettelkasten, RSVP, SITH, Flyxion, TARTAN, Crystal Plenum, Agora, Swype Hero, SpellPop, AOS, Bioforge, Geozotic)
- `python/*_py`: separate Python packages exposing stable APIs, compiled against the Rust crates.

