
# test_002_entropy_lattice.py

import math, os, sys
from pathlib import Path
import bpy

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import common

opts = common.parse_args_after_double_dash()
outdir = Path(__file__).resolve().parent.parent / opts["outdir"]

common.reset_scene()
common.make_camera((7,-7,6))
common.make_three_point_lights()
col = common.ensure_collection("Entropy")

bpy.ops.mesh.primitive_grid_add(size=6, x_subdivisions=100, y_subdivisions=100)
grid = bpy.context.object
col.objects.link(grid)

mesh = grid.data
for v in mesh.vertices:
    v.co.z = 0.5*math.sin(v.co.x)*math.cos(v.co.y)

mat = common.simple_material("EntropyMat",(0.15,0.7,0.4,1))
grid.data.materials.append(mat)

bpy.ops.object.shade_smooth()

bpy.ops.wm.save_as_mainfile(filepath=str(outdir/"scene.blend"))
bpy.context.scene.render.filepath = str(outdir/"render.png")
bpy.ops.render.render(write_still=True)
