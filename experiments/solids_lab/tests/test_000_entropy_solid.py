# Entropy-driven deformation of a solid sphere

import math, sys, os
from pathlib import Path
import bpy

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import common

def entropy(r):
    return 0.5 + 0.5 * math.sin(2.2 * r) * math.exp(-0.4 * r)

opts = common.parse_args()
outdir = Path(__file__).resolve().parent.parent / opts["outdir"]

common.reset_scene()
common.camera_default()
common.lights_basic()

col = common.ensure_collection("EntropySolid")

bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=128, ring_count=64)
obj = bpy.context.object
col.objects.link(obj)

mesh = obj.data
for v in mesh.vertices:
    r = v.co.length
    s = entropy(r)
    v.co *= (1.0 + 0.35 * s)

mat = common.material_basic("EntropyMat", (0.15,0.8,0.45,1), rough=0.35)
obj.data.materials.append(mat)

bpy.ops.object.shade_smooth()
common.save_and_render(outdir)
