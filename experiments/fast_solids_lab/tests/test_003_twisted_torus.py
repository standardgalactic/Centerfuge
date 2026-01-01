import bpy, math, sys, os
from pathlib import Path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import common

common.reset()
common.camera()

bpy.ops.mesh.primitive_torus_add(
    major_radius=1.2,
    minor_radius=0.4,
    major_segments=48,
    minor_segments=16
)
obj = bpy.context.object

for v in obj.data.vertices:
    theta = math.atan2(v.co.y, v.co.x)
    twist = 0.8 * math.sin(3 * theta)
    r = math.hypot(v.co.x, v.co.y)

    v.co.z += 0.25 * math.sin(2 * theta)
    v.co.x = (r + 0.15*math.cos(4*theta)) * math.cos(theta + twist)
    v.co.y = (r + 0.15*math.cos(4*theta)) * math.sin(theta + twist)

bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.normals_make_consistent()
bpy.ops.object.mode_set(mode='OBJECT')

obj.data.materials.append(
    common.material("Torus", (0.3, 0.7, 0.9, 1))
)

out = Path(__file__).resolve().parent.parent / "out/twisted_torus"
common.finish(out)

