"""Prologue: contour surfaces of the prescribed field as Blender meshes; check volumes, the hole, and render nested shells.

    python3 synestia_blender.py check|figure
"""
import math, sys
import numpy as np
import bpy, bmesh
from synestia import R0, SR, SZ, semi_axes, volume_analytic, k_of, enclosed_mass, total_mass
from dla_blender import base_scene
from arrangement_scene import srgb_to_linear


def shell_mesh(name, f, nmaj, nmin, wedge=None):
    """Elliptical-torus surface rho = f*rho0. Vertex (i,j): phi_i about the z axis, theta_j around the ellipse. wedge=(phi0, phi1) leaves it open."""
    a, b = semi_axes(f)
    verts, faces = [], []
    closed = wedge is None
    p0, p1 = (0.0, 2 * math.pi) if closed else wedge
    nm = nmaj if closed else nmaj + 1
    for i in range(nm):
        phi = p0 + (p1 - p0) * i / nmaj
        for j in range(nmin):
            th = 2 * math.pi * j / nmin
            R = R0 + a * math.cos(th)
            verts.append((R * math.cos(phi), R * math.sin(phi), b * math.sin(th)))
    for i in range(nmaj if closed else nmaj):
        i2 = (i + 1) % nm
        for j in range(nmin):
            j2 = (j + 1) % nmin
            faces.append((i * nmin + j, i2 * nmin + j, i2 * nmin + j2, i * nmin + j2))
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    return me


def mesh_volume(me):
    bm = bmesh.new(); bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    v = bm.calc_volume(signed=True); bm.free(); return v


def shell_material(k_max):
    m = bpy.data.materials.new('Contour level'); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_type = 'OBJECT'; at.attribute_name = 'k'
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 1.0; mr.inputs['From Max'].default_value = k_max
    cr = nt.nodes.new('ShaderNodeValToRGB'); e = cr.color_ramp.elements
    e[0].position = 0.0; e[0].color = srgb_to_linear([255, 225, 110]); e[1].position = 1.0; e[1].color = srgb_to_linear([95, 55, 150])
    em = nt.nodes.new('ShaderNodeEmission'); out = nt.nodes.new('ShaderNodeOutputMaterial')
    L = nt.links.new
    L(at.outputs['Fac'], mr.inputs['Value']); L(mr.outputs['Result'], cr.inputs['Fac'])
    L(cr.outputs['Color'], em.inputs['Color']); L(em.outputs['Emission'], out.inputs['Surface'])
    return m


def check():
    sc, _ = base_scene()
    print('closed mesh volume against 2 pi^2 R0 a b, f = 0.1 (a=%.3f, b=%.3f):' % semi_axes(0.1))
    v0 = volume_analytic(0.1)
    for nmaj, nmin in ((16, 8), (32, 16), (64, 32), (128, 64), (256, 128)):
        v = mesh_volume(shell_mesh('s', 0.1, nmaj, nmin))
        print(f'  {nmaj:4d} x {nmin:3d}: {v:.5f}  relative error {(v - v0) / v0:+.2e}')
    print('analytic', round(v0, 5))
    print('hole radius from the mesh (min over vertices of signed ring radius) against R0 - a:')
    for f in (0.1, 0.03, 0.0175, 0.0165, 0.01):
        a, b = semi_axes(f); me = shell_mesh('s', f, 64, 32)
        # ring radius of every vertex in the phi=0 section is its x coordinate (phi_0 = 0)
        xs = [me.vertices[j].co.x for j in range(32)]
        print(f'  f={f:<7} min x {min(xs):+.4f}   R0-a {R0 - a:+.4f}   hole present: {min(xs) > 0}')
    print('one object count, one mesh per shell, one material check in figure()')


def figure():
    sc, _ = base_scene()
    levels = (0.6, 0.3, 0.1, 0.03)
    mat = shell_material(k_of(0.03))
    for f in levels:
        me = shell_mesh(f'Shell {f}', f, 96, 48, wedge=(0.0, 1.5 * math.pi))
        me.materials.append(mat)
        o = bpy.data.objects.new(f'Shell {f}', me); o['k'] = k_of(f); o['level'] = f
        sc.collection.objects.link(o)
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam)
    cam.location = (2.6, -3.6, 3.2); cam.data.lens = 40
    d = np.array([0.0, 0.0, 0.0]) - np.array(cam.location)
    from mathutils import Vector
    cam.rotation_euler = Vector(d).to_track_quat('-Z', 'Y').to_euler(); sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = 1500, 900
    sc.view_settings.view_transform = 'Standard'; sc.eevee.taa_render_samples = 4
    sc.render.image_settings.file_format = 'PNG'; sc.render.filepath = 'figs/fig0_synestia.png'
    print('objects', len([o for o in sc.objects if o.type == 'MESH']), 'materials', len(bpy.data.materials), 'meshes', len(bpy.data.meshes))
    bpy.ops.render.render(write_still=True)


if __name__ == '__main__':
    {'check': check, 'figure': figure}[sys.argv[1]]()
