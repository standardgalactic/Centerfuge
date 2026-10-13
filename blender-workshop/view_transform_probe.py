"""What colour reaches the image for a colour assigned in a material, under each view transform?

Three flat emissive patches carry the three multiplicity colours of arrangement_scene.py. The
camera looks straight at them, the world is black, and the only light is the patch emission, so
the displayed value depends on the colour and the view transform alone.
Run with Blender's Python module: python3 view_transform_probe.py
"""
import os
import tempfile

import bpy
import numpy as np
from PIL import Image

from arrangement_scene import CLASS_RGB, emission_material


def patch_colours(transform, look='None', strength=1.0):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x, sc.render.resolution_y = 96, 32
    sc.view_settings.view_transform = transform
    if look != 'None':
        sc.view_settings.look = look
    sc.world = bpy.data.worlds.new('Black')
    sc.world.use_nodes = True
    sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.0
    for i, (m, rgb) in enumerate(CLASS_RGB.items()):
        mesh = bpy.data.meshes.new(f'P{m}')
        x0 = -3 + 2 * i
        mesh.from_pydata([(x0, -0.9, 0), (x0 + 2, -0.9, 0), (x0 + 2, 0.9, 0), (x0, 0.9, 0)], [], [(0, 1, 2, 3)])
        o = bpy.data.objects.new(f'P{m}', mesh)
        sc.collection.objects.link(o)
        mesh.materials.append(emission_material(f'E{m}', rgb, strength))
    cam = bpy.data.objects.new('C', bpy.data.cameras.new('C'))
    sc.collection.objects.link(cam)
    cam.location = (0, 0, 8)
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = 6.0
    sc.camera = cam
    path = os.path.join(tempfile.mkdtemp(), 'p.png')
    sc.render.image_settings.file_format = 'PNG'
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    a = np.asarray(Image.open(path).convert('RGB'))
    return [tuple(int(v) for v in a[16, 16 + 32 * i]) for i in range(3)]


if __name__ == '__main__':
    print('assigned (sRGB 8-bit):', list(CLASS_RGB.values()))
    for transform, look, strength in (('Standard', 'None', 1.0), ('AgX', 'None', 1.0),
                                      ('AgX', 'AgX - Medium High Contrast', 1.0), ('Standard', 'None', 3.0)):
        print(f'{transform:9s} look={look:28s} emission strength {strength}:', patch_colours(transform, look, strength))
