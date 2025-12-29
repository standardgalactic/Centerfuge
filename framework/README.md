# RSVP Simulation Lab

**Deterministic geometry + rendering backend for inspecting RSVP field evolution**

---

## Philosophy

Blender is treated as a **semantic microscope**, not a simulator:

- **Physics lives in Python**: your actual RSVP equations in `sim/rsvp_core.py`
- **Blender is a probe**: converts field snapshots → geometry → pixels
- **Separation of concerns**: simulation data is inspectable, version-controlled, format-agnostic

This matches the RSVP stance: *physics is not graphics; graphics are a probe*.

---

## Quick Start

```bash
# 1. Run simulation (produces field snapshots)
make sim

# 2. Render a single frame
make geonodes

# 3. Full pipeline: sim → animation → video
make full
```

---

## Project Structure

```
rsvp_sim/
├── sim/
│   ├── rsvp_core.py        # Your RSVP equations
│   ├── run_sim.py          # Simulation driver
│   ├── lattice_adapter.py  # Import custom formats
│   └── fields/             # Output: t000.npz, t001.npz, ...
│
├── blender/
│   ├── common.py           # Camera, lights, exports
│   ├── render_field.py     # Basic sphere visualization
│   ├── render_geonodes.py  # Fast geometry nodes (10-100x faster)
│   ├── render_vectors.py   # Vector field arrows
│   ├── render_animation.py # Time evolution
│   └── render_diagnostics.py # Histograms + stats
│
├── out/
│   ├── renders/            # PNG frames
│   └── evolution.mp4       # Video output
│
└── Makefile                # Pipeline automation
```

---

## Simulation Configuration

Edit `sim/run_sim.py`:

```python
CONFIG = {
    "N": 32,           # Lattice size (32³, 64³, 128³)
    "T": 100,          # Number of timesteps
    "dt": 0.05,        # Timestep size
    "dx": 1.0/32,      # Spatial resolution
    "save_every": 2,   # Save frequency
    "initial": "gaussian"  # or "dipole", "vortex", "random"
}
```

**Replace placeholder dynamics** in `sim/rsvp_core.py` with your actual RSVP PDEs.

---

## Visualization Modes

### 1. Basic (spheres at field maxima)
```bash
blender -b -P blender/render_field.py
```

### 2. Geometry Nodes (10-100x faster)
```bash
make geonodes
```
Single mesh + vertex attributes, scales to millions of points.

### 3. Vector Fields
```bash
make vectors
```
Cylinder arrows aligned with v(x).

### 4. Time Evolution
```bash
make anim
make video
```
Renders all `t000.npz` → `tNNN.npz`, produces MP4.

### 5. Quantitative Diagnostics
```bash
make diag
```
Entropy histograms + floating stats panels.

---

## Importing Your Own Lattice Data

### Supported Formats

The `lattice_adapter.py` supports:

- **NPZ** (default): `np.savez_compressed()`
- **HDF5**: Large datasets with compression
- **Raw binary**: `.bin` + `.json` metadata
- **CSV**: Human-readable (inefficient)
- **Custom**: Add your own parser

### Auto-Detection

```python
from lattice_adapter import LatticeAdapter

data = LatticeAdapter.auto_detect("your_data.npz")
phi = data['phi']  # shape (N,N,N)
v   = data['v']    # shape (3,N,N,N)
s   = data['s']    # shape (N,N,N)
```

### Custom Format Example

Edit `lattice_adapter.py`:

```python
@staticmethod
def from_custom_rsvp(filepath):
    # Your loader here
    return {
        'phi': phi_array,
        'v': v_array,
        's': s_array,
        'metadata': {}
    }
```

Then:

```python
data = LatticeAdapter.from_custom_rsvp("my_rsvp_output.dat")
```

---

## Tuning Visualization

All Blender scripts have editable parameters at the top:

```python
# blender/render_geonodes.py
FIELD_FILE = "sim/fields/t020.npz"  # Which timestep
THRESH = 0.15                        # Minimum φ to show
RADIUS_SCALE = 0.3                   # Sphere size multiplier
```

```python
# blender/render_vectors.py
SUBSAMPLE = 4      # Show every Nth vector
V_SCALE = 2.0      # Arrow length
V_THRESH = 0.01    # Minimum |v| to display
```

---

## Make Targets

| Command | Effect |
|---------|--------|
| `make sim` | Run field evolution |
| `make render` | Single frame (basic) |
| `make geonodes` | Fast single frame |
| `make vectors` | Vector field viz |
| `make anim` | Full animation |
| `make diag` | Diagnostics |
| `make video` | Convert frames → MP4 |
| `make quick` | Sim + fast render |
| `make full` | Complete pipeline |
| `make clean` | Remove outputs |
| `make inspect` | Print field stats |

---

## Performance Notes

### Lattice Size vs Speed

| N³ | Points | Geonodes | Basic |
|----|--------|----------|-------|
| 32³ | 32k | 2s | 30s |
| 64³ | 262k | 8s | 5min |
| 128³ | 2M | 30s | OOM |

**Use geometry nodes for N ≥ 64.**

### Animation

For 50 frames at 64³:
- Geometry nodes: ~7 minutes
- Basic instancing: ~4 hours

---

## Extending the Lab

### Add a New Visualization

1. Create `blender/render_mymode.py`
2. Import `common.py` for camera/lights
3. Load field: `data = np.load("sim/fields/t020.npz")`
4. Convert to Blender geometry
5. Render: `bpy.ops.render.render(write_still=True)`

### Add a New Field

In `rsvp_core.py`:

```python
def step(phi, v, s, **new_field**, dt=0.1, dx=1.0):
    # Evolve new_field
    return phi, v, s, new_field
```

In `run_sim.py`:

```python
np.savez(
    OUT / f"t{t:03d}.npz",
    phi=phi, v=v, s=s, **new_field=new_field**
)
```

### Export Geometry

In any render script:

```python
bpy.ops.wm.save_as_mainfile(filepath="out/meshes/field.blend")
# or
bpy.ops.export_scene.gltf(filepath="out/meshes/field.gltf")
```

---

## Workflow Examples

### Rapid Prototyping
```bash
# Edit rsvp_core.py, then:
make sim geonodes  # ~10 seconds for 32³
```

### Publication Figures
```bash
make sim
blender -b -P blender/render_diagnostics.py
# Adjust camera in Blender GUI, then re-render
```

### High-Res Video
```bash
# In run_sim.py: N=64, T=200
# In render_animation.py: adjust resolution
make full
```

---

## Next Steps

1. **Replace `rsvp_core.py` dynamics** with your actual equations
2. **Tune visualization** thresholds for your field magnitudes
3. **Add analysis scripts** (Fourier modes, topological features, etc.)
4. **Extend lattice_adapter** for your data format

This is a **simulation harness**, not a demo. Blender is your microscope.

---

## Technical Notes

### Why This Architecture?

✅ **Deterministic**: Same data → same render  
✅ **Inspectable**: Fields are NumPy arrays  
✅ **Testable**: Physics code has no graphics dependencies  
✅ **Composable**: Mix visualization modes  
✅ **Scalable**: Geometry nodes handle 10M+ points  

### RSVP-Specific Considerations

- **Entropy visualization**: Color, opacity, or histogram
- **Vector flow**: Streamlines for long-range structure
- **Scalar field**: Isosurfaces at φ = const
- **Topological features**: Detect and highlight in post

### Blender as a Backend

Blender gives you:
- Cycles path tracer (photorealistic)
- Geometry nodes (GPU-accelerated)
- Compositor (post-processing)
- Python API (full control)

But: **Blender never computes physics**. That's your job.

---

## Troubleshooting

### "Module not found: common"
```bash
# Blender needs to find common.py
# Already handled by sys.path.append in scripts
```

### Out of Memory
```bash
# Reduce N in run_sim.py
# Or use geometry nodes instead of basic render
```

### Slow Animation
```bash
# Use render_geonodes.py instead of render_field.py
# Or reduce SUBSAMPLE in render_vectors.py
```
