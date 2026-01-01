import bpy, math, sys, os
from mathutils import Vector
from pathlib import Path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import common

common.reset()
common.camera()

def grow_branch(origin, direction, length, radius, depth):
    if depth == 0:
        return

    bpy.ops.mesh.primitive_cylinder_add(
        radius=radius,
        depth=length,
        location=origin + direction * (length/2),
        rotation=direction.to_track_quat('Z','Y').to_euler()
    )
    obj = bpy.context.object

    end = origin + direction * length

    # Two child directions (vector field bifurcation)
    d1 = (direction + Vector((0.3, 0.1, 0.4))).normalized()
    d2 = (direction + Vector((-0.2, -0.3, 0.4))).normalized()

    grow_branch(end, d1, length*0.7, radius*0.7, depth-1)
    grow_branch(end, d2, length*0.7, radius*0.7, depth-1)

grow_branch(
    origin=Vector((0,0,0)),
    direction=Vector((0,0,1)),
    length=1.5,
    radius=0.12,
    depth=4
)

mat = common.material("Tree", (0.35, 0.7, 0.4, 1))
for o in bpy.context.scene.objects:
    if o.type == 'MESH':
        o.data.materials.append(mat)

out = Path(__file__).resolve().parent.parent / "out/fractal_tree"
common.finish(out)

