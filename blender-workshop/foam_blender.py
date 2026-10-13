"""Chapter 18: foam cells as one mesh, one polygon per cell, coloured by number of sides through a face attribute.

    python3 foam_blender.py check|figure
"""
import sys
import numpy as np
import bpy
from foam import cells, lloyd, sides, area
from dla_blender import base_scene
from arrangement_scene import srgb_to_linear


def side_material():
    m = bpy.data.materials.new('Sides'); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_type = 'GEOMETRY'; at.attribute_name = 'sides'
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 4; mr.inputs['From Max'].default_value = 8
    cr = nt.nodes.new('ShaderNodeValToRGB'); e = cr.color_ramp.elements
    e[0].position = 0.0; e[0].color = srgb_to_linear([60, 90, 200]); e[1].position = 1.0; e[1].color = srgb_to_linear([230, 70, 60])
    mid = e.new(0.5); mid.color = srgb_to_linear([235, 235, 235])
    em = nt.nodes.new('ShaderNodeEmission'); out = nt.nodes.new('ShaderNodeOutputMaterial')
    L = nt.links.new
    L(at.outputs['Fac'], mr.inputs['Value']); L(mr.outputs['Result'], cr.inputs['Fac'])
    L(cr.outputs['Color'], em.inputs['Color']); L(em.outputs['Emission'], out.inputs['Surface'])
    return m


def build_mesh(name, pts, shrink=1.0, tiles=((0, 0),)):
    cs = cells(pts); verts, faces, sd = [], [], []
    for (tx, ty) in tiles:
        for c in cs:
            ctr = c.mean(axis=0)
            p = ctr + shrink * (c - ctr) + np.array([tx, ty])
            base = len(verts); verts += [(float(x), float(y), 0.0) for x, y in p]
            faces.append(tuple(range(base, base + len(p)))); sd.append(sides(c))
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    at = me.attributes.new('sides', 'INT', 'FACE')
    at.data.foreach_set('value', sd)
    return me


def check():
    base_scene()
    N, seed = 150, 2
    pts0 = np.random.default_rng(seed).random((N, 2)); pts1 = lloyd(pts0, 20)
    for label, pts in (('random', pts0), ('after 20 Lloyd steps', pts1)):
        me = build_mesh(label, pts); me.materials.append(side_material())
        areas = [p.area for p in me.polygons]
        att = [d.value for d in me.attributes['sides'].data]
        nv = [len(p.vertices) for p in me.polygons]
        print(f'{label}: polygons {len(me.polygons)}, total area {sum(areas):.6f}, mean sides {np.mean(att):.4f}, attribute == polygon vertex count: {att == nv}, sides histogram {np.bincount(att)[3:].tolist()} (from 3)')
    again = lloyd(np.random.default_rng(seed).random((N, 2)), 20)
    print('relaxed arrangement regenerated from seed and step count is identical:', bool(np.array_equal(again, pts1)))
    print('mean point displacement under 20 steps (torus units):', round(float(np.mean(np.linalg.norm(((pts1 - pts0 + 0.5) % 1.0) - 0.5, axis=1))), 4))


def figure():
    N, seed = 150, 2
    pts0 = np.random.default_rng(seed).random((N, 2)); pts1 = lloyd(pts0, 20)
    tiles = tuple((i, j) for i in (-1, 0, 1) for j in (-1, 0, 1))
    for name, pts in (('a', pts0), ('b', pts1)):
        sc, _ = base_scene()
        me = build_mesh(name, pts, shrink=0.94, tiles=tiles); me.materials.append(side_material())
        o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
        cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam)
        cam.data.type = 'ORTHO'; cam.data.ortho_scale = 1.0; cam.location = (0.5, 0.5, 5); sc.camera = cam
        sc.render.resolution_x = sc.render.resolution_y = 700
        sc.view_settings.view_transform = 'Standard'; sc.eevee.taa_render_samples = 4
        sc.render.image_settings.file_format = 'PNG'; sc.render.filepath = f'figs/fig18_{name}.png'
        bpy.ops.render.render(write_still=True)
    from PIL import Image
    A = Image.open('figs/fig18_a.png'); B = Image.open('figs/fig18_b.png')
    s = Image.new('RGB', (A.width + B.width + 30, A.height), (255, 255, 255)); s.paste(A, (0, 0)); s.paste(B, (A.width + 30, 0)); s.save('figs/fig18_foam.png')


if __name__ == '__main__':
    {'check': check, 'figure': figure}[sys.argv[1]]()
