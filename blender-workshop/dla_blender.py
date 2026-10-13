"""Put DLA clusters into Blender as instanced cubes coloured by arrival order, and check what the scene holds.

    python3 dla_blender.py check|figure       (Blender's Python module; needs dla.py)
"""
import math, sys
import numpy as np
import bpy
from dla import dla
from arrangement_scene import srgb_to_linear


def cluster_material(n_max):
    """One material for every particle: colour = viridis ramp of the object's 'order' property divided by n_max."""
    import matplotlib
    cmap = matplotlib.colormaps['viridis']
    m = bpy.data.materials.new('Arrival order'); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_type = 'OBJECT'; at.attribute_name = 'order'
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0; mr.inputs['From Max'].default_value = n_max
    cr = nt.nodes.new('ShaderNodeValToRGB'); cr.color_ramp.interpolation = 'LINEAR'
    els = cr.color_ramp.elements
    els[0].position = 0.0; els[0].color = srgb_to_linear([int(255 * c) for c in cmap(0.0)[:3]])
    els[1].position = 1.0; els[1].color = srgb_to_linear([int(255 * c) for c in cmap(1.0)[:3]])
    for t in (0.2, 0.4, 0.6, 0.8):
        els.new(t).color = srgb_to_linear([int(255 * c) for c in cmap(t)[:3]])
    em = nt.nodes.new('ShaderNodeEmission'); out = nt.nodes.new('ShaderNodeOutputMaterial')
    L = nt.links.new
    L(at.outputs['Fac'], mr.inputs['Value']); L(mr.outputs['Result'], cr.inputs['Fac'])
    L(cr.outputs['Color'], em.inputs['Color']); L(em.outputs['Emission'], out.inputs['Surface'])
    return m


def add_cluster(name, pts, dx, mesh, n_max, seed=None, p=None):
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    for i, (x, y) in enumerate(pts):
        o = bpy.data.objects.new(f'{name} {i}', mesh)
        o.location = (dx + float(x), float(y), 0.0)
        o['order'] = i
        coll.objects.link(o)
    coll['seed'] = -1 if seed is None else seed
    coll['p_stick'] = -1.0 if p is None else p
    return coll


def base_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.world = bpy.data.worlds.new('W'); sc.world.use_nodes = True
    sc.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.004, 0.005, 0.008, 1)
    me = bpy.data.meshes.new('Site')
    h = 0.5
    me.from_pydata([(x, y, z) for x in (-h, h) for y in (-h, h) for z in (-h, h)], [],
                   [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
    me.update()
    return sc, me


def check():
    sc, me = base_scene()
    pts = dla(1000, 7)
    mat = cluster_material(1000); me.materials.append(mat)
    coll = add_cluster('DLA seed 7', pts, 0.0, me, 1000, seed=7, p=1.0)
    bpy.context.view_layer.update()
    objs = list(coll.objects)
    P = np.array([[o.location.x, o.location.y] for o in objs])
    occ = {(int(x), int(y)) for x, y in P}
    # each site after the first touches an earlier site: the scene is the grown cluster, not a pile of points
    ok = all(any((int(x) + dx, int(y) + dy) in occ_before for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) for i, (x, y) in enumerate(P[1:], 1)
             for occ_before in [{(int(a), int(b)) for a, b in P[:i]}])
    print(f'objects {len(objs)}, distinct sites {len(occ)}, meshes {len(bpy.data.meshes)}, users of the shared mesh {me.users}, materials {len(bpy.data.materials)}')
    print('every site touches an earlier site:', ok, '; positions integer:', bool(np.all(P == np.round(P))), '; stored order matches creation index:', all(o['order'] == i for i, o in enumerate(objs)))
    print('provenance on the collection: seed', coll['seed'], 'p_stick', coll['p_stick'])
    again = dla(1000, int(coll['seed']))
    print('cluster regenerated from the stored seed equals the scene:', bool((again == np.array([[int(x), int(y)] for x, y in P])).all()))


def figure():
    from dla import gyration
    sc, me = base_scene()
    n = 2000
    A = dla(n, 11, 1.0); B = dla(n, 11, 0.1)
    mat = cluster_material(n); me.materials.append(mat)
    cA = A.mean(axis=0); cB = B.mean(axis=0)
    add_cluster('Sticky p=1', A - cA, -70.0, me, n); add_cluster('p=0.1', B - cB, 66.0, me, n)
    print('Rg:', gyration(A), gyration(B))
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam)
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 262; cam.location = (0, 0, 50)
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = 1500, 900
    sc.view_settings.view_transform = 'Standard'
    sc.eevee.taa_render_samples = 4
    sc.render.image_settings.file_format = 'PNG'; sc.render.filepath = 'figs/fig15_clusters.png'
    bpy.ops.render.render(write_still=True)


if __name__ == '__main__':
    {'check': check, 'figure': figure}[sys.argv[1]]()
