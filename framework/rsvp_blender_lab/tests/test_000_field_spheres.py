
# test_000_field_spheres.py

import math, os, sys
from pathlib import Path
import bpy

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import common

def field(x,y,z):
    r = (x*x+y*y+z*z)**0.5
    return math.exp(-0.8*r*r)

opts = common.parse_args_after_double_dash()
outdir = Path(__file__).resolve().parent.parent / opts["outdir"]

common.reset_scene()
common.make_camera()
common.make_three_point_lights()
col = common.ensure_collection("Field")

base = common.simple_material("FieldMat",(0.2,0.8,0.4,1),(0.2,1,0.5,1),0)

step = 0.6
for ix in range(-5,6):
    for iy in range(-5,6):
        for iz in range(-5,6):
            x,y,z = ix*step,iy*step,iz*step
            v = field(x,y,z)
            if v < 0.05: continue
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1+0.2*v, location=(x,y,z))
            o = bpy.context.object
            o.data.materials.append(base)
            col.objects.link(o)

bpy.ops.wm.save_as_mainfile(filepath=str(outdir/"scene.blend"))
bpy.context.scene.render.filepath = str(outdir/"render.png")
bpy.ops.render.render(write_still=True)
