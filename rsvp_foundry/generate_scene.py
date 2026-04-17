#!/usr/bin/env python3
"""
generate_scene.py — headless Blender scene composer using the rsvp suite.

Combines a landscape terrain with field-positioned trees into one .blend.
Tree positions are seeded from the landscape closure field so trees cluster
in regions of high field self-sustainability rather than random placement.

Usage:
    blender --background --python generate_scene.py -- \\
        --output /tmp/rsvp_scene.blend \\
        --seed 3 \\
        --tree-count 12 \\
        --resolution 64 \\
        --size 10.0
"""

from __future__ import annotations
import sys
import argparse
import random


def parse_args() -> argparse.Namespace:
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    p = argparse.ArgumentParser(description="RSVP scene composer")
    p.add_argument("--output", required=True)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--tree-count", type=int, default=10)
    p.add_argument("--resolution", type=int, default=64)
    p.add_argument("--size", type=float, default=10.0)
    p.add_argument("--height-scale", type=float, default=1.4)
    p.add_argument("--bounds-scale", type=float, default=1.2)
    p.add_argument("--trunk-steps", type=int, default=60)
    p.add_argument("--branch-count", type=int, default=8)
    p.add_argument("--no-seam", action="store_true")
    return p.parse_args(argv)


args = parse_args()

import bpy
import bmesh
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rsvp

rng = random.Random(args.seed)

# ---------------------------------------------------------------------------
# Fields
# ---------------------------------------------------------------------------

landscape_ops = rsvp.make_landscape_operators()
terrain: rsvp.ScalarFn = landscape_ops["terrain"]   # type: ignore[assignment]

# Extra harmonic variation per seed
extra = rsvp.HarmonicField(
    weights=(rng.uniform(0.3, 0.8), rng.uniform(0.3, 0.8), 0.0),
    frequencies=(rng.uniform(2.0, 4.0), rng.uniform(1.5, 3.5), 0.0),
    phase=(rng.uniform(0, 6.28), rng.uniform(0, 6.28), 0.0),
    amplitude=rng.uniform(0.1, 0.22),
).scalar()
terrain = rsvp.add_scalar_fields(terrain, extra)

tree_ops = rsvp.make_tree_operators()
tree_v: rsvp.VectorFn = tree_ops["v_field"]   # type: ignore[assignment]
tree_phi: rsvp.ScalarFn = tree_ops["phi"]     # type: ignore[assignment]

# Closure field drives tree placement — high closure = good growing region
phi_base, v_base, closure = rsvp.make_default_rsvp_field()

N = args.resolution
B = args.bounds_scale

# ---------------------------------------------------------------------------
# Terrain mesh
# ---------------------------------------------------------------------------

hmap = rsvp.sample_height_map(
    terrain, nx=N, ny=N,
    bounds_min=(-B, -B), bounds_max=(B, B),
    z_scale=args.height_scale,
)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()

bm = bmesh.new()
verts = []
for ix in range(N):
    row = []
    for iy in range(N):
        wx = rsvp.lerp(-args.size / 2, args.size / 2, ix / max(N - 1, 1))
        wy = rsvp.lerp(-args.size / 2, args.size / 2, iy / max(N - 1, 1))
        wz = hmap[ix][iy]
        row.append(bm.verts.new((wx, wy, wz)))
    verts.append(row)

for ix in range(N - 1):
    for iy in range(N - 1):
        try:
            bm.faces.new((verts[ix][iy], verts[ix+1][iy],
                          verts[ix+1][iy+1], verts[ix][iy+1]))
        except ValueError:
            pass

bm.normal_update()
terrain_mesh = bpy.data.meshes.new("TerrainMesh")
bm.to_mesh(terrain_mesh)
bm.free()

terrain_obj = bpy.data.objects.new("Terrain", terrain_mesh)
bpy.context.scene.collection.objects.link(terrain_obj)
for poly in terrain_mesh.polygons:
    poly.use_smooth = True

# Terrain material
mat = bpy.data.materials.new("Ground")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.15, 0.13, 0.10, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.92
terrain_obj.data.materials.append(mat)

print(f"[scene] terrain: {N}x{N} verts")

# ---------------------------------------------------------------------------
# Tree placement via closure field
# ---------------------------------------------------------------------------

# Sample candidate positions where closure > threshold
# Map field coords [-B, B] to world coords [-size/2, size/2]
def field_to_world(fx: float, fy: float) -> tuple[float, float]:
    wx = (fx + B) / (2 * B) * args.size - args.size / 2
    wy = (fy + B) / (2 * B) * args.size - args.size / 2
    return wx, wy

def terrain_z_at(fx: float, fy: float) -> float:
    """Bilinear sample of hmap at field coords."""
    tx = (fx + B) / (2 * B)
    ty = (fy + B) / (2 * B)
    ix = tx * (N - 1)
    iy = ty * (N - 1)
    ix0, iy0 = int(ix), int(iy)
    ix1, iy1 = min(ix0 + 1, N - 1), min(iy0 + 1, N - 1)
    fx_ = ix - ix0
    fy_ = iy - iy0
    h00 = hmap[ix0][iy0]
    h10 = hmap[ix1][iy0]
    h01 = hmap[ix0][iy1]
    h11 = hmap[ix1][iy1]
    return (h00 * (1 - fx_) * (1 - fy_)
            + h10 * fx_ * (1 - fy_)
            + h01 * (1 - fx_) * fy_
            + h11 * fx_ * fy_)

seed_pts = rsvp.seed_points_from_field(
    closure,
    count=args.tree_count,
    bounds_min=(-B * 0.85, -B * 0.85, 0.0),
    bounds_max=( B * 0.85,  B * 0.85, 0.0),
    threshold=0.3,
    rng=rng,
)

print(f"[scene] tree positions found: {len(seed_pts)}")

# ---------------------------------------------------------------------------
# Tree curves
# ---------------------------------------------------------------------------

tree_col = bpy.data.collections.new("Trees")
bpy.context.scene.collection.children.link(tree_col)

bark_mat = bpy.data.materials.new("Bark")
bark_mat.use_nodes = True
bk = bark_mat.node_tree.nodes.get("Principled BSDF")
if bk:
    bk.inputs["Base Color"].default_value = (0.18, 0.11, 0.06, 1.0)
    bk.inputs["Roughness"].default_value = 0.88

def make_tree_curve(pts: list[rsvp.Vec3], name: str, bevel: float) -> bpy.types.Object:
    cd = bpy.data.curves.new(name, "CURVE")
    cd.dimensions = "3D"
    cd.bevel_depth = bevel
    cd.bevel_resolution = 3
    cd.use_fill_caps = True
    sp = cd.splines.new("NURBS")
    sp.points.add(len(pts) - 1)
    for i, (x, y, z) in enumerate(pts):
        sp.points[i].co = (x, y, z, 1.0)
    sp.use_endpoint_u = True
    obj = bpy.data.objects.new(name, cd)
    tree_col.objects.link(obj)
    obj.data.materials.append(bark_mat)
    return obj

for t_idx, (fx, fy, _) in enumerate(seed_pts):
    wx, wy = field_to_world(fx, fy)
    wz = terrain_z_at(fx, fy)

    # Per-tree directional perturbation for variety
    perturb_v = rsvp.add_vector_fields(
        tree_v,
        rsvp.DirectionalBias(
            direction=(rng.gauss(0, 0.2), rng.gauss(0, 0.2), 1.0),
            strength=0.6,
            curl=rng.uniform(0.1, 0.45),
        ).vector(),
    )

    trunk = rsvp.trace_growth_path(
        start=(wx, wy, wz),
        direction_field=perturb_v,
        scalar_field=None,
        step_size=rng.uniform(0.04, 0.07),
        steps=args.trunk_steps,
    )
    make_tree_curve(trunk, f"trunk_{t_idx:03d}", bevel=rng.uniform(0.05, 0.10))

    branches = rsvp.branch_paths(
        root_path=trunk,
        direction_field=perturb_v,
        branch_probability=0.10,
        max_branches=args.branch_count,
        step_size=0.035,
        branch_steps=30,
        lateral_strength=rng.uniform(0.5, 0.8),
        rng=rng,
    )
    for b_idx, bpath in enumerate(branches):
        make_tree_curve(bpath, f"branch_{t_idx:03d}_{b_idx:02d}", bevel=0.025)

print(f"[scene] trees placed: {len(seed_pts)}")

# ---------------------------------------------------------------------------
# Lighting and camera
# ---------------------------------------------------------------------------

half = args.size / 2

cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 28.0
cam_obj = bpy.data.objects.new("Camera", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
cam_obj.location = (half * 1.3, -half * 1.5, half * 0.8)
cam_obj.rotation_euler = (1.05, 0.0, 0.65)
bpy.context.scene.camera = cam_obj

sun_data = bpy.data.lights.new("Sun", type="SUN")
sun_data.energy = 3.5
sun_data.angle = 0.04
sun_obj = bpy.data.objects.new("Sun", sun_data)
bpy.context.scene.collection.objects.link(sun_obj)
sun_obj.rotation_euler = (0.55, 0.0, -1.0)

fill_data = bpy.data.lights.new("Fill", type="AREA")
fill_data.energy = 60.0
fill_data.size = args.size
fill_obj = bpy.data.objects.new("Fill", fill_data)
bpy.context.scene.collection.objects.link(fill_obj)
fill_obj.location = (0.0, 0.0, args.size * 1.4)

world = bpy.context.scene.world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.008, 0.008, 0.012, 1.0)
    bg.inputs["Strength"].default_value = 0.35

bpy.context.scene.render.engine = "CYCLES"
bpy.context.scene.cycles.samples = 64
bpy.context.scene.cycles.use_denoising = True
bpy.context.scene.render.resolution_x = 1920
bpy.context.scene.render.resolution_y = 1080

bpy.ops.wm.save_as_mainfile(filepath=args.output)
print(f"[scene] saved to {args.output}")