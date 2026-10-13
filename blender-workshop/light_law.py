"""Measure how a rendered diffuse patch responds to a point light's power, distance, and angle.

Run with Blender's Python module: python3 light_law.py
Each render is a 64 x 64 OpenEXR so the pixel values are linear radiance, before any view
transform. The patch is a plane with a diffuse material, the world is black, and the only
light is one point light, so the centre pixel responds to that light alone.
"""
import math
import os
import tempfile

import bpy
import numpy as np


def render_patch(power, distance, angle_deg, albedo=0.8, tmp=None):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x = sc.render.resolution_y = 64
    sc.render.image_settings.file_format = 'OPEN_EXR'
    sc.render.image_settings.color_depth = '32'
    sc.view_settings.view_transform = 'Standard'
    sc.world = bpy.data.worlds.new('Black')
    sc.world.use_nodes = True
    sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.0

    mesh = bpy.data.meshes.new('Patch')
    mesh.from_pydata([(-3, -3, 0), (3, -3, 0), (3, 3, 0), (-3, 3, 0)], [], [(0, 1, 2, 3)])
    patch = bpy.data.objects.new('Patch', mesh)
    sc.collection.objects.link(patch)
    mat = bpy.data.materials.new('Diffuse')
    mat.use_nodes = True
    b = mat.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (albedo, albedo, albedo, 1)
    b.inputs['Roughness'].default_value = 1.0
    b.inputs['Specular IOR Level'].default_value = 0.0
    mesh.materials.append(mat)

    a = math.radians(angle_deg)
    light = bpy.data.lights.new('P', 'POINT')
    light.energy = power
    light.shadow_soft_size = 0.0
    lo = bpy.data.objects.new('P', light)
    sc.collection.objects.link(lo)
    lo.location = (distance * math.sin(a), 0.0, distance * math.cos(a))

    cam = bpy.data.objects.new('C', bpy.data.cameras.new('C'))
    sc.collection.objects.link(cam)
    cam.location = (0.0, -6.0, 6.0)
    cam.rotation_euler = (math.radians(45), 0, 0)
    cam.data.lens = 120          # narrow field, so the centre pixel sees the point under the origin
    sc.camera = cam

    path = os.path.join(tmp, 'p.exr')
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(path)
    px = np.array(img.pixels[:]).reshape(64, 64, 4)
    bpy.data.images.remove(img)
    return float(px[30:34, 30:34, 0].mean())


if __name__ == '__main__':
    tmp = tempfile.mkdtemp()
    base = render_patch(1000, 4.0, 0.0, tmp=tmp)
    print('reference (1000 W, distance 4, normal incidence):', round(base, 5))
    print('power scaling  (distance 4, normal): value / reference vs power / 1000')
    for p in (250, 500, 1000, 2000, 4000):
        v = render_patch(p, 4.0, 0.0, tmp=tmp)
        print(f'   power {p:5d}  ratio {v / base:.4f}  expected {p / 1000:.4f}')
    print('distance scaling (1000 W, normal): ratio vs (4/d)^2')
    ds, vs = [], []
    for d in (2.0, 3.0, 4.0, 6.0, 8.0):
        v = render_patch(1000, d, 0.0, tmp=tmp)
        ds.append(d); vs.append(v)
        print(f'   d {d:3.1f}  ratio {v / base:.4f}  expected {(4.0 / d) ** 2:.4f}')
    slope = np.polyfit(np.log(ds), np.log(vs), 1)[0]
    print('   fitted log-log slope', round(float(slope), 4), '(inverse square gives -2)')
    print('angle scaling (1000 W, distance 4): ratio vs cos(theta)')
    for t in (0, 30, 45, 60, 75):
        v = render_patch(1000, 4.0, t, tmp=tmp)
        print(f'   theta {t:2d}  ratio {v / base:.4f}  expected {math.cos(math.radians(t)):.4f}')
