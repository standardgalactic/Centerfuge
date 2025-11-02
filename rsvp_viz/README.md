# RSVP Visualizer — *Tetraorthodrome Construction and Field Animation*

**Version:** 1.0  
**Target Blender:** 4.2.x  
**Renderer:** Cycles (GPU preferred)  
**Frame Count:** 180 frames @ 24 fps  
**Author:** Flyxion  

---

## Overview

`rsvp_viz` provides a complete headless Blender environment for visualizing **RSVP field structures** and the **Tetraorthodrome** — a 4-axis rotational frame representing orthogonal couplings of scalar Φ, vector 𝒗, and entropy S fields.

The repository includes:
- Ten sequential **`bpy` scripts** demonstrating geometric and dynamic phases of the Tetraorthodrome.  
- A **Geometry-Nodes / VDB pipeline** for scalar–vector–entropy field synthesis.  
- Cluster-ready **Docker + SLURM** configs with full provenance tracking.  
- **Tools** for NPZ→VDB and NPZ→point-cloud conversion.  
- Example **YAML configuration** (`data/lamphrodyne.yaml`) for immediate rendering.

---

## Quick Start (Local)

```bash
# Build the project tree
chmod +x make_all.sh
./make_all.sh

cd rsvp_viz

# Run an end-to-end pipeline render
./run_field_pipeline.sh data/lamphrodyne.yaml

# Or test any tetraorthodrome stage directly
blender -b -P scripts/tetraorthodrome/step_01_base_tetra.py -- --out output/step01.blend
blender -b -P scripts/tetraorthodrome/step_10_summary_render.py -- --out output/step10.blend --frames 180

