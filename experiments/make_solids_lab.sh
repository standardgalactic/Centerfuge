#!/usr/bin/env bash
# Generate a new Blender bpy experiment suite for theory-driven 3D solids

set -e

LAB_NAME="${1:-solids_lab}"

echo "Creating lab: $LAB_NAME"

mkdir -p "$LAB_NAME"/{tests,out}

############################################
# common.py — shared geometry + render helpers
############################################

cat > "$LAB_NAME/common.py" << 'EOF'
import bpy
import math
from mathutils import Vector
from pathlib import Path

def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 64
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080

def ensure_collection(name):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col

def camera_default():
    cam_data = bpy.data.cameras.new("Camera")
    cam = bpy.data.objects.new("Camera", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = (6, -6, 4)
    cam.rotation_euler = (math.radians(60), 0, math.radians(45))
    bpy.context.scene.camera = cam

def lights_basic():
    def light(name, loc, power):
        l = bpy.data.lights.new(name, 'AREA')
        l.energy = power
        o = bpy.data.objects.new(name, l)
        bpy.context.scene.collection.objects.link(o)
        o.location = loc

    light("Key", (4,-4,6), 2000)
    light("Fill", (-5,-3,3), 800)
    light("Rim", (0,6,4), 1200)

def material_basic(name, color=(0.6,0.6,0.6,1), rough=0.4, emit=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n = m.node_tree.nodes
    n.clear()
    out = n.new("ShaderNodeOutputMaterial")
    bsdf = n.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Emission Strength"].default_value = emit
    m.node_tree.links.new(bsdf.outputs[0], out.inputs[0])
    return m

def save_and_render(outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(outdir / "scene.blend"))
    bpy.context.scene.render.filepath = str(outdir / "render.png")
    bpy.ops.render.render(write_still=True)

def parse_args():
    import sys
    if "--" in sys.argv:
        a = sys.argv[sys.argv.index("--")+1:]
    else:
        a = []
    opts = {"outdir": "out/run"}
    for i,x in enumerate(a):
        if x == "--outdir":
            opts["outdir"] = a[i+1]
    return opts
EOF

############################################
# Test 000 — Entropy-modulated solid
############################################

cat > "$LAB_NAME/tests/test_000_entropy_solid.py" << 'EOF'
# Entropy-driven deformation of a solid sphere

import math, sys, os
from pathlib import Path
import bpy

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import common

def entropy(r):
    return 0.5 + 0.5 * math.sin(2.2 * r) * math.exp(-0.4 * r)

opts = common.parse_args()
outdir = Path(__file__).resolve().parent.parent / opts["outdir"]

common.reset_scene()
common.camera_default()
common.lights_basic()

col = common.ensure_collection("EntropySolid")

bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=128, ring_count=64)
obj = bpy.context.object
col.objects.link(obj)

mesh = obj.data
for v in mesh.vertices:
    r = v.co.length
    s = entropy(r)
    v.co *= (1.0 + 0.35 * s)

mat = common.material_basic("EntropyMat", (0.15,0.8,0.45,1), rough=0.35)
obj.data.materials.append(mat)

bpy.ops.object.shade_smooth()
common.save_and_render(outdir)
EOF

############################################
# Test 001 — Torsion / vector-field solid
############################################

cat > "$LAB_NAME/tests/test_001_torsion_solid.py" << 'EOF'
# Vector-field torsion encoded as axial twist

import math, sys, os
from pathlib import Path
import bpy

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import common

opts = common.parse_args()
outdir = Path(__file__).resolve().parent.parent / opts["outdir"]

common.reset_scene()
common.camera_default()
common.lights_basic()

col = common.ensure_collection("TorsionSolid")

bpy.ops.mesh.primitive_cylinder_add(radius=0.8, depth=3.0, vertices=128)
obj = bpy.context.object
col.objects.link(obj)

mesh = obj.data
for v in mesh.vertices:
    z = v.co.z
    theta = 0.9 * z
    x,y = v.co.x, v.co.y
    v.co.x = x*math.cos(theta) - y*math.sin(theta)
    v.co.y = x*math.sin(theta) + y*math.cos(theta)

mat = common.material_basic("TorsionMat", (0.1,0.6,0.9,1), rough=0.25, emit=0.2)
obj.data.materials.append(mat)

bpy.ops.object.shade_smooth()
common.save_and_render(outdir)
EOF

############################################
# Test 002 — Admissibility shell solid
############################################

cat > "$LAB_NAME/tests/test_002_admissible_shell.py" << 'EOF'
# Shell thickness encodes admissibility constraint

import math, sys, os
from pathlib import Path
import bpy

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import common

def admissibility(theta):
    return 0.4 + 0.3 * math.cos(3*theta)

opts = common.parse_args()
outdir = Path(__file__).resolve().parent.parent / opts["outdir"]

common.reset_scene()
common.camera_default()
common.lights_basic()

col = common.ensure_collection("Shell")

bpy.ops.mesh.primitive_uv_sphere_add(radius=1.2, segments=128, ring_count=64)
obj = bpy.context.object
col.objects.link(obj)

mesh = obj.data
for v in mesh.vertices:
    theta = math.atan2(v.co.y, v.co.x)
    v.co *= admissibility(theta)

mat = common.material_basic("ShellMat", (0.8,0.5,0.2,1), rough=0.5)
obj.data.materials.append(mat)

bpy.ops.object.shade_smooth()
common.save_and_render(outdir)
EOF

echo "✔ Lab created."
echo
echo "Run examples:"
echo "  blender -b -P $LAB_NAME/tests/test_000_entropy_solid.py -- --outdir out/entropy"
echo "  blender -b -P $LAB_NAME/tests/test_001_torsion_solid.py -- --outdir out/torsion"
echo "  blender -b -P $LAB_NAME/tests/test_002_admissible_shell.py -- --outdir out/shell"

