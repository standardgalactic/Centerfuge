
# test_001_vortex_torsion.py

import math, os, sys
from pathlib import Path
import bpy

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import common

opts = common.parse_args_after_double_dash()
outdir = Path(__file__).resolve().parent.parent / opts["outdir"]

common.reset_scene()
common.make_camera((8,-8,5))
common.make_three_point_lights()
col = common.ensure_collection("Vortex")

mat = common.simple_material("VortexMat",(0.1,0.9,0.6,1),(0.1,1,0.7,1),0.5)

R = 3
for i in range(64):
    t = 2*math.pi*i/64
    x,y = R*math.cos(t),R*math.sin(t)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.06, depth=1, location=(x,y,0),
        rotation=(0,math.pi/2,t))
    o = bpy.context.object
    o.data.materials.append(mat)
    col.objects.link(o)

bpy.ops.wm.save_as_mainfile(filepath=str(outdir/"scene.blend"))
bpy.context.scene.render.filepath = str(outdir/"render.png")
bpy.ops.render.render(write_still=True)
