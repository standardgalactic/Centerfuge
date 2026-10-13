"""Chapter 9: one geometry, several presentations. What does each presentation let a reader recover about the habitat?

    python3 presentations.py eye|plan|wire|figure        (Blender's Python module)

Question A: what fraction of the interior floor can an observer standing in the doorway, eye height 1.6, see?
Question B: where is the entrance in the south wall?
"""
import itertools, math, os, sys, tempfile
import bpy, numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
from habitat import build, ENTRANCES

CELL, HALF = 0.1, 2.8
N = int(round(2 * HALF / CELL))           # 56 cells per side
EYE_H = 1.6


def scene_setup(entrance):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.world = bpy.data.worlds.new('W'); sc.world.use_nodes = True
    sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0
    coll, gap = build(entrance, sc)
    return sc, coll, gap


def flat_material(name, rgb):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    em = nt.nodes.new('ShaderNodeEmission'); em.inputs['Color'].default_value = (*rgb, 1)
    out = nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
    return m


def position_material(name):
    """Emission colour = (x, y scaled to [0,1] over the interior, 1): the pixel says which floor point it shows."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    geo = nt.nodes.new('ShaderNodeNewGeometry'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    comb = nt.nodes.new('ShaderNodeCombineColor')
    mx = nt.nodes.new('ShaderNodeMath'); my = nt.nodes.new('ShaderNodeMath')
    for mnode in (mx, my):
        mnode.operation = 'MULTIPLY_ADD'
        mnode.inputs[1].default_value = 1 / (2 * HALF); mnode.inputs[2].default_value = 0.5
    em = nt.nodes.new('ShaderNodeEmission'); out = nt.nodes.new('ShaderNodeOutputMaterial')
    comb.inputs['Blue'].default_value = 1.0
    L = nt.links.new
    L(geo.outputs['Position'], sep.inputs['Vector'])
    L(sep.outputs['X'], mx.inputs[0]); L(sep.outputs['Y'], my.inputs[0])
    L(mx.outputs['Value'], comb.inputs['Red']); L(my.outputs['Value'], comb.inputs['Green'])
    L(comb.outputs['Color'], em.inputs['Color']); L(em.outputs['Emission'], out.inputs['Surface'])
    return m


def assign(o, mat):
    o.data.materials.clear(); o.data.materials.append(mat)


def render_exr(sc, path):
    sc.render.image_settings.file_format = 'OPEN_EXR'
    sc.render.image_settings.color_depth = '32'
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(path + '.exr' if not path.endswith('.exr') else path)
    W, H = img.size
    a = np.array(img.pixels[:], dtype=np.float32).reshape(H, W, 4)[::-1]      # row 0 at the top
    bpy.data.images.remove(img)
    return a


def make_camera(sc, loc, rot, lens=None, ortho=None):
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam)
    cam.location = loc; cam.rotation_euler = rot
    if lens: cam.data.lens = lens
    if ortho:
        cam.data.type = 'ORTHO'; cam.data.ortho_scale = ortho
    sc.camera = cam
    bpy.context.view_layer.update()
    return cam


def cell_centres():
    c = -HALF + CELL * (np.arange(N) + 0.5)
    return [(i, j, c[i], c[j]) for i in range(N) for j in range(N)]


def truth(sc, cam, eye):
    """Cells whose centre is reachable by an unobstructed ray from the eye (reach) and, if a camera is given, also inside its frame."""
    dg = bpy.context.evaluated_depsgraph_get()
    reach, frame = set(), set()
    for i, j, x, y in cell_centres():
        p = Vector((x, y, 0.0)); d = p - eye; dist = d.length; d.normalize()
        ok, *_ = sc.ray_cast(dg, eye, d, distance=dist * 0.9995)
        if not ok:
            reach.add((i, j))
            if cam is not None:
                uv = world_to_camera_view(sc, cam, p)
                if 0 <= uv.x <= 1 and 0 <= uv.y <= 1 and uv.z > 0:
                    frame.add((i, j))
    return reach, frame


def eye():
    W, H = 800, 600
    for ent in ENTRANCES:
        sc, coll, (g0, g1) = scene_setup(ent)
        objs = {o.name: o for o in coll.objects}
        pos = position_material('Pos'); black = flat_material('Black', (0, 0, 0))
        for n, o in objs.items():
            assign(o, pos if n == 'Platform' else black)
        xc = (g0 + g1) / 2
        e = Vector((xc, -2.9, EYE_H))
        cam = make_camera(sc, tuple(e), (math.pi / 2, 0, 0), lens=18)
        sc.render.resolution_x, sc.render.resolution_y = W, H
        sc.render.resolution_percentage = 100
        sc.eevee.taa_render_samples = 1
        sc.render.filter_size = 0.0
        sc.view_settings.view_transform = 'Raw'; sc.view_settings.look = 'None'
        a = render_exr(sc, os.path.join(tempfile.mkdtemp(), 'eye'))
        reach, frame = truth(sc, cam, e)
        floor = a[..., 2] > 0.999
        x = a[..., 0] * 2 * HALF - HALF; y = a[..., 1] * 2 * HALF - HALF
        inside = floor & (np.abs(x) < HALF) & (np.abs(y) < HALF)
        ci = np.floor((x[inside] + HALF) / CELL).astype(int).clip(0, N - 1); cj = np.floor((y[inside] + HALF) / CELL).astype(int).clip(0, N - 1)
        seen = set(zip(ci.tolist(), cj.tolist()))
        both = len(seen & frame)
        print(f'entrance {ent:6s}: interior cells {N*N}; reachable from the eye {len(reach)} ({100*len(reach)/N**2:.1f}%); '
              f'reachable and in frame {len(frame)} ({100*len(frame)/N**2:.1f}%); seen in the cell-id image {len(seen)}; '
              f'in both {both}; image only {len(seen - frame)}; truth only {len(frame - seen)}')
        print(f'      floor pixels {int(floor.sum())} of {W*H}; reachable but outside the frame: {len(reach - frame)} cells')


def plan():
    for ent in ENTRANCES:
        sc, coll, (g0, g1) = scene_setup(ent)
        objs = {o.name: o for o in coll.objects}
        cols = {'wall': (1, 0, 0), 'floor': (0, 1, 0), 'plinth': (0, 0, 1)}
        mats = {k: flat_material(k, v) for k, v in cols.items()}
        for n, o in objs.items():
            assign(o, mats['floor'] if n == 'Platform' else mats['plinth'] if n == 'Plinth' else mats['wall'])
        make_camera(sc, (0, 0, 12), (0, 0, 0), ortho=6.4)
        for size in (100, 200, 400):
            sc.render.resolution_x = sc.render.resolution_y = size
            sc.eevee.taa_render_samples = 1; sc.render.filter_size = 0.0
            sc.view_settings.view_transform = 'Raw'
            a = render_exr(sc, os.path.join(tempfile.mkdtemp(), 'plan'))
            res = 6.4 / size                                        # metres per pixel
            wall = (a[..., 0] > 0.5); floor = (a[..., 1] > 0.5); plinth = (a[..., 2] > 0.5)
            # interior region in pixel coordinates
            px = lambda m: (m + 3.2) / res
            lo, hi = int(round(px(-HALF))), int(round(px(HALF)))
            region = np.zeros_like(floor); region[lo:hi, lo:hi] = True
            frac_floor = (floor & region).sum() / region.sum()
            # entrance: along the south wall strip (y in [-2.95,-2.85]) read the non-wall pixels between x=-3 and 3
            row = int(round((3.2 - (-2.9)) / res))                  # image row of y = -2.9 (row 0 is y = +3.2)
            line = ~wall[row, int(round(px(-3.0))):int(round(px(3.0)))]
            c = int(round(((g0 + g1) / 2 - (-3.0)) / res))         # a pixel in the middle of the gap
            l = r = c
            while l > 0 and line[l - 1]: l -= 1
            while r < len(line) - 1 and line[r + 1]: r += 1
            x0 = (l + int(round(px(-3.0)))) * res - 3.2; x1 = (r + 1 + int(round(px(-3.0)))) * res - 3.2
            print(f'plan {ent:6s} {size:3d} px ({1000*res:.1f} mm/px): floor-coloured share of interior {100*frac_floor:.2f}%; '
                  f'gap read as [{x0:.3f}, {x1:.3f}] (true [{g0:.1f}, {g1:.1f}]), edge errors {abs(x0-g0)*1000:.1f} and {abs(x1-g1)*1000:.1f} mm')


def seg_cross(p, q, r, s):
    d1, d2 = q - p, s - r
    den = d1[0] * d2[1] - d1[1] * d2[0]
    if abs(den) < 1e-12:
        return False
    t = ((r - p)[0] * d2[1] - (r - p)[1] * d2[0]) / den
    u = ((r - p)[0] * d1[1] - (r - p)[1] * d1[0]) / den
    return 1e-6 < t < 1 - 1e-6 and 1e-6 < u < 1 - 1e-6


def seg_dist3(p, q, r, s):
    u, v, w = q - p, s - r, p - r
    a, b, c, d, e = u @ u, u @ v, v @ v, u @ w, v @ w
    den = a * c - b * b
    t = 0.0 if den < 1e-12 else np.clip((b * e - c * d) / den, 0, 1)
    sdt = np.clip((b * t + e) / c, 0, 1)
    t = np.clip((b * sdt - d) / a, 0, 1)
    return np.linalg.norm((p + t * u) - (r + sdt * v))


def wire():
    for ent in ENTRANCES:
        sc, coll, gap = scene_setup(ent)
        for name, loc, rot, kw in (('oblique', (7.0, -9.0, 6.0), None, {'lens': 35}), ('elevation', (0, -14, 1.2), (math.pi / 2, 0, 0), {'lens': 35})):
            cam = make_camera(sc, loc, rot or (0, 0, 0), **kw)
            if rot is None:
                cam.rotation_euler = (-cam.location).to_track_quat('-Z', 'Y').to_euler(); bpy.context.view_layer.update()
            sc.render.resolution_x, sc.render.resolution_y = 800, 600
            edges = []
            for o in coll.objects:
                for e in o.data.edges:
                    edges.append(np.array([o.matrix_world @ o.data.vertices[k].co for k in e.vertices]))
            def proj(P):
                uv = world_to_camera_view(sc, cam, Vector(P)); return np.array([uv.x * 800, (1 - uv.y) * 600])
            E2 = [np.array([proj(a), proj(b)]) for a, b in edges]
            dg = bpy.context.evaluated_depsgraph_get()
            visible = []
            for (a, b) in edges:
                m = Vector((a + b) / 2); o = cam.matrix_world.translation; d = m - o; dist = d.length; d.normalize()
                ok, loc_, n_, idx, hit, mat = sc.ray_cast(dg, o, d, distance=dist * 0.999)
                visible.append(not ok)
            def count(idxs):
                false = true = 0
                for i, j in itertools.combinations(idxs, 2):
                    if seg_cross(E2[i][0], E2[i][1], E2[j][0], E2[j][1]):
                        if seg_dist3(edges[i][0], edges[i][1], edges[j][0], edges[j][1]) > 1e-4:
                            false += 1
                        else:
                            true += 1
                return false, true
            allf, allt = count(range(len(edges)))
            visf, vist = count([i for i, v in enumerate(visible) if v])
            print(f'{ent:6s} {name:9s}: {len(edges)} edges, {sum(visible)} with unobstructed midpoint; '
                  f'screen crossings in wireframe: {allf} false, {allt} true; among unobstructed-midpoint edges: {visf} false, {vist} true')


if __name__ == '__main__':
    {'eye': eye, 'plan': plan, 'wire': wire}[sys.argv[1]]()
