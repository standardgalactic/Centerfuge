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
