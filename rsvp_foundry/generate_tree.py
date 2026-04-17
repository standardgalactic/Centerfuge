"""
generate_tree.py — headless Blender tree generator using the rsvp suite.

Usage:
    blender --background --python generate_tree.py -- \
        --output /tmp/rsvp_tree.blend \
        --seed 42 \
        --trunk-steps 80 \
        --branch-count 12

The script builds an RSVP-field-driven tree, converts growth paths to
bevelled curves, assigns a simple bark material, and saves the .blend file.
No GUI required.
"""

from __future__ import annotations
import sys
import argparse
import random

# ---------------------------------------------------------------------------
# Argument parsing — must happen before bpy import so --help works cleanly
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    # Blender passes its own args before '--'; we only want ours after it
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    parser = argparse.ArgumentParser(description="RSVP headless tree generator")
    parser.add_argument("--output", default="/tmp/rsvp_tree.blend")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--trunk-steps", type=int, default=80)
    parser.add_argument("--trunk-step-size", type=float, default=0.06)
    parser.add_argument("--trunk-bevel", type=float, default=0.08)
    parser.add_argument("--branch-probability", type=float, default=0.10)
    parser.add_argument("--branch-count", type=int, default=10)
    parser.add_argument("--branch-steps", type=int, default=35)
    parser.add_argument("--branch-bevel", type=float, default=0.03)
    parser.add_argument("--lateral-strength", type=float, default=0.70)
    parser.add_argument("--curl", type=float, default=0.30)
    return parser.parse_args(argv)

args = parse_args()

# ---------------------------------------------------------------------------
# Now safe to import bpy and rsvp
# ---------------------------------------------------------------------------

import bpy  # noqa: E402  (only available inside Blender)
import sys, os
sys.path.insert(0, os.path.dirname(__file__))  # ensure rsvp package is findable

import rsvp  # noqa: E402


# ---------------------------------------------------------------------------
# Field setup
# ---------------------------------------------------------------------------

rng = random.Random(args.seed)

ops = rsvp.make_tree_operators()
phi: rsvp.ScalarFn = ops["phi"]           # type: ignore[assignment]
v_field: rsvp.VectorFn = ops["v_field"]   # type: ignore[assignment]
grad_phi: rsvp.VectorFn = ops["grad_phi"] # type: ignore[assignment]

# Perturb the directional bias slightly per seed so each tree is unique
perturb = rsvp.DirectionalBias(
    direction=(rng.gauss(0, 0.15), rng.gauss(0, 0.15), 1.0),
    strength=1.0,
    curl=args.curl,
).vector()
v_field = rsvp.add_vector_fields(v_field, perturb)


# ---------------------------------------------------------------------------
# Geometry generation
# ---------------------------------------------------------------------------

trunk_path = rsvp.trace_growth_path(
    start=(0.0, 0.0, 0.0),
    direction_field=v_field,
    scalar_field=None,      # pure flow integration for trunk
    step_size=args.trunk_step_size,
    steps=args.trunk_steps,
)

branches = rsvp.branch_paths(
    root_path=trunk_path,
    direction_field=v_field,
    branch_probability=args.branch_probability,
    max_branches=args.branch_count,
    step_size=0.04,
    branch_steps=args.branch_steps,
    lateral_strength=args.lateral_strength,
    rng=rng,
)

print(f"[rsvp] trunk: {len(trunk_path)} pts  branches: {len(branches)}")


# ---------------------------------------------------------------------------
# Blender scene setup
# ---------------------------------------------------------------------------

# Clear default scene
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()

def points_to_curve(
    points: list[rsvp.Vec3],
    name: str,
    bevel_depth: float,
    collection: bpy.types.Collection,
) -> bpy.types.Object:
    """Convert a list of Vec3 into a NURBS path object with bevel."""
    curve_data = bpy.data.curves.new(name=name, type="CURVE")
    curve_data.dimensions = "3D"
    curve_data.resolution_u = 4
    curve_data.bevel_depth = bevel_depth
    curve_data.bevel_resolution = 3
    curve_data.use_fill_caps = True

    spline = curve_data.splines.new("NURBS")
    spline.points.add(len(points) - 1)   # one point already exists

    for i, (x, y, z) in enumerate(points):
        spline.points[i].co = (x, y, z, 1.0)   # w=1 for NURBS

    spline.use_endpoint_u = True

    obj = bpy.data.objects.new(name, curve_data)
    collection.objects.link(obj)
    return obj


# Create a collection for the tree
tree_col = bpy.data.collections.new("RSVPTree")
bpy.context.scene.collection.children.link(tree_col)

# Trunk
trunk_obj = points_to_curve(
    trunk_path, "trunk", args.trunk_bevel, tree_col
)

# Branches — taper bevel by lateral progress
branch_objs = []
for i, bpath in enumerate(branches):
    # Bevel tapers from trunk_bevel * 0.5 at root to branch_bevel at tip
    bobj = points_to_curve(
        bpath, f"branch_{i:03d}", args.branch_bevel, tree_col
    )
    branch_objs.append(bobj)


# ---------------------------------------------------------------------------
# Material — simple bark (Principled BSDF, no textures, portable)
# ---------------------------------------------------------------------------

bark_mat = bpy.data.materials.new("BarkMaterial")
bark_mat.use_nodes = True
nodes = bark_mat.node_tree.nodes
links = bark_mat.node_tree.links

bsdf = nodes.get("Principled BSDF")
if bsdf is None:
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")

bsdf.inputs["Base Color"].default_value = (0.22, 0.14, 0.08, 1.0)
bsdf.inputs["Roughness"].default_value = 0.85
# Blender 4.x renamed "Specular" to "Specular IOR Level"
specular_key = "Specular IOR Level" if "Specular IOR Level" in bsdf.inputs else "Specular"
bsdf.inputs[specular_key].default_value = 0.05

for obj in [trunk_obj] + branch_objs:
    if obj.data.materials:
        obj.data.materials[0] = bark_mat
    else:
        obj.data.materials.append(bark_mat)


# ---------------------------------------------------------------------------
# Camera and basic lighting (useful for quick batch renders)
# ---------------------------------------------------------------------------

# Camera positioned to frame a unit-scale tree
cam_data = bpy.data.cameras.new("Camera")
cam_obj = bpy.data.objects.new("Camera", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
cam_obj.location = (3.5, -3.5, 2.5)
cam_obj.rotation_euler = (1.1, 0.0, 0.785)
bpy.context.scene.camera = cam_obj

# Key light
sun_data = bpy.data.lights.new("Sun", type="SUN")
sun_data.energy = 3.0
sun_obj = bpy.data.objects.new("Sun", sun_data)
bpy.context.scene.collection.objects.link(sun_obj)
sun_obj.location = (4.0, 2.0, 6.0)
sun_obj.rotation_euler = (0.6, 0.0, -0.8)


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

bpy.ops.wm.save_as_mainfile(filepath=args.output)
print(f"[rsvp] saved to {args.output}")