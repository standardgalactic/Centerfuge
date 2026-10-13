"""Chapter 8, camera measurements: does the pinhole formula predict where a point lands in the image?

    python3 camera_probe.py       (Blender's Python module)
"""
import math, os, tempfile
import bpy, numpy as np
from PIL import Image
from scipy import ndimage
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
from arrangement_scene import emission_material


def pinhole(cam, point, W, H):
    """Pixel (x right, y down) of a world point by the textbook formula for a camera looking down -Z."""
    d = cam.data
    p = cam.matrix_world.inverted() @ Vector(point)           # camera coordinates; camera looks down -Z
    fit_w = W >= H                                              # 'AUTO' sensor fit uses the sensor width for the longer side
    sensor = d.sensor_width
    scale = (W if fit_w else H) / sensor                        # pixels per millimetre on the sensor
    return (W / 2 + scale * d.lens * p.x / -p.z, H / 2 - scale * d.lens * p.y / -p.z)


def run(lens, W=400, H=300, ortho=False):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'BLENDER_EEVEE'
    sc.view_settings.view_transform = 'Standard'
    sc.render.resolution_x, sc.render.resolution_y = W, H
    sc.render.resolution_percentage = 100; sc.eevee.taa_render_samples = 4
    sc.world = bpy.data.worlds.new('W'); sc.world.use_nodes = True
    sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0
    mat = emission_material('E', (255, 255, 255))
    mesh = bpy.data.meshes.new('m'); mesh.from_pydata([(0, 0, 0)], [], [])
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04, segments=16, ring_count=8)
    mesh = bpy.context.object.data; bpy.data.objects.remove(bpy.context.object)
    mesh.materials.append(mat)
    pts = [(0, 0, 0), (1.0, 0.5, 0.3), (-1.2, -0.4, 0.8), (0.6, -0.5, -0.6), (-0.7, 0.45, -0.2)]
    for i, p in enumerate(pts):
        o = bpy.data.objects.new(f'P{i}', mesh); sc.collection.objects.link(o); o.location = p
    cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam)
    cam.location = (3.1, -5.2, 2.3)
    cam.rotation_euler = (-cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.lens = lens
    if ortho:
        cam.data.type = 'ORTHO'; cam.data.ortho_scale = 6.0
    sc.camera = cam
    bpy.context.view_layer.update()
    path = os.path.join(tempfile.mkdtemp(), 'c.png')
    sc.render.image_settings.file_format = 'PNG'; sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    a = np.asarray(Image.open(path).convert('L')).astype(float)
    lab, n = ndimage.label(a > 40)
    cents = ndimage.center_of_mass(a, lab, range(1, n + 1))
    img = [(c[1] + 0.5, c[0] + 0.5) for c in cents]            # pixel centres: add half a pixel
    out = []
    for p in pts:
        uv = world_to_camera_view(sc, cam, Vector(p))
        api = (uv.x * W, (1 - uv.y) * H)
        mine = pinhole(cam, p, W, H) if not ortho else None
        j = min(range(len(img)), key=lambda k: (img[k][0] - api[0]) ** 2 + (img[k][1] - api[1]) ** 2)
        out.append((api, mine, img[j]))
    return cam, n, out


if __name__ == '__main__':
    for lens in (24, 50, 85):
        cam, n, out = run(lens)
        e_api = max(math.hypot(o[0][0] - o[2][0], o[0][1] - o[2][1]) for o in out)
        e_mine = max(math.hypot(o[1][0] - o[2][0], o[1][1] - o[2][1]) for o in out)
        e_f = max(math.hypot(o[0][0] - o[1][0], o[0][1] - o[1][1]) for o in out)
        fov = math.degrees(cam.data.angle_x)
        print(f'lens {lens:3d} mm: horizontal FOV {fov:6.2f} deg (formula {math.degrees(2*math.atan(36/(2*lens))):6.2f}); '
              f'{n} blobs; max px error: formula vs image {e_mine:.2f}, world_to_camera_view vs image {e_api:.2f}, formula vs API {e_f:.4f}')
    cam, n, out = run(50, ortho=True)
    e_api = max(math.hypot(o[0][0] - o[2][0], o[0][1] - o[2][1]) for o in out)
    print(f'orthographic scale 6: {n} blobs; max px error world_to_camera_view vs image {e_api:.2f}')
    # portrait frame: which dimension the sensor width governs
    cam, n, out = run(50, W=300, H=400)
    e_mine = max(math.hypot(o[1][0] - o[2][0], o[1][1] - o[2][1]) for o in out)
    print(f'portrait 300x400: formula (sensor on longer side) vs image {e_mine:.2f} px')
