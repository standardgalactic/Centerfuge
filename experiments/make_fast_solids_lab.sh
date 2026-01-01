#!/usr/bin/env bash
set -e

LAB="${1:-fast_solids_lab}"
mkdir -p "$LAB"/{tests,out}

########################
# common.py (FAST)
########################
cat > "$LAB/common.py" << 'EOF'
import bpy, math
from pathlib import Path

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 1280

    # World light (never black)
    world = scene.world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Strength"].default_value = 1.2

def camera():
    bpy.ops.object.camera_add(location=(4,-4,3), rotation=(1.1,0,0.8))
    bpy.context.scene.camera = bpy.context.object

def material(name, color):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = 0.4
    return m

def finish(outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(outdir/"scene.blend"))
    bpy.context.scene.render.filepath = str(outdir/"render.png")
    bpy.ops.render.render(write_still=True)
EOF

########################
# Test 000 — Radial scalar solid
########################
cat > "$LAB/tests/test_000_scalar.py" << 'EOF'
import bpy, math, sys, os
from pathlib import Path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import common

common.reset()
common.camera()

# Low-poly sphere
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.0)
obj = bpy.context.object

# Scalar deformation (VERY LIGHT)
for v in obj.data.vertices:
    r = v.co.length
    v.co *= 1.0 + 0.2*math.exp(-r*r)

# Fix normals
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.normals_make_consistent()
bpy.ops.object.mode_set(mode='OBJECT')

obj.data.materials.append(
    common.material("Scalar", (0.2,0.8,0.4,1))
)

out = Path(__file__).resolve().parent.parent / "out/scalar"
common.finish(out)
EOF

########################
# Test 001 — Axial torsion
########################
cat > "$LAB/tests/test_001_torsion.py" << 'EOF'
import bpy, math, sys, os
from pathlib import Path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import common

common.reset()
common.camera()

bpy.ops.mesh.primitive_cylinder_add(vertices=32, depth=2.0, radius=0.7)
obj = bpy.context.object

for v in obj.data.vertices:
    t = 0.5*v.co.z
    x,y = v.co.x, v.co.y
    v.co.x = x*math.cos(t)-y*math.sin(t)
    v.co.y = x*math.sin(t)+y*math.cos(t)

bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.normals_make_consistent()
bpy.ops.object.mode_set(mode='OBJECT')

obj.data.materials.append(
    common.material("Torsion", (0.3,0.6,0.9,1))
)

out = Path(__file__).resolve().parent.parent / "out/torsion"
common.finish(out)
EOF

echo "✔ Fast solids lab created"
echo "Run:"
echo "  blender -b -P $LAB/tests/test_000_scalar.py"
echo "  blender -b -P $LAB/tests/test_001_torsion.py"

