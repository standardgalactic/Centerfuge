# Flyxion Simulation Suite v3.1 (Static Visuals)

v3.1 is designed to give you **instant, visible objects** in Blender with
**single-frame renders only**. No animations, no long sim times.

## Contents

- `v3_1/scripts/`
  - `hydra_persona_field.py` — 7x7 lattice + 4 HYDRA persona orbs.
  - `semantic_merge_static.py` — 3 merge blobs (A, B, Merge) in the center.
  - `xylomorphic_city_static.py` — ring of trunk towers + canopy hubs.
  - `delta_sigma_static.py` — 4 colored arcs suggesting delta–sigma streams.

- `v3_1/helpers/`
  - `storage_helper_v3_1.py` — sets up camera, lights, ground, render settings.
  - `run_manager_v3_1.py` — loads and executes a target script, saves .blend.

- `v3_1/render_stills_v3_1.sh`
  - Batch-runs all scripts, saving `.blend` and `.png` per script.

## Usage

From inside the `v3_1` folder:

```bash
chmod +x render_stills_v3_1.sh
./render_stills_v3_1.sh
```

You will get:

- `output_v3_1/hydra_persona_field.png`
- `output_v3_1/semantic_merge_static.png`
- `output_v3_1/xylomorphic_city_static.png`
- `output_v3_1/delta_sigma_static.png`
