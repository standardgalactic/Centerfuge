import bpy, math, sys, os
from mathutils import Vector
from pathlib import Path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import common

common.reset()
common.camera()


def make_shape(offset):
    offset = Vector(offset)   # ← FIX

    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=32,
        ring_count=16,
        radius=0.8
    )
    obj = bpy.context.object
    obj.location = offset

    for v in obj.data.vertices:
        p = v.co + offset
        r = p.length
        v.co *= 1.0 + 0.3 * math.sin(3 * r)

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.normals_make_consistent()
    bpy.ops.object.mode_set(mode='OBJECT')

    return obj


a = make_shape((0.7,0,0))
b = make_shape((-0.7,0,0))

mat = common.material("Interlock", (0.4, 0.7, 0.85, 1))
a.data.materials.append(mat)
b.data.materials.append(mat)

out = Path(__file__).resolve().parent.parent / "out/interlocking"
common.finish(out)

