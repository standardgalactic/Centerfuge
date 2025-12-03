# Flyxion Simulation Suite v3

This package contains version 3 of the Blender-based simulation and
visualization tools for RSVP, HYDRA, xylomorphic architecture, semantic
merge operators, and delta–sigma cognitive modulators.

## Structure

- `v3/scripts/`
  - `hydra_persona_field.py` — HYDRA multi-persona agents moving on an RSVP lattice.
  - `xylomorphic_city_generator.py` — Xylo-city / xylomorphic organ-city generator.
  - `semantic_merge_operators_anim.py` — Semantic merge operator animation.
  - `delta_sigma_cognitive_modulators.py` — Delta–sigma bitstreams on CLIO edges.

- `v3/helpers/`
  - `storage_helper_v3.py` — scene, camera orbit, lights, ground, render settings.
  - `run_manager_v3.py` — orchestrator to run a target script and save a blend file.

- Root scripts
  - `run_all_simulations_v3.sh` — batch-run all simulations headless.
  - `render_all_v3.sh` — render all .blend files and encode to MP4 via ffmpeg.

## Basic usage

1. Ensure `blender` and `ffmpeg` are in your PATH.
2. From the project root, run:

   ```bash
   chmod +x v3/run_all_simulations_v3.sh
   ./v3/run_all_simulations_v3.sh
   ```

3. To render and encode videos:

   ```bash
   chmod +x v3/render_all_v3.sh
   ./v3/render_all_v3.sh
   ```
