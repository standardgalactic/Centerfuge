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
