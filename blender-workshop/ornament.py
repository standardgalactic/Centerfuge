"""Chapter 10: what does surface ornament cost a reading task?

    python3 ornament.py contrast|cost|figure        (Blender's Python module)

Task: find the plinth in an oblique view of the habitat. Reading procedure: classify each pixel to the nearest of four
reference colours (plinth, floor, wall, background) in CIE Lab, and score the plinth class against a mask rendered from
flat identity colours with the same camera. Ornament: a procedural noise pattern on the floor of amplitude a, which
carries no information about the plinth.
"""
import math, os, sys, tempfile, time
import numpy as np
import bpy
from presentations import scene_setup, assign, make_camera, flat_material, render_exr
from arrangement_scene import srgb_to_linear

FLOOR = (150, 135, 110)
WALL = (200, 195, 185)
BACK = (24, 28, 36)
PLINTHS = {'distinct': (0, 114, 178), 'tonal 1.15': tuple(min(255, round(v * 1.15)) for v in FLOOR), 'tonal 1.45': tuple(min(255, round(v * 1.45)) for v in FLOOR)}


def lab(rgb8):
    c = np.asarray(rgb8, dtype=float).reshape(-1, 3) / 255.0
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = lin @ M.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 216 / 24389, np.cbrt(xyz), (24389 / 27 * xyz + 16) / 116)
    return np.stack([116 * f[:, 1] - 16, 500 * (f[:, 0] - f[:, 1]), 200 * (f[:, 1] - f[:, 2])], axis=1)


def delta_e(a, b):
    return float(np.linalg.norm(lab(a) - lab(b)))


def noisy_floor_material(amp, scale=6.0):
    """Emission whose colour mixes two tones of the floor colour by a noise pattern; amp = relative tone spread."""
    m = bpy.data.materials.new('Floor noise'); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = scale; nz.inputs['Detail'].default_value = 3.0
    nz.noise_dimensions = '3D'
    mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value = 0.3; mr.inputs['From Max'].default_value = 0.7
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
    lo = tuple(min(255, v * (1 - amp)) for v in FLOOR); hi = tuple(min(255, v * (1 + amp)) for v in FLOOR)
    mix.inputs['A'].default_value = srgb_to_linear(lo); mix.inputs['B'].default_value = srgb_to_linear(hi)
    em = nt.nodes.new('ShaderNodeEmission'); out = nt.nodes.new('ShaderNodeOutputMaterial')
    L = nt.links.new
    L(tc.outputs['Object'], nz.inputs['Vector']); L(nz.outputs['Fac'], mr.inputs['Value'])
    L(mr.outputs['Result'], mix.inputs['Factor']); L(mix.outputs['Result'], em.inputs['Color'])
    L(em.outputs['Emission'], out.inputs['Surface'])
    return m


def setup(floor_factory, plinth_rgb, size=(480, 360)):
    sc, coll, gap = scene_setup('east')      # resets the file, so materials are made afterwards
    floor_mat = floor_factory()
    objs = {o.name: o for o in coll.objects}
    wall = flat_material('Wall', tuple(srgb_to_linear(WALL)[:3]))
    pl = flat_material('Plinth', tuple(srgb_to_linear(plinth_rgb)[:3]))
    for n, o in objs.items():
        assign(o, floor_mat if n == 'Platform' else pl if n == 'Plinth' else wall)
    sc.world.node_tree.nodes['Background'].inputs['Color'].default_value = srgb_to_linear(BACK)
    sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.0
    cam = make_camera(sc, (5.0, -6.0, 10.0), (0, 0, 0), lens=35)
    cam.rotation_euler = (-cam.location).to_track_quat('-Z', 'Y').to_euler(); bpy.context.view_layer.update()
    sc.render.resolution_x, sc.render.resolution_y = size
    sc.render.resolution_percentage = 100
    sc.eevee.taa_render_samples = 1; sc.render.filter_size = 0.0
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
    return sc, objs


def to_srgb8(a):
    lin = np.clip(a[..., :3], 0, 1)
    s = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.power(lin, 1 / 2.4) - 0.055)
    return np.round(s * 255).astype(int)


def identity_mask(plinth_rgb):
    """Flat identity colours, same camera: red = plinth."""
    sc, objs = setup(lambda: flat_material('F', (0, 1, 0)), plinth_rgb)
    for n, o in objs.items():
        if n == 'Plinth': assign(o, flat_material('P', (1, 0, 0)))
        elif n != 'Platform': assign(o, flat_material('W', (0, 0, 1)))
    sc.view_settings.view_transform = 'Raw'
    a = render_exr(sc, os.path.join(tempfile.mkdtemp(), 'id'))
    return a[..., 0] > 0.5


def read(img8, refs):
    L = lab(img8.reshape(-1, 3))
    names = list(refs)
    R = lab(np.array([refs[k] for k in names]))
    d = ((L[:, None, :] - R[None, :, :]) ** 2).sum(axis=2)
    return np.array(names)[d.argmin(axis=1)].reshape(img8.shape[:2])


def score(pred, truth):
    p = pred == 'plinth'
    tp = (p & truth).sum(); fp = (p & ~truth).sum(); fn = (~p & truth).sum()
    return tp / max(1, tp + fp + fn), tp / max(1, tp + fp), tp / max(1, tp + fn)


def contrast():
    for pname, prgb in PLINTHS.items():
        truth = identity_mask(prgb)
        print(f'plinth "{pname}" {prgb}: mask {int(truth.sum())} px; assigned Lab dE to floor {delta_e(prgb, FLOOR):.1f}')
        refs = {'plinth': prgb, 'floor': FLOOR, 'wall': WALL, 'background': BACK}
        for amp in (0.0, 0.1, 0.2, 0.35, 0.5):
            sc, objs = setup(lambda: noisy_floor_material(amp), prgb)
            a = render_exr(sc, os.path.join(tempfile.mkdtemp(), 'o'))
            img = to_srgb8(a)
            floor_px = (~truth) & (np.abs(img - np.array(FLOOR)).sum(axis=2) < 140) & (np.abs(img - np.array(WALL)).sum(axis=2) > 30)
            iou, prec, rec = score(read(img, refs), truth)
            spread = np.std(lab(img[floor_px])[:, 0]) if floor_px.sum() else 0
            print(f'   amplitude {amp:4.2f}: floor lightness spread (sd of L*) {spread:5.2f}; plinth IoU {iou:.3f}, precision {prec:.3f}, recall {rec:.3f}')


def cost():
    prgb = PLINTHS['distinct']
    for label, mat in (('flat', None), ('noise 0.35', 0.35)):
        ts = []
        for rep in range(3):
            sc, objs = setup((lambda: flat_material('F', tuple(srgb_to_linear(FLOOR)[:3]))) if mat is None else (lambda: noisy_floor_material(mat)), prgb, size=(960, 720))
            sc.eevee.taa_render_samples = 16
            sc.render.image_settings.file_format = 'PNG'; sc.render.filepath = '/tmp/cost.png'
            t = time.time(); bpy.ops.render.render(write_still=True); ts.append(time.time() - t)
        print(f'{label:10s}: render times {["%.1f" % t for t in ts]} s')




def shading():
    """How many distinct tones does the plinth show, with flat emission and with a lit diffuse material?"""
    from arrangement_scene import diffuse_material
    import bpy
    prgb = PLINTHS['distinct']
    truth = identity_mask(prgb)
    out = {}
    for label in ('flat emission', 'lit diffuse'):
        sc, objs = setup(lambda: flat_material('F', tuple(srgb_to_linear(FLOOR)[:3])), prgb)
        if label == 'lit diffuse':
            wall = diffuse_material('W', WALL, 0.8); pl = diffuse_material('P', prgb, 0.5); fl = diffuse_material('F2', FLOOR, 0.9)
            for n, o in objs.items():
                assign(o, fl if n == 'Platform' else pl if n == 'Plinth' else wall)
            sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sc.collection.objects.link(sun)
            sun.data.energy = 3.0; sun.rotation_euler = (math.radians(50), math.radians(10), math.radians(25))
        img = to_srgb8(render_exr(sc, os.path.join(tempfile.mkdtemp(), 's')))
        px = img[truth]
        uniq, counts = np.unique(px, axis=0, return_counts=True)
        big = uniq[counts >= 20]
        L = lab(big)[:, 0]
        print(f'{label:13s}: plinth mask {int(truth.sum())} px, {len(uniq)} distinct colours, {len(big)} with at least 20 px; lightness L* of those: '
              + ', '.join(f'{v:.1f}' for v in sorted(L)))


if __name__ == '__main__':
    {'contrast': contrast, 'cost': cost, 'shading': shading}[sys.argv[1]]()
