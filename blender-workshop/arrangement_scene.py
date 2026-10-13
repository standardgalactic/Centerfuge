"""Render a nine-circle arrangement with vertices coloured by multiplicity, then ask the
image what it establishes.

    python3 arrangement_scene.py source coded out.png        (Blender's Python module)
    python3 arrangement_scene.py teaching uniform out.png

The scene is built from the same normals used to count the arrangement (arrangement_family.py).
Markers use an Emission shader at strength 1 under the Standard view transform, so the colour
that reaches the image is the colour that was assigned, up to edge blending. That choice makes
the colour a measurement channel; it is not a claim about how a finished image should be lit.
"""
import math
import sys

import bpy
import numpy as np
from mathutils import Vector

from arrangement_family import family_normals, summarize

DEG = math.pi / 180
ARRANGEMENTS = {'source': (0.0, 35 * DEG), 'teaching': (22.5 * DEG, 30 * DEG)}
# Okabe-Ito colours as 8-bit sRGB: blue, orange, reddish purple.
CLASS_RGB = {2: (0, 114, 178), 3: (230, 159, 0), 4: (204, 121, 167)}
UNIFORM_RGB = (86, 180, 233)


def srgb_to_linear(c8):
    out = []
    for v in c8:
        v = v / 255.0
        out.append(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4)
    return (*out, 1.0)


def emission_material(name, rgb8, strength=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = srgb_to_linear(rgb8)
    em.inputs['Strength'].default_value = strength
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
    return m


def diffuse_material(name, rgb8, roughness):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = srgb_to_linear(rgb8)
    b.inputs['Roughness'].default_value = roughness
    return m


def build(which, coded=True):
    alpha, beta = ARRANGEMENTS[which]
    normals = family_normals(alpha, beta)
    info = summarize(normals)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.view_settings.view_transform = 'Standard'
    sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x = sc.render.resolution_y = 900
    sc.world = bpy.data.worlds.new('World')
    sc.world.use_nodes = True
    bg = sc.world.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.004, 0.005, 0.008, 1)
    bg.inputs['Strength'].default_value = 1.0

    ball = bpy.data.objects.new('Globe', bpy.data.meshes.new('Globe'))
    sc.collection.objects.link(ball)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=64, ring_count=32)
    src = bpy.context.object
    ball.data = src.data
    bpy.data.objects.remove(src)
    ball.data.materials.append(diffuse_material('Globe', (22, 30, 44), 0.7))
    for p in ball.data.polygons:
        p.use_smooth = True

    # One torus mesh shared by all nine circles; each object only carries a rotation.
    R, r = 1.015, 0.011
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=128, minor_segments=8)
    tmp = bpy.context.object
    tube_mesh = tmp.data
    bpy.data.objects.remove(tmp)
    tube_mesh.materials.append(diffuse_material('Tube', (176, 180, 186), 0.45))
    for i, n in enumerate(normals):
        o = bpy.data.objects.new(f'Circle {i}', tube_mesh)
        sc.collection.objects.link(o)
        o.rotation_euler = Vector(n).to_track_quat('Z', 'Y').to_euler()

    # One marker mesh shared by every vertex; material chosen per multiplicity class.
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.034, segments=24, ring_count=12)
    tmp = bpy.context.object
    marker_mesh = tmp.data
    bpy.data.objects.remove(tmp)
    mats = {m: emission_material(f'Class {m}', CLASS_RGB[m] if coded else UNIFORM_RGB) for m in CLASS_RGB}
    markers = []
    for p, on in zip(info['vertices'], info['circles_at']):
        m = len(on)
        o = bpy.data.objects.new(f'Vertex m={m}', bpy.data.meshes.new('x'))
        o.data = marker_mesh
        o.material_slots  # shared mesh; the material is attached per object below
        sc.collection.objects.link(o)
        o.location = tuple(R * p)
        o['multiplicity'] = m
        o.active_material_index = 0
        markers.append(o)
    # Per-object material override: link the slot to the object, not to the shared mesh.
    for o in markers:
        if not o.material_slots:
            o.data.materials.append(mats[2])      # placeholder slot on the shared mesh
        o.material_slots[0].link = 'OBJECT'
        o.material_slots[0].material = mats[o['multiplicity']]

    # Camera and lights
    az, el, dist = math.radians(-35), math.radians(24), 6.0
    cam = bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera'))
    sc.collection.objects.link(cam)
    cam.location = (dist * math.cos(el) * math.cos(az), dist * math.cos(el) * math.sin(az), dist * math.sin(el))
    cam.rotation_euler = (-cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = 85
    sc.camera = cam
    for name, loc, power, size, color in (('Key', (-3.5, -4.0, 5.0), 1400, 4.0, (1.0, 0.97, 0.92)),
                                          ('Rim', (4.0, 3.5, 3.0), 700, 4.0, (0.7, 0.8, 1.0))):
        L = bpy.data.lights.new(name, 'AREA')
        L.energy, L.size, L.color = power, size, color
        lo = bpy.data.objects.new(name, L)
        sc.collection.objects.link(lo)
        lo.location = loc
        lo.rotation_euler = (-Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return sc, cam, markers, info


def _reached(sc, dg, origin, obj, point):
    """True if the segment from the camera to `point` meets no other object (a first hit on obj itself
    counts, as in the suite's verify_visibility) and `point` lies inside the camera frame."""
    from bpy_extras.object_utils import world_to_camera_view
    uv = world_to_camera_view(sc, sc.camera, point)
    if not (0.0 <= uv.x <= 1.0 and 0.0 <= uv.y <= 1.0 and uv.z > 0.0):
        return False
    d = point - origin
    dist = d.length
    d.normalize()
    ok, loc, n, idx, hit, mat = sc.ray_cast(dg, origin + d * 1e-4, d, distance=dist * 0.999)
    return (not ok) or hit == obj


def predicted_visible(cam, markers, stride=7):
    """Two bounds on the markers that can appear in the image, per multiplicity class.

    'centre' counts a marker only if its centre is reachable: a lower bound, since a marker can show
    around the limb of the globe or past a thin tube while its centre is hidden. 'surface' counts a
    marker if any sampled point on its surface is reachable: an upper-leaning estimate."""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    sc = bpy.context.scene
    origin = cam.matrix_world.translation.copy()
    centre = {2: 0, 3: 0, 4: 0}
    surface = {2: 0, 3: 0, 4: 0}
    for o in markers:
        m = o['multiplicity']
        if _reached(sc, dg, origin, o, o.matrix_world.translation):
            centre[m] += 1
        pts = [o.matrix_world @ v.co for v in o.data.vertices][::stride]
        if any(_reached(sc, dg, origin, o, p) for p in pts):
            surface[m] += 1
    return {'centre': centre, 'surface': surface}


def render(path, size=900):
    sc = bpy.context.scene
    sc.render.resolution_x = sc.render.resolution_y = size
    sc.render.image_settings.file_format = 'PNG'
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)


def detect(path, tol=22, min_pixels=12, colours=None):
    """Count connected blobs of each assigned colour in the image (within tol per channel)."""
    from PIL import Image
    from scipy import ndimage
    a = np.asarray(Image.open(path).convert('RGB')).astype(int)
    found = {}
    for m, rgb in (colours or CLASS_RGB).items():
        mask = (np.abs(a - np.array(rgb)) <= tol).all(axis=2)
        lab, n = ndimage.label(mask)
        sizes = ndimage.sum(mask, lab, range(1, n + 1))
        found[m] = int((sizes >= min_pixels).sum())
    return found


if __name__ == '__main__':
    which, mode, path = sys.argv[1], sys.argv[2], sys.argv[3]
    sc, cam, markers, info = build(which, coded=(mode == 'coded'))
    print('classes in the arrangement', info['hist'], ' markers', len(markers))
    print('markers reachable from the camera', predicted_visible(cam, markers))
    render(path)
    if mode == 'coded':
        print('blobs detected by colour', detect(path))
    else:
        print('blobs detected in the single marker colour', detect(path, colours={'all': UNIFORM_RGB}))
