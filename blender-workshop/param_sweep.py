"""Chapter 14: the parameter space of the nine-circle family, and a reproducible member generator.

    python3 param_sweep.py grid|separation|tolerance|members        (members needs Blender's Python module)
"""
import itertools, math, sys
import numpy as np
from arrangement_family import family_normals, summarize, normal

D = math.pi / 180


def counts(al, be, tol=None):
    s = summarize(family_normals(al, be))
    return (len(s['vertices']), s['E'] if 'E' in s else None, s['F'] if 'F' in s else None, s)


def grid():
    types = {}
    exceptions = []
    for a in range(0, 91):
        for b in range(1, 90):
            try:
                s = summarize(family_normals(a * D, b * D))
            except ValueError:
                types.setdefault('coincident', []).append((a, b)); continue
            key = (len(s['vertices']), s['E'], s['F'], tuple(sorted(s['hist'].items())))
            types.setdefault(key, []).append((a, b))
    print('alpha 0..90 deg and beta 1..89 deg in 1-degree steps:', sum(len(v) for v in types.values()), 'members,', len(types), 'combinatorial types')
    for k, v in sorted(types.items(), key=lambda kv: -len(kv[1])):
        al = sorted(set(a for a, b in v)); be = sorted(set(b for a, b in v))
        print(' type', k if k != 'coincident' else k, ':', len(v), 'members; alpha values', al if len(al) <= 8 else f'{len(al)} values', '; beta range', (be[0], be[-1]), 'count', len(be))
    return types


def separation():
    print('delta = distance of alpha from the lattice (degrees)   beta   min separation between distinct vertices   separation/delta(rad)')
    for beta in (20, 35, 50):
        for deg in (10, 1, 0.1, 0.01):
            al = deg * D
            P = np.array(summarize(family_normals(al, beta * D))['vertices'])
            m = min(np.linalg.norm(p - q) for p, q in itertools.combinations(P, 2))
            print(f'{deg:8.2f}                                              {beta:3d}    {m:.4e}                                   {m / al:.3f}')


def tolerance():
    print('delta (rad)   vertices counted at merge tolerance 1e-7 (beta = 35 deg)   min separation')
    for e in (-1, -2, -3, -4, -5, -6, -6.5, -7, -8):
        al = 10 ** e
        N = family_normals(al, 35 * D)
        pts = []
        for a, b in itertools.combinations(range(9), 2):
            c = np.cross(N[a], N[b]); c /= np.linalg.norm(c)
            for p in (c, -c):
                if not any(np.linalg.norm(p - q) < 1e-7 for q in pts):
                    pts.append(p)
        P = np.array(pts)
        m = min(np.linalg.norm(p - q) for p, q in itertools.combinations(P, 2)) if len(P) > 1 else 0
        print(f'{al:10.1e}    {len(pts):3d}                                                    {m:.2e}')




def members():
    """Generate several members of the family into named collections, record each one's specification on the
    collection, and reconstruct the counts from the stored record alone. Safe to run twice."""
    import json
    import bpy
    from mathutils import Vector

    def build(alpha_deg, beta_deg, samples=64, radius=10.0):
        name = f'Arrangement a{alpha_deg:g} b{beta_deg:g}'
        if name in bpy.data.collections:
            return bpy.data.collections[name], False
        normals = family_normals(alpha_deg * D, beta_deg * D)
        s = summarize(normals)
        coll = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(coll)
        for i, n in enumerate(normals):
            n = Vector(n)
            a = Vector((1, 0, 0)) if abs(n.x) < 0.8 else Vector((0, 1, 0))
            u = a.cross(n).normalized(); v = n.cross(u).normalized()
            cu = bpy.data.curves.new(f'{name} circle {i}', 'CURVE'); cu.dimensions = '3D'
            sp = cu.splines.new('POLY'); sp.points.add(samples - 1); sp.use_cyclic_u = True
            for j, p in enumerate(sp.points):
                t = 2 * math.pi * j / samples
                p.co = (*(radius * (u * math.cos(t) + v * math.sin(t))), 1.0)
            o = bpy.data.objects.new(f'{name} circle {i}', cu)
            coll.objects.link(o)
            o['unit_normal'] = list(n)
        coll['spec'] = json.dumps({'alpha_deg': alpha_deg, 'beta_deg': beta_deg, 'samples': samples, 'radius': radius})
        coll['counts'] = json.dumps({'V': len(s['vertices']), 'E': s['E'], 'F': s['F']})
        return coll, True

    bpy.ops.wm.read_factory_settings(use_empty=True)
    specs = [(0, 35), (22.5, 30), (10, 35), (45, 35), (5, 35)]
    for rep in (1, 2):
        made = [build(a, b)[1] for a, b in specs]
        print(f'run {rep}: created {sum(made)} of {len(specs)}; collections {len(bpy.data.collections)}, objects {len(bpy.data.objects)}, curves {len(bpy.data.curves)}')
    print('collection                     recorded counts          counts rebuilt from the stored normals   max |stored normal - family normal|')
    for c in bpy.data.collections:
        spec = json.loads(c['spec']); rec = json.loads(c['counts'])
        N = [np.array(o['unit_normal'][:]) for o in c.objects]
        s = summarize(N)
        ref = family_normals(spec['alpha_deg'] * D, spec['beta_deg'] * D)
        dev = max(np.linalg.norm(a - b) for a, b in zip(N, ref))
        print(f"{c.name:30s} {rec['V']:3d} {rec['E']:3d} {rec['F']:3d}            {len(s['vertices']):3d} {s['E']:3d} {s['F']:3d}                                  {dev:.1e}")


if __name__ == '__main__':
    {'grid': grid, 'separation': separation, 'tolerance': tolerance, 'members': members}[sys.argv[1]]()
