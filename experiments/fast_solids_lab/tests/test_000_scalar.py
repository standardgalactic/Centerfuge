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
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode='OBJECT')

obj.data.materials.append(
    common.material("Scalar", (0.2,0.8,0.4,1))
)

out = Path(__file__).resolve().parent.parent / "out/scalar"
common.finish(out)
