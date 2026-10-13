"""Chapter 17: a branching realisation as one object per edge, sharing a mesh, coloured by generation.

    python3 branching_blender.py check|figure
"""
import math, sys
import numpy as np
import bpy
from branching import gw, layout
from dla_blender import base_scene
from arrangement_scene import srgb_to_linear


def depth_material(d_max):
    m = bpy.data.materials.new('Generation'); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_type = 'OBJECT'; at.attribute_name = 'depth'
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0; mr.inputs['From Max'].default_value = d_max
    cr = nt.nodes.new('ShaderNodeValToRGB'); e = cr.color_ramp.elements
    e[0].position = 0.0; e[0].color = srgb_to_linear([40, 30, 100]); e[1].position = 1.0; e[1].color = srgb_to_linear([245, 200, 60])
    em = nt.nodes.new('ShaderNodeEmission'); out = nt.nodes.new('ShaderNodeOutputMaterial')
    L = nt.links.new
    L(at.outputs['Fac'], mr.inputs['Value']); L(mr.outputs['Result'], cr.inputs['Fac'])
    L(cr.outputs['Color'], em.inputs['Color']); L(em.outputs['Emission'], out.inputs['Surface'])
    return m


def add_tree(name, nodes, dx, mesh, d_max, seed, m, width=0.35, sx=None, sy=2.0, span=100.0):
    pos = layout(nodes)
    sx = sx or span / max(1.0, max(p[0] for p in pos))
    coll = bpy.data.collections.new(name); bpy.context.scene.collection.children.link(coll)
    for i, (par, d) in enumerate(nodes):
        if par < 0:
            continue
        (x0, y0), (x1, y1) = pos[par], pos[i]
        x0, x1 = x0 * sx, x1 * sx; y0, y1 = y0 * sy, y1 * sy
        o = bpy.data.objects.new(f'{name} edge {par}-{i}', mesh)
        o.location = (dx + (x0 + x1) / 2, (y0 + y1) / 2, 0)
        o.rotation_euler = (0, 0, math.atan2(y1 - y0, x1 - x0))
        o.scale = (math.hypot(x1 - x0, y1 - y0), width, 0.2)
        o['depth'] = d; o['parent'] = par; o['child'] = i
        coll.objects.link(o)
    coll['seed'] = seed; coll['m'] = m; coll['nodes'] = len(nodes)
    return coll


def pick_critical(lo=150, hi=300):
    for sd in range(2000):
        nodes, st = gw(1.0, sd, max_gen=400)
        if st == 'extinct' and lo <= len(nodes) <= hi:
            return sd, nodes


def check():
    sc, me = base_scene(); me.materials.append(depth_material(28))
    sd, nodes = pick_critical()
    coll = add_tree('Critical', nodes, 0.0, me, 28, sd, 1.0)
    bpy.context.view_layer.update()
    objs = list(coll.objects)
    edges = [(o['parent'], o['child']) for o in objs]
    n = len(nodes)
    # tree test: n-1 edges, every non-root node has exactly one parent, parents precede children (acyclic), reachable from root
    par = {c: p for p, c in edges}
    ok_one = len(par) == len(edges) == n - 1
    ok_order = all(p < c for p, c in edges)
    depth = {0: 0}
    for p, c in sorted(edges, key=lambda e: e[1]):
        depth[c] = depth[p] + 1
    print(f'seed {sd}: nodes {n}, edge objects {len(objs)}, meshes {len(bpy.data.meshes)}, users of shared mesh {me.users}, materials {len(bpy.data.materials)}')
    print('n-1 edges, one parent each:', ok_one, '; parents precede children:', ok_order, '; stored depth matches recomputed depth:', all(o['depth'] == depth[o['child']] for o in objs))
    # geometry: each edge object's midpoint equals the midpoint of its endpoints in the layout
    pos = layout(nodes); err = 0.0; sx = 100.0 / max(1.0, max(p[0] for p in pos))
    for o in objs:
        (x0, y0), (x1, y1) = pos[o['parent']], pos[o['child']]
        err = max(err, abs(o.location.x - sx * (x0 + x1) / 2), abs(o.location.y - 2.0 * (y0 + y1) / 2))
    print('max midpoint error (float32):', f'{err:.1e}')
    again, st = gw(float(coll['m']), int(coll['seed']), max_gen=400)
    print('regenerated from stored seed and m equals the scene:', again == nodes, '; extinction at depth', max(d for _, d in nodes))
    print('population per generation:', np.bincount([d for _, d in nodes]).tolist())


def figure():
    sc, me = base_scene(); me.materials.append(depth_material(28))
    sdc, nc = pick_critical()
    nsup, sup = None, None
    for sd in range(200):
        nodes, st = gw(1.5, sd, cap=300)
        if st == 'cap' and max(d for _, d in nodes) >= 6:
            sup = nodes; nsup = sd; break
    ca = add_tree('Critical', nc, -110.0, me, 28, sdc, 1.0)
    cb = add_tree('Supercritical', sup, 10.0, me, 28, nsup, 1.5)
    print('critical seed', sdc, len(nc), 'depth', max(d for _, d in nc), '| supercritical seed', nsup, len(sup), 'depth', max(d for _, d in sup))
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam)
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 240; cam.location = (0, -28, 50); sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = 1500, 520
    sc.view_settings.view_transform = 'Standard'; sc.eevee.taa_render_samples = 4
    sc.render.image_settings.file_format = 'PNG'; sc.render.filepath = 'figs/fig17_trees.png'
    bpy.ops.render.render(write_still=True)


if __name__ == '__main__':
    {'check': check, 'figure': figure}[sys.argv[1]]()
