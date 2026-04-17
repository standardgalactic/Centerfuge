"""
generate_landscape.py — headless Blender landscape generator using the rsvp suite.

Usage:
    blender --background --python generate_landscape.py -- \
        --output /tmp/rsvp_landscape.blend \
        --seed 7 \
        --resolution 128 \
        --size 10.0 \
        --height-scale 1.8 \
        --seam-axis x \
        --seam-position 0.0 \
        --seam-width 0.2 \
        --add-water

Produces a displaced mesh terrain with optional water plane and seam artifact,
suitable for use as a station exterior or surface environment in KOMMUNIKATION.

The terrain scalar is built from the rsvp landscape preset, optionally
perturbed by a seam displacement field that produces TARTAN-style gluing
artifacts along a configurable axis.
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

    parser = argparse.ArgumentParser(description="RSVP headless landscape generator")
    parser.add_argument("--output", default="/tmp/rsvp_landscape.blend")
    parser.add_argument("--seed", type=int, default=0)

    # Grid
    parser.add_argument("--resolution", type=int, default=64,
                        help="Vertices per side (64 = 64x64 grid)")
    parser.add_argument("--size", type=float, default=10.0,
                        help="World-space width and depth of terrain")

    # Height
    parser.add_argument("--height-scale", type=float, default=1.5)
    parser.add_argument("--bounds-scale", type=float, default=1.2,
                        help="Field sample bounds (larger = more of the field)")

    # Seam
    parser.add_argument("--seam-axis", default="x", choices=["x", "y", "z"])
    parser.add_argument("--seam-position", type=float, default=0.0)
    parser.add_argument("--seam-width", type=float, default=0.18)
    parser.add_argument("--seam-offset-x", type=float, default=0.2)
    parser.add_argument("--seam-offset-y", type=float, default=0.0)
    parser.add_argument("--seam-twist", type=float, default=0.0)
    parser.add_argument("--no-seam", action="store_true",
                        help="Disable seam artifact entirely")

    # Water
    parser.add_argument("--add-water", action="store_true")
    parser.add_argument("--water-level", type=float, default=0.0)

    # Materials
    parser.add_argument("--rock-color", nargs=3, type=float,
                        default=[0.18, 0.16, 0.14],
                        metavar=("R", "G", "B"))
    parser.add_argument("--seam-color", nargs=3, type=float,
                        default=[0.05, 0.05, 0.08],
                        metavar=("R", "G", "B"))

    return parser.parse_args(argv)


args = parse_args()

import bpy
import bmesh
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import rsvp


# ---------------------------------------------------------------------------
# Field setup
# ---------------------------------------------------------------------------

rng = random.Random(args.seed)

landscape_ops = rsvp.make_landscape_operators()
terrain: rsvp.ScalarFn = landscape_ops["terrain"]   # type: ignore[assignment]

# Optionally layer in a second harmonic with a random phase offset
# to break the preset's bilateral symmetry
extra = rsvp.HarmonicField(
    weights=(rng.uniform(0.3, 0.8), rng.uniform(0.3, 0.8), 0.0),
    frequencies=(rng.uniform(2.0, 4.5), rng.uniform(1.5, 3.5), 0.0),
    phase=(rng.uniform(0, 6.28), rng.uniform(0, 6.28), 0.0),
    amplitude=rng.uniform(0.12, 0.25),
).scalar()

terrain = rsvp.add_scalar_fields(terrain, extra)

# Closure field — used to modulate seam visibility and as a debug channel
phi, v_field, closure = rsvp.make_default_rsvp_field()


# ---------------------------------------------------------------------------
# Height map evaluation
# ---------------------------------------------------------------------------

N = args.resolution
B = args.bounds_scale
hmap = rsvp.sample_height_map(
    terrain,
    nx=N, ny=N,
    bounds_min=(-B, -B),
    bounds_max=(B, B),
    z_scale=args.height_scale,
)

# Seam metric map — same grid, used for material masking
if not args.no_seam:
    seam_map = [
        [
            rsvp.seam_obstruction_metric(
                x=(ix / max(N - 1, 1)) * 2 * B - B,
                y=(iy / max(N - 1, 1)) * 2 * B - B,
                z=0.0,
                seam_axis=args.seam_axis,
                seam_position=args.seam_position,
                width=args.seam_width,
            )
            for iy in range(N)
        ]
        for ix in range(N)
    ]
else:
    seam_map = [[0.0] * N for _ in range(N)]

print(f"[rsvp] height map: {N}x{N}  "
      f"min={min(h for row in hmap for h in row):.3f}  "
      f"max={max(h for row in hmap for h in row):.3f}")


# ---------------------------------------------------------------------------
# Apply seam displacement to xy positions if requested
# ---------------------------------------------------------------------------

def displaced_xy(ix: int, iy: int) -> tuple[float, float]:
    """Return world-space xy after seam displacement."""
    raw_x = rsvp.lerp(-args.size / 2, args.size / 2, ix / max(N - 1, 1))
    raw_y = rsvp.lerp(-args.size / 2, args.size / 2, iy / max(N - 1, 1))
    if args.no_seam:
        return raw_x, raw_y
    # Normalise to field coords for seam_displacement, then rescale
    fx = rsvp.lerp(-B, B, ix / max(N - 1, 1))
    fy = rsvp.lerp(-B, B, iy / max(N - 1, 1))
    dx, dy, _ = rsvp.seam_displacement(
        fx, fy, 0.0,
        seam_axis=args.seam_axis,
        seam_position=args.seam_position,
        width=args.seam_width,
        offset=(args.seam_offset_x, args.seam_offset_y, 0.0),
        twist=args.seam_twist,
    )
    # Map displaced field coords back to world space
    world_x = (dx + B) / (2 * B) * args.size - args.size / 2
    world_y = (dy + B) / (2 * B) * args.size - args.size / 2
    return world_x, world_y


# ---------------------------------------------------------------------------
# Blender scene setup
# ---------------------------------------------------------------------------

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()


# ---------------------------------------------------------------------------
# Build terrain mesh via bmesh
# ---------------------------------------------------------------------------

bm = bmesh.new()

# Create vertex grid
verts: list[list[bmesh.types.BMVert]] = []
for ix in range(N):
    row = []
    for iy in range(N):
        wx, wy = displaced_xy(ix, iy)
        wz = hmap[ix][iy]
        row.append(bm.verts.new((wx, wy, wz)))
    verts.append(row)

# Create faces
for ix in range(N - 1):
    for iy in range(N - 1):
        v00 = verts[ix][iy]
        v10 = verts[ix + 1][iy]
        v11 = verts[ix + 1][iy + 1]
        v01 = verts[ix][iy + 1]
        try:
            bm.faces.new((v00, v10, v11, v01))
        except ValueError:
            pass  # duplicate face guard

bm.normal_update()

terrain_mesh = bpy.data.meshes.new("TerrainMesh")
bm.to_mesh(terrain_mesh)
bm.free()

terrain_obj = bpy.data.objects.new("Terrain", terrain_mesh)
bpy.context.scene.collection.objects.link(terrain_obj)

# Smooth shading
for poly in terrain_mesh.polygons:
    poly.use_smooth = True

# Add edge-split modifier to preserve seam hard edges
edge_split = terrain_obj.modifiers.new("EdgeSplit", "EDGE_SPLIT")
edge_split.split_angle = 0.6   # ~35 degrees


# ---------------------------------------------------------------------------
# Vertex colour layer for seam masking
# ---------------------------------------------------------------------------

terrain_mesh.vertex_colors.new(name="SeamMask")
color_layer = terrain_mesh.vertex_colors["SeamMask"]

# Map vertex index -> flat ix, iy for seam lookup
flat_idx = {(ix * N + iy): (ix, iy) for ix in range(N) for iy in range(N)}

for poly in terrain_mesh.polygons:
    for loop_idx in poly.loop_indices:
        vert_idx = terrain_mesh.loops[loop_idx].vertex_index
        # Recover ix, iy from linear index (robust fallback)
        ix = vert_idx // N
        iy = vert_idx % N
        if ix < N and iy < N:
            s = seam_map[ix][iy]
        else:
            s = 0.0
        color_layer.data[loop_idx].color = (s, s, s, 1.0)


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------

def make_terrain_material() -> bpy.types.Material:
    mat = bpy.data.materials.new("TerrainMaterial")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    mix = nodes.new("ShaderNodeMixShader")

    # Rock / ground BSDF
    rock = nodes.new("ShaderNodeBsdfPrincipled")
    rc = args.rock_color
    rock.inputs["Base Color"].default_value = (*rc, 1.0)
    rock.inputs["Roughness"].default_value = 0.90
    specular_key = "Specular IOR Level" if "Specular IOR Level" in rock.inputs else "Specular"
    rock.inputs[specular_key].default_value = 0.02

    # Seam material — darker, slightly emissive to read on screen
    seam_bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    sc = args.seam_color
    seam_bsdf.inputs["Base Color"].default_value = (*sc, 1.0)
    seam_bsdf.inputs["Roughness"].default_value = 0.6
    emission_key = "Emission Color" if "Emission Color" in seam_bsdf.inputs else "Emission"
    seam_bsdf.inputs[emission_key].default_value = (*[c * 0.4 for c in sc], 1.0)
    seam_bsdf.inputs["Emission Strength"].default_value = 0.3

    # Vertex colour drives the mix
    vcol = nodes.new("ShaderNodeVertexColor")
    vcol.layer_name = "SeamMask"

    # Smooth the mask slightly
    smooth = nodes.new("ShaderNodeMath")
    smooth.operation = "SMOOTH_MIN"
    smooth.inputs[1].default_value = 1.0
    smooth.inputs[2].default_value = 0.15

    links.new(vcol.outputs["Color"], smooth.inputs[0])
    links.new(smooth.outputs["Value"], mix.inputs["Fac"])
    links.new(rock.outputs["BSDF"], mix.inputs[1])
    links.new(seam_bsdf.outputs["BSDF"], mix.inputs[2])
    links.new(mix.outputs["Shader"], out.inputs["Surface"])

    return mat

terrain_obj.data.materials.append(make_terrain_material())


# ---------------------------------------------------------------------------
# Optional water plane
# ---------------------------------------------------------------------------

if args.add_water:
    bpy.ops.mesh.primitive_plane_add(
        size=args.size * 1.05,
        location=(0.0, 0.0, args.water_level),
    )
    water_obj = bpy.context.active_object
    water_obj.name = "Water"

    water_mat = bpy.data.materials.new("WaterMaterial")
    water_mat.use_nodes = True
    w_nodes = water_mat.node_tree.nodes
    w_links = water_mat.node_tree.links
    w_nodes.clear()

    w_out = w_nodes.new("ShaderNodeOutputMaterial")
    w_bsdf = w_nodes.new("ShaderNodeBsdfPrincipled")
    w_bsdf.inputs["Base Color"].default_value = (0.03, 0.06, 0.12, 1.0)
    w_bsdf.inputs["Roughness"].default_value = 0.03
    transmission_key = "Transmission Weight" if "Transmission Weight" in w_bsdf.inputs else "Transmission"
    w_bsdf.inputs[transmission_key].default_value = 0.85
    w_bsdf.inputs["IOR"].default_value = 1.33
    w_links.new(w_bsdf.outputs["BSDF"], w_out.inputs["Surface"])

    water_mat.blend_method = "BLEND"
    water_obj.data.materials.append(water_mat)


# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------

cam_data = bpy.data.cameras.new("Camera")
cam_data.lens = 35.0
cam_obj = bpy.data.objects.new("Camera", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)

half = args.size / 2
cam_obj.location = (half * 1.2, -half * 1.4, half * 0.9)
cam_obj.rotation_euler = (1.05, 0.0, 0.65)
bpy.context.scene.camera = cam_obj


# ---------------------------------------------------------------------------
# Lighting — sun + weak fill
# ---------------------------------------------------------------------------

sun_data = bpy.data.lights.new("Sun", type="SUN")
sun_data.energy = 4.0
sun_data.angle = 0.05
sun_obj = bpy.data.objects.new("Sun", sun_data)
bpy.context.scene.collection.objects.link(sun_obj)
sun_obj.rotation_euler = (0.5, 0.0, -1.1)

fill_data = bpy.data.lights.new("Fill", type="AREA")
fill_data.energy = 80.0
fill_data.size = args.size * 0.6
fill_obj = bpy.data.objects.new("Fill", fill_data)
bpy.context.scene.collection.objects.link(fill_obj)
fill_obj.location = (0.0, 0.0, args.size * 1.5)
fill_obj.rotation_euler = (0.0, 0.0, 0.0)

# World sky
world = bpy.context.scene.world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.01, 0.01, 0.015, 1.0)
    bg.inputs["Strength"].default_value = 0.4


# ---------------------------------------------------------------------------
# Render settings (Cycles, quick preview quality)
# ---------------------------------------------------------------------------

bpy.context.scene.render.engine = "CYCLES"
bpy.context.scene.cycles.samples = 64
bpy.context.scene.cycles.use_denoising = True
bpy.context.scene.render.resolution_x = 1920
bpy.context.scene.render.resolution_y = 1080


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

bpy.ops.wm.save_as_mainfile(filepath=args.output)
print(f"[rsvp] saved landscape to {args.output}")
print(f"[rsvp] seam axis={args.seam_axis}  water={args.add_water}  "
      f"verts={N * N}  faces={(N-1) * (N-1)}")