"""Chapter 16: a lattice of wall cells in Blender, before and after the smoothing rule.

    python3 occupancy_blender.py check|figure
"""
import sys
import numpy as np
import bpy
from scipy import ndimage
from occupancy import occupy, smooth, smooth_step, open_stats, FOUR
from dla_blender import base_scene
from arrangement_scene import srgb_to_linear


def wall_material():
    """One material for all walls: colour from the object's 'nbrs' property (wall neighbours of eight)."""
    m = bpy.data.materials.new('Wall by neighbours'); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_type = 'OBJECT'; at.attribute_name = 'nbrs'
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0; mr.inputs['From Max'].default_value = 8
    cr = nt.nodes.new('ShaderNodeValToRGB')
    e = cr.color_ramp.elements
    e[0].position = 0.0; e[0].color = srgb_to_linear([240, 190, 90])
    e[1].position = 1.0; e[1].color = srgb_to_linear([60, 40, 110])
    em = nt.nodes.new('ShaderNodeEmission'); out = nt.nodes.new('ShaderNodeOutputMaterial')
    L = nt.links.new
    L(at.outputs['Fac'], mr.inputs['Value']); L(mr.outputs['Result'], cr.inputs['Fac'])
    L(cr.outputs['Color'], em.inputs['Color']); L(em.outputs['Emission'], out.inputs['Surface'])
    return m


def neighbours(wall):
    pad = np.pad(wall, 1, constant_values=True).astype(int)
    return (sum(np.roll(np.roll(pad, i, 0), j, 1) for i in (-1, 0, 1) for j in (-1, 0, 1)) - pad)[1:-1, 1:-1]


def add_grid(name, wall, dx, mesh, seed, p, rule):
    coll = bpy.data.collections.new(name); bpy.context.scene.collection.children.link(coll)
    nb = neighbours(wall)
    for (i, j) in zip(*np.nonzero(wall)):
        o = bpy.data.objects.new(f'{name} {i},{j}', mesh)
        o.location = (dx + float(j), float(-i), 0.0)
        o['nbrs'] = int(nb[i, j]); coll.objects.link(o)
    coll['seed'] = seed; coll['p_wall'] = p; coll['n'] = wall.shape[0]; coll['rule'] = rule
    return coll


def grid_from(coll, dx):
    n = int(coll['n']); g = np.zeros((n, n), bool)
    for o in coll.objects:
        g[int(round(-o.location.y)), int(round(o.location.x - dx))] = True
    return g


def check():
    sc, me = base_scene(); me.materials.append(wall_material())
    n, p, sd = 64, 0.45, 3
    w0 = occupy(n, p, sd); w1, steps, ok = smooth(w0)
    c0 = add_grid('Random', w0, 0.0, me, sd, p, 'occupy'); c1 = add_grid('Smoothed', w1, 80.0, me, sd, p, 'occupy+smooth5of9')
    bpy.context.view_layer.update()
    print(f'objects {len(c0.objects)} + {len(c1.objects)}; wall cells {int(w0.sum())} + {int(w1.sum())}; meshes {len(bpy.data.meshes)}; users of the shared mesh {me.users}; materials {len(bpy.data.materials)}')
    r0 = grid_from(c0, 0.0); r1 = grid_from(c1, 80.0)
    print('grid read back from the scene equals the generated grid:', bool((r0 == w0).all()), bool((r1 == w1).all()))
    print('open components read from the scene:', open_stats(r0)[0], '->', open_stats(r1)[0], '; largest open fraction', round(open_stats(r0)[1], 3), '->', round(open_stats(r1)[1], 3))
    again = smooth(occupy(int(c1["n"]), float(c1["p_wall"]), int(c1["seed"])))[0]
    print('smoothed grid regenerated from stored seed equals the scene:', bool((again == r1).all()), '; fixed point reached in', steps, 'steps:', ok)
    print('one more rule step leaves the scene grid unchanged:', bool((smooth_step(r1) == r1).all()))


def figure():
    sc, me = base_scene(); me.materials.append(wall_material())
    n, p, sd = 48, 0.45, 3
    w0 = occupy(n, p, sd); w1, steps, ok = smooth(w0)
    add_grid('Random', w0, -27.0 - n / 2, me, sd, p, 'occupy'); add_grid('Smoothed', w1, 27.0 - n / 2 + 0.0, me, sd, p, 'smooth')
    # floor tint behind each panel
    for cx in (-27.0, 27.0):
        bm = bpy.data.meshes.new('F'); bm.from_pydata([(-24.5, -24.5, -1), (24.5, -24.5, -1), (24.5, 24.5, -1), (-24.5, 24.5, -1)], [], [(0, 1, 2, 3)])
        fo = bpy.data.objects.new('Floor', bm); fo.location = (cx, -23.5, 0); sc.collection.objects.link(fo)
        fm = bpy.data.materials.new('Floor'); fm.use_nodes = True
        fm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = tuple(srgb_to_linear([225, 235, 245]))
        fm.node_tree.nodes['Principled BSDF'].inputs['Emission Color'].default_value = tuple(srgb_to_linear([225, 235, 245]))
        fm.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 1.0
        bm.materials.append(fm)
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam)
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 112; cam.location = (0, -23.5, 50); sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = 1500, 700
    sc.view_settings.view_transform = 'Standard'; sc.eevee.taa_render_samples = 4
    sc.render.image_settings.file_format = 'PNG'; sc.render.filepath = 'figs/fig16_caves.png'
    bpy.ops.render.render(write_still=True)
    print('open components', open_stats(w0)[0], '->', open_stats(w1)[0], 'steps', steps)


if __name__ == '__main__':
    {'check': check, 'figure': figure}[sys.argv[1]]()
