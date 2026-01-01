import bpy, math, sys, os
from pathlib import Path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import common

common.reset()
common.camera()

bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.0)
obj = bpy.context.object

def admissible(theta, phi):
    return 1.0 + 0.25 * (
        math.sin(3*theta)*math.cos(2*phi)
        + 0.5*math.cos(5*phi)
    )

for v in obj.data.vertices:
    r = v.co.length
    theta = math.acos(v.co.z / r)
    phi = math.atan2(v.co.y, v.co.x)
    v.co *= admissible(theta, phi)

bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.normals_make_consistent()
bpy.ops.object.mode_set(mode='OBJECT')

obj.data.materials.append(
    common.material("Star", (0.6, 0.8, 0.3, 1))
)

out = Path(__file__).resolve().parent.parent / "out/star_convex"
common.finish(out)

