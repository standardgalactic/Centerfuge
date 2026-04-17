# RSVP Procedural Geometry Foundry

## File tree

```
rsvp/                        Field algebra (no bpy dependency)
  vec.py                     Vector math
  fields.py                  Basin, DirectionalBias, HarmonicField, EntropyCap
  operators.py               Gradient, divergence, curl, closure_field
  sampling.py                Grid sampling, rejection seeding
  terrain.py                 Height maps, terrain_field, tower_radius
  growth.py                  trace_growth_path, branch_paths
  seams.py                   seam_displacement, seam_obstruction_metric
  presets.py                 Preset builders
  __init__.py                Flat public API

Generators (headless Blender scripts):
  generate_tree.py           RSVP-field-driven tree curves
  generate_landscape.py      Displaced terrain + seam artifact
  generate_scene.py          Landscape + closure-seeded trees

Meta-layer (code → compilers):
  make_generator.py          Emit new generator from preset template
  compose_generator.py       Symbolically compose fields → new generators
  manifest_to_generators.py  Bias next round from manifest analysis

Analysis (no Blender):
  probe_fields.py            Field statistics without rendering
  build_registry.py          Aggregate all manifests → registry.json
  select_interesting.py      Score and rank registry entries
  make_contact_sheet.py      PNG or HTML contact sheet from batch PNGs

Rendering:
  render_still.py            Universal auto-framing still renderer (bpy)
  render_from_generator.sh   Generate + render in one step
  make_scenes.sh             Batch scene composition

Orchestration:
  rsvp_batch.sh              Batch runner with JSON sidecars + manifest
  rsvp_expand.sh             Compose → batch → aggregate (full loop)
  replay.sh                  Recompile any asset by generator + seed
```

## The three layers

1. `rsvp/` — invariant field algebra
2. `generate_*.py` — compilers: fields → geometry
3. `compose_*/manifest_*/build_*` — meta-compilers: explore the space

## Quickstart

```bash
# Field stats, no Blender needed
python probe_fields.py --preset make_tree_operators --samples 2000

# Single asset
blender --background --python generate_tree.py -- --output /tmp/tree.blend --seed 3

# Generate + render
./render_from_generator.sh tree 42 --resolution 1024

# Replay any asset by identity
./replay.sh tree 42 --render

# Batch 8 seeds, 4 parallel jobs
./rsvp_batch.sh -g tree -s "0:8" -r -j 4

# Full self-expansion loop
./rsvp_expand.sh --count 6 --master-seed 0 --render

# Build corpus registry
python build_registry.py --root ./rsvp_output

# Select best seeds and emit batch commands
python select_interesting.py --registry registry.json --metric slow --emit-batch

# Contact sheet from batch output
python make_contact_sheet.py --input-dir ./rsvp_output --cols 4

# Compose scenes across seeds
./make_scenes.sh --seeds "0:6" --render
```
