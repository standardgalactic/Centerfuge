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
