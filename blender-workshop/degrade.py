"""Chapter 29: degrading a construction along its own resolution axes, and asking which invariants survive.

    python3 degrade.py grid|decimate|odd
Object: the contour shell of the prologue at f = 0.05, a torus with elliptical cross-section (a = 0.857, b = 0.367, hole radius 0.143).
"""
import math, sys, time
import numpy as np
import bpy, bmesh
from synestia import R0, semi_axes, volume_analytic
from synestia_blender import shell_mesh, mesh_volume

F = 0.05
A, B = semi_axes(F)
HOLE = R0 - A
TOL = dict(volume=0.01, hole=0.05, smooth=25.0)


def measures(me, nmaj=None):
    """Volume error, hole inradius error, largest angle between neighbouring faces (degrees), faces."""
    vol = mesh_volume(me); ve = vol / volume_analytic(F) - 1
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    rad = np.hypot(co[:, 0], co[:, 1])
    # the hole is the open disc inside the inner rim: take the vertices of the smallest-radius ring and the polygon they make in plan view
    r0 = rad.min(); ring = np.where(np.abs(rad - r0) < 1e-5)[0]
    k = len(ring)
    hole_in = r0 * math.cos(math.pi / k) if k >= 3 else 0.0
    he = hole_in / HOLE - 1
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ang = max((math.degrees(e.calc_face_angle(0)) for e in bm.edges if len(e.link_faces) == 2), default=0.0)
    nf = len(bm.faces); bm.free()
    return dict(vol=ve, hole=he, ang=ang, faces=nf, ring=k)


def ok(m):
    return dict(volume=abs(m['vol']) < TOL['volume'], hole=abs(m['hole']) < TOL['hole'], smooth=m['ang'] < TOL['smooth'])


def grid():
    ns = [6, 8, 12, 16, 24, 32, 48, 64]
    print('nmaj nmin  faces   vol err    hole err   max angle   volume hole smooth')
    rows = []
    for nmaj in ns:
        for nmin in ns:
            me = shell_mesh('s', F, nmaj, nmin); m = measures(me); o = ok(m); rows.append((nmaj, nmin, m, o)); bpy.data.meshes.remove(me)
    for nmaj, nmin, m, o in rows:
        if nmaj in (8, 16, 64) and nmin in (8, 16, 64) or nmaj == nmin:
            print(f'{nmaj:4d} {nmin:4d} {m["faces"]:6d}  {m["vol"]:+9.5f}  {m["hole"]:+9.5f}  {m["ang"]:8.2f}    {"ok" if o["volume"] else "--":>6s} {"ok" if o["hole"] else "--":>4s} {"ok" if o["smooth"] else "--":>6s}')
    for name in ('volume', 'hole', 'smooth'):
        best = min((r for r in rows if r[3][name]), key=lambda r: r[2]['faces'], default=None)
        print(f'cheapest grid meeting {name} alone: nmaj={best[0]} nmin={best[1]} faces={best[2]["faces"]}' if best else f'none meets {name}')
    best = min((r for r in rows if all(r[3].values())), key=lambda r: r[2]['faces'], default=None)
    print('cheapest meeting all three:', (best[0], best[1], best[2]['faces']) if best else None)
    return rows


def hole_ray(me, nrays=720):
    """Hole radius from the geometry alone: cast rays outward from the axis at z = 0 and take the smallest first-hit distance."""
    from mathutils.bvhtree import BVHTree
    bm = bmesh.new(); bm.from_mesh(me); t = BVHTree.FromBMesh(bm); d = []
    for k in range(nrays):
        ph = 2 * math.pi * (k + 0.5) / nrays
        hit = t.ray_cast((0, 0, 0), (math.cos(ph), math.sin(ph), 0))
        d.append(hit[3] if hit[0] is not None else np.inf)
    bm.free(); return min(d) / HOLE - 1


def odd():
    print('nmin  hole err (rings)   hole err (rays)   vol err')
    for nmin in (6, 7, 8, 9, 16, 17, 32, 33):
        me = shell_mesh('s', F, 32, nmin); m = measures(me)
        print(f'{nmin:4d}  {m["hole"]:+9.5f}         {hole_ray(me):+9.5f}        {m["vol"]:+9.5f}'); bpy.data.meshes.remove(me)


def decimate():
    print('triangles  method      vol err    hole err (rays)  max angle')
    fine = shell_mesh('fine', F, 128, 128)
    sc = bpy.data.scenes.new('S')
    for ntri in (144, 384, 768, 1536, 3072):
        # uniform grid with this many triangles: nmaj*nmin*2 = ntri, nmin = 1.5 nmaj as the cheapest-grid ratio of the table suggests
        nmaj = int(round(math.sqrt(ntri / 3))); nmin = int(round(1.5 * nmaj))
        if nmin % 2: nmin += 1
        me = shell_mesh('u', F, nmaj, nmin)
        bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.to_mesh(me); bm.free()
        m = measures(me)
        print(f'{len(me.polygons):8d}   grid {nmaj}x{nmin}'.ljust(30) + f'{m["vol"]:+9.5f}   {hole_ray(me):+9.5f}      {m["ang"]:7.2f}')
        # collapse decimation from the fine mesh to the same triangle count
        o = bpy.data.objects.new('f', fine.copy()); sc.collection.objects.link(o)
        bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.to_mesh(o.data); bm.free()
        n0 = len(o.data.polygons); md = o.modifiers.new('d', 'DECIMATE'); md.decimate_type = 'COLLAPSE'; md.ratio = ntri / n0
        sc.view_layers[0].update(); ev = o.evaluated_get(sc.view_layers[0].depsgraph); me2 = ev.to_mesh()
        m2 = measures(me2)
        print(f'{len(me2.polygons):8d}   collapse'.ljust(30) + f'{m2["vol"]:+9.5f}   {hole_ray(me2):+9.5f}      {m2["ang"]:7.2f}')
        ev.to_mesh_clear(); bpy.data.objects.remove(o)


def aspects():
    print('base 16 x 16 and one parameter doubled (minor count kept even):')
    print('mesh      faces   vol err    hole err   max angle')
    for nmaj, nmin in ((16, 16), (32, 16), (16, 32), (32, 32)):
        me = shell_mesh('s', F, nmaj, nmin); m = measures(me)
        print(f'{nmaj:2d} x {nmin:2d}  {m["faces"]:6d}  {m["vol"]:+9.5f}  {m["hole"]:+9.5f}  {m["ang"]:8.2f}'); bpy.data.meshes.remove(me)


if __name__ == '__main__':
    globals()[sys.argv[-1]]()
