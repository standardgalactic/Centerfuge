# Methods

## Code Organization
- Cargo workspace with shared crates: `core_types`, `simulation`, `linguistics`, `tiling`, `semantics`, `io`.
- Per‑project binaries in `rust/projects/*`.
- PyO3 packages in `python/*_py`.

## Reproducibility
- CI builds on push.
- Deterministic seeds for stochastic modules.
- Property tests for invariants.
