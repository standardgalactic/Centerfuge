# Flyxion Simulation Suite v3.2 (RSVP Objects Pack)

v3.2 adds a suite of still-image Blender generators that visualize core
elements of your theories: RSVP plenum cells, HYDRA personas, xylomorphic
organ clusters, higher-category merge operators, and delta–sigma towers.

## Scripts

- `rsvp_plenum_cell.py`
  Single RSVP plenum cell: scalar Φ core, vector ellipsoid, entropy sparks,
  and lamphrodynamic flow ribbons.

- `rsvp_three_cell_lattice.py`
  Three plenum cells arranged in a triangle, connected by glowing filaments.

- `hydra_persona_glyphs.py`
  Central field node with four glyphs (Seer, Engineer, Archivist, Trickster)
  linked by thin persona channels.

- `xylomorphic_organ_cluster_v2.py`
  Cluster of trunks, hubs, and curved branches forming an organ-like/xylomorphic
  structure.

- `semantic_merge_hicat.py`
  Objects A, B, and M as blocks with arrows A <- M -> B plus a colimit arrow
  from below.

- `delta_sigma_tower.py`
  Stacked torus rings with emission intensity encoding bitstream-like patterns.

## Helpers

- `storage_helper_v3_2.py`
  Sets up camera, lights, ground, and render settings for stills.

- `run_manager_v3_2.py`
  Loads a single script, executes it, and saves a .blend if requested.

## Batch rendering

Use:

```bash
cd v3_2
chmod +x render_stills_v3_2.sh
./render_stills_v3_2.sh
```

Output will be placed in `output_v3_2/` as `.blend` and `.png` per script.
