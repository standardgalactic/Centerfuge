"""Chapter 19: adapted transport networks as one object per edge, width = conductance, colour = flow; read back and re-solve.

    python3 transport_blender.py check|figure
"""
import sys
import numpy as np
import bpy
from transport import adapt, solve, balance_residual, grid
from dla_blender import base_scene
from arrangement_scene import srgb_to_linear

W0, W1 = 0.06, 0.9
N = 16


def flow_material():
    m = bpy.data.materials.new('Flow'); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_type = 'OBJECT'; at.attribute_name = 'flow'
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.0; mr.inputs['From Max'].default_value = 0.5
    cr = nt.nodes.new('ShaderNodeValToRGB'); e = cr.color_ramp.elements
    e[0].position = 0.0; e[0].color = srgb_to_linear([70, 80, 150]); e[1].position = 1.0; e[1].color = srgb_to_linear([255, 215, 80])
    em = nt.nodes.new('ShaderNodeEmission'); out = nt.nodes.new('ShaderNodeOutputMaterial')
    L = nt.links.new
    L(at.outputs['Fac'], mr.inputs['Value']); L(mr.outputs['Result'], cr.inputs['Fac'])
    L(cr.outputs['Color'], em.inputs['Color']); L(em.outputs['Emission'], out.inputs['Surface'])
    return m


def add_network(name, E, D, Q, dx, mesh, seed, mu, steps):
    coll = bpy.data.collections.new(name); bpy.context.scene.collection.children.link(coll)
    for k, (a, b) in enumerate(E):
        ax, ay = divmod(a, N)[1], -divmod(a, N)[0]; bx, by = divmod(b, N)[1], -divmod(b, N)[0]
        o = bpy.data.objects.new(f'{name} {a}-{b}', mesh)
        o.location = (dx + (ax + bx) / 2, (ay + by) / 2, 0)
        horiz = ay == by
        o.scale = (1.0, W0 + W1 * float(D[k]), 0.2) if horiz else (W0 + W1 * float(D[k]), 1.0, 0.2)
        o['a'] = int(a); o['b'] = int(b); o['flow'] = abs(float(Q[k]))
        coll.objects.link(o)
    coll['seed'] = seed; coll['mu'] = mu; coll['steps'] = steps; coll['n'] = N
    return coll


def check():
    sc, me = base_scene(); me.materials.append(flow_material())
    mu, seed, steps = 1.2, 0, 1500
    E, D, Q, p = adapt(N, seed, mu, steps=steps)
    coll = add_network('mu1.2', E, D, Q, 0.0, me, seed, mu, steps)
    bpy.context.view_layer.update()
    objs = list(coll.objects)
    Es = np.array([[o['a'], o['b']] for o in objs])
    Dr = np.array([((o.scale.y if o.scale.x == 1.0 else o.scale.x) - W0) / W1 for o in objs])
    print(f'objects {len(objs)}, meshes {len(bpy.data.meshes)}, users {me.users}, materials {len(bpy.data.materials)}')
    print('edge list read from the scene equals the generated one:', bool((Es == E).all()), '; max |D_scene - D| =', f'{np.abs(Dr - D).max():.1e}')
    p2, Q2 = solve(N, Es, Dr, 0, N * N - 1)
    print('flows re-solved from scene conductances: max |Q - stored flow| =', f'{np.abs(np.abs(Q2) - np.array([o["flow"] for o in objs])).max():.1e}', '; node-balance residual', f'{balance_residual(N, Es, Q2, 0, N * N - 1):.1e}')
    print('edges with D > 0.01:', int((Dr > 0.01).sum()), 'of', len(Dr), '; total D', round(float(Dr.sum()), 3), 'vs', round(float(D.sum()), 3))
    E2, D2, Q2b, _ = adapt(N, int(coll['seed']), float(coll['mu']), steps=int(coll['steps']))
    print('regenerated from stored seed, mu, steps equals the scene:', bool(np.allclose(D2, Dr, atol=1e-5)))


def figure():
    sc, me = base_scene(); me.materials.append(flow_material())
    mus = (0.5, 1.0, 1.2, 1.5)
    for i, mu in enumerate(mus):
        E, D, Q, p = adapt(N, 0, mu, steps=1500)
        add_network(f'mu {mu}', E, D, Q, i * 19.0, me, 0, mu, 1500)
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam)
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 78; cam.location = (3 * 19.0 / 2 + 7.5, -7.5, 50); sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = 1560, 380
    sc.view_settings.view_transform = 'Standard'; sc.eevee.taa_render_samples = 4
    sc.render.image_settings.file_format = 'PNG'; sc.render.filepath = 'figs/fig19_networks.png'
    bpy.ops.render.render(write_still=True)


if __name__ == '__main__':
    {'check': check, 'figure': figure}[sys.argv[1]]()
