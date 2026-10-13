"""Render the best antipodal pair of orthographic views of the script's arrangement (Figure 8.1)."""
import numpy as np, bpy, sys
from mathutils import Vector
from view_budget import fib, vertices_of
from arrangement_scene import build
V = vertices_of('source'); dirs = fib(4000)
d = dirs[int(np.abs(dirs @ V.T).min(axis=1).argmax())]
for tag, s in (('a', 1), ('b', -1)):
    sc, cam, markers, info = build('source')
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 2.9
    cam.location = Vector(s * d) * 6
    cam.rotation_euler = (-cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.resolution_x = sc.render.resolution_y = 700
    sc.eevee.taa_render_samples = 32
    sc.render.image_settings.file_format = 'PNG'; sc.render.filepath = f'figs/fig8_view_{tag}.png'
    bpy.ops.render.render(write_still=True)
print('direction', d)
