# Admissibility Experiments

[Prototype Visualizer](https://standardgalactic.github.io/Centerfuge/admissibility-experiments/dist/)

This repository is a reproducible suite of headless Blender scenes. Each scene is an experiment: it constructs a claim as geometry, measures the resulting scene state, renders the evidence, and writes a JSON sidecar. A failed check is retained as a diagnostic artifact. Scene processes exit successfully when they detect an inadmissible result; `tools/verify_suite.py` is the component that gives the batch a non-zero status.

The archive contains sixteen experiments spanning Spherepop primitives, RSVP and distinction holonomy, TARTAN and structural semantics, infrastructure, narrative systems, and pedagogy. The first five implement the foundational suite specified in `docs/FOUNDATIONAL_SUITE.md`. The other eleven extend the same contract.

## Requirements

Blender 4.0 or later is supported. The suite selects `BLENDER_EEVEE` on Blender 4.0/4.1 and `BLENDER_EEVEE_NEXT` where that identifier is available. No third-party Python package is required inside Blender. Ordinary Python 3.10 or later is sufficient for manifest validation.

## Run

From this directory:

```bash
./render_all.sh
python3 tools/verify_suite.py
```

To render one experiment:

```bash
blender --background --python scenes/pop_refuse_bind_collapse.py
```

Override output location, resolution, or sample count with environment variables:

```bash
ADMISSIBILITY_OUTPUT=/tmp/renders WIDTH=1280 HEIGHT=720 SAMPLES=32 ./render_all.sh
```

For a quick geometry-and-sidecar smoke test without final images:

```bash
DRY_RUN=1 ./render_all.sh
```

## Contract

Every scene module exposes `build()`, `measure()`, and `render()`. Construction leaves machine-readable custom properties on the objects it creates. Measurement reads those properties or Blender geometry rather than declaring an expected result by fiat. The sidecar records parameters, render settings, computed checks, output paths, and status. Status is `pass` only when all checks pass.

The final `render_ledger` experiment scans the outputs of every preceding experiment. Missing scripts, sidecars, outputs, or statuses become visible break markers. Run it last.

## Layout

`scenes/` contains the sixteen standalone entry points and the shared implementation. `specs/` contains full diagnostic specifications. `tools/` contains suite verification and manifest generation. `output/` is created at runtime and is intentionally absent from the archive.

## Deliberate limitations

The fusion comparison and molecular assembler are epistemic schematics, not engineering simulations. Their sidecars check internal accounting and declared relationships, not physical feasibility. The RSVP field and persistence-cone scenes likewise test whether a proposed visual mapping is internally coherent; they do not count as evidence for the underlying cosmological theory.

# Admissibility Results Dashboard

This is a separate, dependency-free dashboard for an Admissibility Experiments output directory. It does not modify the experiment suite.

Generate the dashboard by pointing the builder at the experiment-suite root:

```bash
python3 build_dashboard.py /home/bonobo/Centerfuge/admissibility-experiments
```

Then serve the generated site:

```bash
python3 -m http.server 8000 --directory dist
```

Open `http://localhost:8000/`. Re-run the builder after producing new Blender results. The builder copies render images into `dist/renders/`, so the generated `dist/` directory can be moved or archived independently.

The page includes suite totals, status and framework filters, text search, render previews, expected-versus-observed check results, evidence, parameters, generator metadata, and an explicit empty state when no sidecars exist.
