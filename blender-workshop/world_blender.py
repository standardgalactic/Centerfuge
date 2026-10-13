"""Chapter 24: the scene as a rendering of state. Geometry is built once; render(state) only sets properties and draws.

    python3 world_blender.py check
"""
import hashlib, os, sys
import numpy as np
import bpy
from world import E, N, SRC, SNK, initial, run, step, state_hash, path_edges, apply
from transport import solve
from dla_blender import base_scene
from transport_blender import flow_material, W0, W1


def build_geometry(scene, mesh):
    """The authored layer: one object per edge, positioned from the grid, with no dependence on state."""
    coll = bpy.data.collections.new('World'); scene.collection.children.link(coll)
    objs = []
    for k, (a, b) in enumerate(E):
        ax, ay = a % N, -(a // N); bx, by = b % N, -(b // N)
        o = bpy.data.objects.new(f'edge {k}', mesh); o.location = ((ax + bx) / 2, (ay + by) / 2, 0)
        o['horizontal'] = int(ay == by); coll.objects.link(o); objs.append(o)
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); scene.collection.objects.link(cam)
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 19; cam.location = (7.5, -7.5, 50); scene.camera = cam
    scene.render.resolution_x = scene.render.resolution_y = 500
    scene.view_settings.view_transform = 'Standard'; scene.eevee.taa_render_samples = 1
    scene.render.image_settings.file_format = 'PNG'
    return objs


def render(scene, objs, state, path):
    """The presentation layer: a function of the state. It reads the state and writes properties on objects, nothing else."""
    p, Q = solve(N, E, state['D'], SRC, SNK)
    for k, o in enumerate(objs):
        w = W0 + W1 * float(state['D'][k])
        o.scale = (1.0, w, 0.2) if o['horizontal'] else (w, 1.0, 0.2)
        o['flow'] = abs(float(Q[k]))
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(path); px = np.array(im.pixels[:], dtype=np.float32); bpy.data.images.remove(im)
    return hashlib.sha1(px.tobytes()).hexdigest()[:12]


def check():
    out = '/tmp/claude-0/-home-claude/927989f5-bbd5-524c-a738-cde2187a9709/scratchpad/w.png'
    sc, me = base_scene(); me.materials.append(flow_material())
    objs = build_geometry(sc, me)
    mu = 1.5
    S = run(initial(0), mu, 300, [])
    h0 = state_hash(S)
    r1 = render(sc, objs, S, out); r2 = render(sc, objs, S, out)
    print('state hash before/after two renders:', h0, state_hash(S), '; pixel hashes of the two renders:', r1, r2)
    # destroy the scene and rebuild the geometry from the authored layer
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)
    objs2 = build_geometry(sc, me)
    r3 = render(sc, objs2, S, out)
    print('pixel hash after deleting every object and rebuilding from geometry and state:', r3, '; equal to the first:', r3 == r1)
    # a difference of state that the picture cannot show
    path = sorted(path_edges(S)); e_path = path[10]; on = set(path)
    off = np.array([k for k in range(len(E)) if k not in on])
    S2 = dict(D=S['D'].copy(), blocked=S['blocked'].copy(), t=S['t']); S2['D'][off] = np.maximum(S2['D'][off], 1e-12)
    r2_ = render(sc, objs2, S2, out)
    print(f'unused edges at D ~ 1e-42 (natural) versus raised to 1e-12: state hashes {state_hash(S)} vs {state_hash(S2)}; pixel hashes {r1} vs {r2_}; images equal: {r2_ == r1}')
    for label, W in (('natural', S), ('raised', S2)):
        T = run(apply(W, ('cut', e_path)), mu, 700, [])
        p, Q = solve(N, E, T['D'], SRC, SNK)
        print(f'  {label}: cut path edge {e_path}, run 400 steps: flow through the cut edge {abs(Q[e_path]):.4f}, kept edges {len(path_edges(T))}, kept edges not on the old path {len(path_edges(T) - on)}')
    # picture of the cut-and-restore world versus the plain world
    log = [(100, 'cut', path[10]), (150, 'restore', path[10])]
    H = run(initial(0), mu, 300, log)
    rH = render(sc, objs2, H, out)
    print('world with cut at 100 and restore at 150, blocked edges now:', int(H['blocked'].sum()), '; same image as the world with no events:', rH == r1)


if __name__ == '__main__':
    {'check': check}[sys.argv[1]]()
