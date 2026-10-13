"""Chapter 8: how many views certify a vertex count, a one-material data-driven shader, and render budgets.

    python3 view_budget.py coverage|shader|budget       (Blender's Python module)
"""
import math, sys, time, os, tempfile, json
import numpy as np
import bpy
from mathutils import Vector
from arrangement_family import family_normals, summarize
from arrangement_scene import build, CLASS_RGB, detect, ARRANGEMENTS, srgb_to_linear, emission_material, predicted_visible

DEG = math.pi / 180


def fib(n):
    i = np.arange(n) + 0.5
    z = 1 - 2 * i / n
    r = np.sqrt(1 - z * z)
    t = np.pi * (1 + 5 ** 0.5) * i
    return np.stack([r * np.cos(t), r * np.sin(t), z], axis=1)


def vertices_of(which):
    a, b = ARRANGEMENTS[which]
    return np.array(summarize(family_normals(a, b))['vertices'])


def coverage():
    dirs = fib(4000)
    for which in ('source', 'teaching'):
        V = vertices_of(which)
        facing = dirs @ V.T                                  # cosine between view direction and outward vertex normal
        for thr in (0.0, 0.2):
            seen = (facing > thr).sum(axis=1)
            print(f'{which:8s} n={len(V)} threshold {thr}: visible per view min {seen.min()}, median {int(np.median(seen))}, max {seen.max()}')
        # greedy cover with facing > 0.2
        for thr in (0.2,):
            covered = np.zeros(len(V), bool); chosen = []
            while not covered.all() and len(chosen) < 12:
                gain = ((facing > thr) & ~covered).sum(axis=1)
                k = int(gain.argmax()); chosen.append(k); covered |= facing[k] > thr
            print(f'{which:8s}: greedy views to see every vertex at facing > {thr}: {len(chosen)}')
        # exact check of whether two antipodal views suffice
        best = 0
        for thr in (0.2, 0.1, 0.05):
            ok = [(np.abs(facing[i]) > thr).all() for i in range(len(dirs))]
            print(f'{which:8s}: antipodal pair sees all vertices at |facing| > {thr}: {any(ok)}  ({sum(ok)} of {len(dirs)} directions)')
    return


def view_count_in_blender(which, d):
    sc, cam, markers, info = build(which)
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 3.0
    d = Vector(d).normalized()
    cam.location = d * 6.0
    cam.rotation_euler = (-cam.location).to_track_quat('-Z', 'Y').to_euler()
    pv = predicted_visible(cam, markers)
    return sum(pv['centre'].values()), sum(pv['surface'].values()), len(markers)


def blender_cover():
    for which in ('source', 'teaching'):
        V = vertices_of(which)
        dirs = fib(4000)
        facing = dirs @ V.T
        # pick direction maximising min |facing| (best antipodal pair), then count with tubes in Blender
        m = np.abs(facing).min(axis=1)
        k = int(m.argmax())
        d = dirs[k]
        c1 = view_count_in_blender(which, d)
        c2 = view_count_in_blender(which, -d)
        print(f'{which}: best antipodal direction has min |facing| {m[k]:.3f}; Blender centre-bound counts {c1[0]} + {c2[0]} of {c1[2]}, surface-bound {c1[1]} + {c2[1]}')


def shader():
    which = 'source'
    sc, cam, markers, info = build(which)
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 3.0
    cam.location = Vector((0.5, -1.0, 0.45)).normalized() * 6
    cam.rotation_euler = (-cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.resolution_x = sc.render.resolution_y = 450
    sc.eevee.taa_render_samples = 16
    p1 = os.path.join(tempfile.mkdtemp(), 'three.png'); p2 = os.path.join(tempfile.mkdtemp(), 'one.png')
    def draw(path):
        sc.render.image_settings.file_format = 'PNG'; sc.render.filepath = path
        bpy.ops.render.render(write_still=True)
    draw(p1)
    mats_before = len(bpy.data.materials)
    # one material: Attribute (object property) -> Map Range -> Color Ramp (constant) -> Emission
    m = bpy.data.materials.new('Class by property'); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    attr = nt.nodes.new('ShaderNodeAttribute'); attr.attribute_type = 'OBJECT'; attr.attribute_name = 'multiplicity'
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 2; mr.inputs['From Max'].default_value = 4
    cr = nt.nodes.new('ShaderNodeValToRGB'); cr.color_ramp.interpolation = 'CONSTANT'
    e = cr.color_ramp.elements
    e[0].position = 0.0; e[0].color = srgb_to_linear(CLASS_RGB[2])
    e[1].position = 0.25; e[1].color = srgb_to_linear(CLASS_RGB[3])
    e.new(0.75).color = srgb_to_linear(CLASS_RGB[4])
    em = nt.nodes.new('ShaderNodeEmission'); out = nt.nodes.new('ShaderNodeOutputMaterial')
    L = nt.links.new
    L(attr.outputs['Fac'], mr.inputs['Value']); L(mr.outputs['Result'], cr.inputs['Fac'])
    L(cr.outputs['Color'], em.inputs['Color']); L(em.outputs['Emission'], out.inputs['Surface'])
    for o in markers:
        o.material_slots[0].link = 'OBJECT'; o.material_slots[0].material = m
    print('nodes in the single material:', len(nt.nodes), ' links:', len(nt.links))
    draw(p2)
    from PIL import Image
    a = np.asarray(Image.open(p1).convert('RGB')).astype(int); b = np.asarray(Image.open(p2).convert('RGB')).astype(int)
    print('blobs by class, three materials :', detect(p1))
    print('blobs by class, one material    :', detect(p2))
    print('pixels differing by more than 2 :', int((np.abs(a - b).max(axis=2) > 2).sum()), 'of', a.shape[0] * a.shape[1])
    print('materials used by markers: three-material scene had', 3, ' one-material scene has 1; datablocks now in file:', len(bpy.data.materials), '(unused ones remain until purged)')


def budget():
    from PIL import Image
    def render(size, samples):
        sc, cam, markers, info = build('source')
        sc.render.resolution_x = sc.render.resolution_y = size
        sc.eevee.taa_render_samples = samples
        path = os.path.join(tempfile.mkdtemp(), 'b.png')
        sc.render.image_settings.file_format = 'PNG'; sc.render.filepath = path
        t = time.time(); bpy.ops.render.render(write_still=True); dt = time.time() - t
        return np.asarray(Image.open(path).convert('RGB')).astype(float), dt
    ref, tref = render(300, 256)
    print(f'reference 300 px, 256 samples: {tref:.1f} s')
    for s in (1, 4, 16, 64):
        a, dt = render(300, s)
        rms = np.sqrt(((a - ref) ** 2).mean())
        print(f'300 px, {s:3d} samples: {dt:5.1f} s, rms difference from reference {rms:.2f} of 255, max {np.abs(a - ref).max():.0f}')
    a1, _ = render(300, 16); a2, _ = render(300, 16)
    print('two renders with identical settings are bit-identical:', bool((a1 == a2).all()))
    for size in (150, 300, 600):
        a, dt = render(size, 16)
        print(f'{size} px, 16 samples: {dt:5.1f} s, pixels {size*size}, seconds per megapixel {dt/(size*size/1e6):.0f}')


if __name__ == '__main__':
    {'coverage': coverage, 'bcover': blender_cover, 'shader': shader, 'budget': budget}[sys.argv[1]]()
