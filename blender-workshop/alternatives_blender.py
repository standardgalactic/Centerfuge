"""Chapter 28: the three constructions inside Blender.

    python3 alternatives_blender.py report|boolean|raycast
"""
import sys
import numpy as np
import bpy, bmesh
from mathutils import Vector
from alternatives import CONSTRUCTIONS, analytic, signed_volume

SPEC = dict(n=12, rise=0.2, run=0.3, width=1.2)


def mesh_of(name, V, F):
    me = bpy.data.meshes.new(name); me.from_pydata(V, [], F); me.update(); return me


def facts(me, merge=False):
    bm = bmesh.new(); bm.from_mesh(me)
    if merge: bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    out = dict(V=len(bm.verts), E=len(bm.edges), F=len(bm.faces),
               over2=sum(1 for e in bm.edges if len(e.link_faces) > 2), boundary=sum(1 for e in bm.edges if e.is_boundary),
               volume=bm.calc_volume(signed=True), area=sum(f.calc_area() for f in bm.faces))
    bm.free(); return out


def report():
    A = analytic(SPEC)
    print(f'analytic volume {A["volume"]:.6f} area {A["area"]:.6f}')
    print('construction  merged  V    E    F    edges>2faces  boundary  volume      area       validate_changed')
    for name, fn in CONSTRUCTIONS.items():
        V, F = fn(SPEC)
        for merge in (False, True):
            me = mesh_of(name, V, F); changed = me.validate(verbose=False)
            f = facts(me, merge)
            print(f'{name:12s}  {str(merge):6s} {f["V"]:4d} {f["E"]:4d} {f["F"]:4d}  {f["over2"]:11d}  {f["boundary"]:8d}  {f["volume"]:10.6f}  {f["area"]:9.4f}  {changed}')


def cutter(scene):
    """A box that removes the staircase for y > half its length: x and z generous, y from half to beyond the back."""
    n, u = SPEC['n'], SPEC['run']
    me = mesh_of('cut', *( [(x, y, z) for x in (-1, 3) for y in (1.85, n * u + 1) for z in (-1, 5)],
                           [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]))
    o = bpy.data.objects.new('cut', me); scene.collection.objects.link(o); return o


def boolean():
    sc = bpy.data.scenes.new('S'); n, r, u, w = SPEC['n'], SPEC['rise'], SPEC['run'], SPEC['width']
    y0 = 1.85                                      # inside step 7, so the cut plane meets no existing face
    full = int(y0 // u); part = y0 - full * u
    expect = w * r * (u * full * (full + 1) / 2 + part * (full + 1))
    print(f'volume remaining after cutting away y > {y0}: expected {expect:.6f}')
    cut = cutter(sc)
    for solver, self_ in (('EXACT', False), ('EXACT', True), ('FLOAT', False)):
        for name, fn in CONSTRUCTIONS.items():
            V, F = fn(SPEC)
            o = bpy.data.objects.new(name, mesh_of(name, V, F)); sc.collection.objects.link(o)
            m = o.modifiers.new('b', 'BOOLEAN'); m.operation = 'DIFFERENCE'; m.object = cut; m.solver = solver
            if solver == 'EXACT': m.use_self = self_
            sc.view_layers[0].update()
            ev = o.evaluated_get(sc.view_layers[0].depsgraph); me = ev.to_mesh(); nf = len(me.polygons)
            vol = signed_volume([tuple(v.co) for v in me.vertices], [tuple(p.vertices) for p in me.polygons]) if nf else float('nan')
            print(f'{solver:5s} self={str(self_):5s} {name:8s} faces {nf:3d}  volume {vol:10.6f}  error {vol-expect:+.6f}'); ev.to_mesh_clear()
            bpy.data.objects.remove(o)


def raycast():
    sc = bpy.data.scenes.new('S'); rng = np.random.default_rng(0)
    n, u, w = SPEC['n'], SPEC['run'], SPEC['width']
    xs = rng.uniform(0.05, w - 0.05, 200); ys = rng.uniform(0.01, n * u - 0.01, 200)
    res = {}
    for name, fn in CONSTRUCTIONS.items():
        V, F = fn(SPEC); o = bpy.data.objects.new(name, mesh_of(name, V, F)); sc.collection.objects.link(o)
        sc.view_layers[0].update(); dg = sc.view_layers[0].depsgraph; ev = o.evaluated_get(dg)
        z = []
        for x, y in zip(xs, ys):
            ok, loc, nor, idx = ev.ray_cast(Vector((x, y, 10)), Vector((0, 0, -1)))
            z.append(loc.z if ok else np.nan)
        res[name] = np.array(z)
    for k in res: print(f'{k:8s} first-hit height from above: misses {int(np.isnan(res[k]).sum())}, max |difference from prism| {np.nanmax(np.abs(res[k]-res["prism"])):.2e}')


if __name__ == '__main__':
    globals()[sys.argv[-1]]()
