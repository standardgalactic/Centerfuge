import bpy, math, sys, os
from pathlib import Path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import common

common.reset()
common.camera()

bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=1.0)
obj = bpy.context.object

def envelope(theta, phi):
    return 1.0 + 0.25 * (
        math.cos(6*phi)
        + 0.6*math.sin(4*theta)
        + 0.4*math.cos(3*theta + 2*phi)
    )

for v in obj.data.vertices:
    r = v.co.length
    theta = math.acos(v.co.z / r)
    phi = math.atan2(v.co.y, v.co.x)
    v.co *= envelope(theta, phi)

bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.normals_make_consistent()
bpy.ops.object.mode_set(mode='OBJECT')

obj.data.materials.append(
    common.material("Lobed", (0.85, 0.55, 0.3, 1))
)

out = Path(__file__).resolve().parent.parent / "out/many_lobed"
common.finish(out)

