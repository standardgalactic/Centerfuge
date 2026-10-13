"""Chapter 12: how much circle is a Bezier circle, and what does a bevel add?

    python3 curves_probe.py bezier|handles|tube       (Blender's Python module)
"""
import math, sys
import bpy, numpy as np
from mathutils import Vector


def fresh():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def evaluated_mesh(o):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    P = np.array([v.co[:] for v in me.vertices]); E = np.array([e.vertices[:] for e in me.edges])
    return me, ev, P, E


def radial_error(P, E, R=1.0, k=9):
    """Largest |r - R| over points sampled along every edge of the evaluated polyline (so chord sag is counted)."""
    worst = 0.0
    for t in np.linspace(0, 1, k):
        Q = P[E[:, 0]] * (1 - t) + P[E[:, 1]] * t
        worst = max(worst, float(np.abs(np.linalg.norm(Q[:, :2], axis=1) - R).max()), float(np.abs(Q[:, 2]).max()))
    return worst


def bezier():
    print('resolution_u  Bezier circle (4 nodes)         NURBS circle (8 points, order 3)')
    for ru in (1, 2, 4, 8, 12, 24, 64):
        row = []
        for kind in ('bezier', 'nurbs'):
            fresh()
            getattr(bpy.ops.curve, f'primitive_{kind}_circle_add')(radius=1.0)
            o = bpy.context.active_object; o.data.resolution_u = ru
            me, ev, P, E = evaluated_mesh(o)
            row.append((len(P), radial_error(P, E)))
            ev.to_mesh_clear()
        print(f'{ru:11d}  {row[0][0]:4d} vertices, max radial error {row[0][1]:.2e}   {row[1][0]:4d} vertices, max radial error {row[1][1]:.2e}')
    fresh()
    bpy.ops.curve.primitive_bezier_circle_add(radius=1.0)
    bp = bpy.context.active_object.data.splines[0].bezier_points
    print('Blender handle length for the 4-node circle:', round((bp[0].handle_right - bp[0].co).length, 8),
          ' ideal 4/3*tan(pi/8) =', round(4 / 3 * math.tan(math.pi / 8), 8))


def circle_through(N, handle):
    fresh()
    data = bpy.data.curves.new('c', 'CURVE'); data.dimensions = '3D'; data.resolution_u = 64
    sp = data.splines.new('BEZIER'); sp.bezier_points.add(N - 1); sp.use_cyclic_u = True
    h = 4 / 3 * math.tan(math.pi / (2 * N))
    for i, p in enumerate(sp.bezier_points):
        a = 2 * math.pi * i / N
        c = Vector((math.cos(a), math.sin(a), 0)); t = Vector((-math.sin(a), math.cos(a), 0))
        p.co = c
        if handle == 'AUTO':
            p.handle_left_type = p.handle_right_type = 'AUTO'
        else:
            p.handle_left_type = p.handle_right_type = 'FREE'
            p.handle_left = c - t * h; p.handle_right = c + t * h
    o = bpy.data.objects.new('c', data); bpy.context.scene.collection.objects.link(o)
    bpy.context.view_layer.update()
    me, ev, P, E = evaluated_mesh(o)
    err = radial_error(P, E); ev.to_mesh_clear()
    return err


def handles():
    print(' nodes   Auto handles   tangent handles of length (4/3)tan(pi/2N)   chord-only polygon with the same nodes')
    for N in (3, 4, 6, 8, 12, 16):
        a = circle_through(N, 'AUTO'); f = circle_through(N, 'FREE')
        print(f'{N:6d}   {a:.2e}       {f:.2e}                                  {1 - math.cos(math.pi / N):.2e}')


def tube():
    R, A, n = 10.0, 0.025, 256
    print('bevel_resolution  vertices  faces  ring size  area measured  area predicted  ratio to exact torus area')
    exact = 4 * math.pi ** 2 * R * A
    for br in range(0, 7):
        fresh()
        d = bpy.data.curves.new('t', 'CURVE'); d.dimensions = '3D'; d.bevel_depth = A; d.bevel_resolution = br
        sp = d.splines.new('POLY'); sp.points.add(n - 1); sp.use_cyclic_u = True
        for j, p in enumerate(sp.points):
            t = 2 * math.pi * j / n; p.co = (R * math.cos(t), R * math.sin(t), 0, 1)
        o = bpy.data.objects.new('t', d); bpy.context.scene.collection.objects.link(o)
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get(); ev = o.evaluated_get(dg); me = ev.to_mesh()
        V, F = len(me.vertices), len(me.polygons)
        area = sum(p.area for p in me.polygons)
        ring = V // n
        pred = 2 * ring * A * math.sin(math.pi / ring) * 2 * n * R * math.sin(math.pi / n)
        print(f'{br:16d}  {V:8d}  {F:5d}  {ring:9d}  {area:13.6f}  {pred:14.6f}  {area / exact:.5f}')
        ev.to_mesh_clear()
    print('exact torus area 4 pi^2 R a =', round(exact, 6))


if __name__ == '__main__':
    {'bezier': bezier, 'handles': handles, 'tube': tube}[sys.argv[1]]()
