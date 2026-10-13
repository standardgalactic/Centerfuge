"""Show three times of the network run as three globes, node colour from stock, and ask the image what it holds.

    python3 network_scene.py out.png          (Blender's Python module; reads network_states.json)

Colour carries the stock: a sequential ramp (viridis, 256 steps) applied to stock divided by the
largest stock in the whole run, so the three globes are comparable. Markers have one size, so that
colour is the only carrier. Stock below zero is clamped to the bottom of the ramp, as in the
Chapter 6 export script, which means the image cannot show a negative stock.
"""
import json
import math
import sys

import bpy
import numpy as np
from mathutils import Vector

from arrangement_family import family_normals
from arrangement_scene import diffuse_material, emission_material

FRAMES = (5, 20, 120)           # saved-state indices; one saved state is one time unit
OFFSETS = (-2.6, 0.0, 2.6)


def ramp():
    import matplotlib
    cmap = matplotlib.colormaps['viridis']
    return [tuple(int(round(255 * c)) for c in cmap(i / 255)[:3]) for i in range(256)]


def to_index(x, peak):
    return int(round(255 * min(max(x, 0.0), peak) / peak))


def build(path_json='network_states.json'):
    data = json.load(open(path_json))
    pos = np.array(data['pos'])
    states = np.array(data['states'])
    peak = float(states.max())
    colours = ramp()

    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.view_settings.view_transform = 'Standard'
    sc.render.resolution_x, sc.render.resolution_y = 1500, 560
    sc.world = bpy.data.worlds.new('World')
    sc.world.use_nodes = True
    bg = sc.world.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.004, 0.005, 0.008, 1)
    bg.inputs['Strength'].default_value = 1.0

    def mesh_of(op, **kw):
        op(**kw)
        o = bpy.context.object
        m = o.data
        bpy.data.objects.remove(o)
        return m

    globe_mesh = mesh_of(bpy.ops.mesh.primitive_uv_sphere_add, radius=1.0, segments=64, ring_count=32)
    globe_mesh.materials.append(diffuse_material('Globe', (22, 30, 44), 0.7))
    for p in globe_mesh.polygons:
        p.use_smooth = True
    R = 1.015
    tube_mesh = mesh_of(bpy.ops.mesh.primitive_torus_add, major_radius=R, minor_radius=0.008,
                        major_segments=128, minor_segments=8)
    tube_mesh.materials.append(diffuse_material('Tube', (120, 124, 130), 0.5))
    marker_mesh = mesh_of(bpy.ops.mesh.primitive_uv_sphere_add, radius=0.05, segments=24, ring_count=12)
    marker_mesh.materials.append(emission_material('placeholder', (0, 0, 0)))
    normals = family_normals(22.5 * math.pi / 180, 30 * math.pi / 180)    # the arrangement the network is built on

    markers = {}
    for gi, (k, dx) in enumerate(zip(FRAMES, OFFSETS)):
        g = bpy.data.objects.new(f'Globe {k}', globe_mesh)
        sc.collection.objects.link(g)
        g.location = (dx, 0, 0)
        for i, n in enumerate(normals):
            o = bpy.data.objects.new(f'Circle {k}.{i}', tube_mesh)
            sc.collection.objects.link(o)
            o.location = (dx, 0, 0)
            o.rotation_euler = Vector(n).to_track_quat('Z', 'Y').to_euler()
        for j, p in enumerate(pos):
            o = bpy.data.objects.new(f'Node {k}.{j}', marker_mesh)
            sc.collection.objects.link(o)
            o.location = (dx + R * p[0], R * p[1], R * p[2])
            idx = to_index(states[k][j], peak)
            o.material_slots[0].link = 'OBJECT'
            o.material_slots[0].material = emission_material(f'Stock {k}.{j}', colours[idx])
            o['frame'], o['node'], o['index'] = k, j, idx
            markers[(k, j)] = o

    az, el, dist = 0.0, math.radians(26), 14.0
    cam = bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera'))
    sc.collection.objects.link(cam)
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = 7.4
    cam.location = (0.0, -dist * math.cos(el), dist * math.sin(el))
    cam.rotation_euler = (-cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam
    for name, loc, power, size, color in (('Key', (-4.0, -5.0, 6.0), 1800, 5.0, (1.0, 0.97, 0.92)),
                                          ('Rim', (5.0, 4.0, 4.0), 800, 5.0, (0.7, 0.8, 1.0))):
        L = bpy.data.lights.new(name, 'AREA')
        L.energy, L.size, L.color = power, size, color
        lo = bpy.data.objects.new(name, L)
        sc.collection.objects.link(lo)
        lo.location = loc
        lo.rotation_euler = (-Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return sc, cam, markers, states, peak, colours


def reachable(sc, cam, o):
    from bpy_extras.object_utils import world_to_camera_view
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    origin = cam.matrix_world.translation.copy()
    t = o.matrix_world.translation
    uv = world_to_camera_view(sc, cam, t)
    if not (0 <= uv.x <= 1 and 0 <= uv.y <= 1):
        return False, None
    view = (cam.matrix_world.to_3x3() @ Vector((0, 0, -1))).normalized()   # orthographic: every ray runs along the view axis
    start = t - view * 30.0
    ok, loc, n, idx, hit, mat = sc.ray_cast(dg, start, view, distance=30.0 * 0.9995)
    return ((not ok) or hit == o), (uv.x, uv.y)


def read_back(path, sc, cam, markers, states, peak, colours, pos):
    """Recover each reachable node's stock from the colour at its projected centre.

    Returns, for nodes facing the camera by more than 0.2 (cosine of the angle between the outward
    normal and the direction to the camera) and for the grazing rest, the number of nodes and the
    stock errors as a fraction of the peak."""
    from PIL import Image
    a = np.asarray(Image.open(path).convert('RGB')).astype(int)
    W, H = a.shape[1], a.shape[0]
    table = np.array(colours)
    bpy.context.view_layer.update()
    view = (cam.matrix_world.to_3x3() @ Vector((0, 0, -1))).normalized()
    groups = {'facing': [], 'grazing': []}
    total = 0
    for (k, j), o in markers.items():
        total += 1
        ok, uv = reachable(sc, cam, o)
        if not ok:
            continue
        px, py = int(round(uv[0] * W)), int(round((1 - uv[1]) * H))
        rgb = np.median(a[py - 1:py + 2, px - 1:px + 2].reshape(-1, 3), axis=0)
        idx = int(np.argmin(((table - rgb) ** 2).sum(axis=1)))
        err = abs(idx / 255 * peak - min(max(states[k][j], 0.0), peak)) / peak
        facing = float(-view.dot(Vector(pos[j])))
        groups['facing' if facing > 0.2 else 'grazing'].append(err)
    return total, {g: np.array(v) for g, v in groups.items()}


if __name__ == '__main__':
    out = sys.argv[1]
    sc, cam, markers, states, peak, colours = build()
    if not (len(sys.argv) > 2 and sys.argv[2] == 'analyse'):
        sc.render.image_settings.file_format = 'PNG'
        sc.render.filepath = out
        bpy.ops.render.render(write_still=True)
    pos = np.array(json.load(open('network_states.json'))['pos'])
    total, g = read_back(out, sc, cam, markers, states, peak, colours, pos)
    print(f'{total} markers in the scene')
    for name, e in g.items():
        bad = int((e > 0.01).sum())
        good = e[e <= 0.01]
        print(f'{name:8s}: {len(e)} reachable; {bad} misread by more than 1 percent of peak; '
              f'max error of the rest {100 * good.max():.3f} percent, median {100 * np.median(e):.3f} percent')
