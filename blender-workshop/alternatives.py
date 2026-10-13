"""Chapter 28: three constructions of the same solid, and measurements that tell them apart. Pure Python and numpy.

    python3 alternatives.py table|thickness|interpret
A staircase of n solid steps (n, rise r, run u, width w): step k covers y in ((k-1)u, ku), x in (0, w), and has height k*r.
"""
import numpy as np
from stairs import geometry as prism


def cuboid(x0, x1, y0, y1, z0, z1, base):
    v = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    f = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    return v, [tuple(base + i for i in q) for q in f]


def columns(spec):
    """B: one cuboid per step, from the floor to the step's height; neighbouring cuboids touch along partial faces."""
    n, r, u, w = spec['n'], spec['rise'], spec['run'], spec['width']; V, F = [], []
    for k in range(1, n + 1):
        v, f = cuboid(0, w, (k - 1) * u, k * u, 0, k * r, len(V)); V += v; F += f
    return V, F


def layers(spec):
    """C: one slab per height, each of thickness r, running from where the step begins to the back wall."""
    n, r, u, w = spec['n'], spec['rise'], spec['run'], spec['width']; V, F = [], []
    for k in range(1, n + 1):
        v, f = cuboid(0, w, (k - 1) * u, n * u, (k - 1) * r, k * r, len(V)); V += v; F += f
    return V, F


CONSTRUCTIONS = {'prism': lambda s: prism(s), 'columns': columns, 'layers': layers}


def triangles(V, F):
    V = np.array(V, float); T = []
    for f in F:
        for i in range(1, len(f) - 1): T.append((f[0], f[i], f[i + 1]))
    return V, np.array(T)


def signed_volume(V, F):
    V, T = triangles(V, F); a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    return float(np.einsum('ij,ij->i', a, np.cross(b, c)).sum() / 6)


def area(V, F):
    """Surface area by Newell's formula per face, which is exact for planar faces including concave ones."""
    V = np.array(V, float); tot = 0.0
    for f in F:
        P = V[list(f)]; tot += 0.5 * np.linalg.norm(np.cross(P, np.roll(P, -1, axis=0)).sum(axis=0))
    return float(tot)


def edge_counts(V, F, places=6):
    """Faces per undirected edge, with vertices identified by rounded position, so unmerged copies count as one."""
    key = {}; idx = []
    for v in V:
        k = tuple(round(c, places) for c in v); idx.append(key.setdefault(k, len(key)))
    cnt = {}
    for f in F:
        for i in range(len(f)):
            e = tuple(sorted((idx[f[i]], idx[f[(i + 1) % len(f)]]))); cnt[e] = cnt.get(e, 0) + 1
    return cnt


def analytic(spec):
    n, r, u, w = spec['n'], spec['rise'], spec['run'], spec['width']
    return dict(volume=w * r * u * n * (n + 1) / 2, area=2 * u * r * n * (n + 1) / 2 + w * 2 * n * (u + r))


def height_at(spec, y):
    n, r, u = spec['n'], spec['rise'], spec['run']
    k = np.clip(np.ceil(y / u), 1, n); return np.where((y > 0) & (y < n * u), k * r, 0.0)


def vertical_hits(V, F, xs, ys):
    """Sorted z of every crossing of the vertical line through (x, y), for each query point (Moller-Trumbore, vectorised over points)."""
    V, T = triangles(V, F); a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    out = []
    d = np.array([0.0, 0.0, 1.0])
    e1, e2 = b - a, c - a; p = np.cross(d, e2); det = np.einsum('ij,ij->i', e1, p)
    ok = np.abs(det) > 1e-12
    for x, y in zip(xs, ys):
        o = np.array([x, y, -10.0]); s = o - a
        inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
        uu = np.einsum('ij,ij->i', s, p) * inv
        q = np.cross(s, e1); vv = (q @ d) * inv; t = np.einsum('ij,ij->i', e2, q) * inv
        hit = ok & (uu >= 0) & (vv >= 0) & (uu + vv <= 1)
        out.append(np.sort(t[hit] - 10.0))
    return out


def table(spec):
    A = analytic(spec)
    print(f'spec {spec}   analytic volume {A["volume"]:.6f}   analytic area {A["area"]:.6f}')
    print('construction   verts  faces  volume        area        area/analytic  edges with !=2 faces')
    for name, fn in CONSTRUCTIONS.items():
        V, F = fn(spec); ec = edge_counts(V, F)
        print(f'{name:13s}  {len(V):5d}  {len(F):5d}  {signed_volume(V, F):11.6f}  {area(V, F):11.6f}  {area(V, F) / A["area"]:8.4f}      {sum(1 for c in ec.values() if c != 2)} of {len(ec)}')


def thickness(spec, m=300, seed=0):
    rng = np.random.default_rng(seed); n, r, u, w = spec['n'], spec['rise'], spec['run'], spec['width']
    xs = rng.uniform(0.05, w - 0.05, m); ys = rng.uniform(0.01, n * u - 0.01, m); true = height_at(spec, ys)
    print('construction   hits per vertical line (min..max)   mean |error| of (second hit - first hit)   mean |error| of (last hit - first hit)   first hit correct')
    for name, fn in CONSTRUCTIONS.items():
        V, F = fn(spec); H = vertical_hits(V, F, xs, ys)
        cnt = [len(h) for h in H]
        t12 = np.array([h[1] - h[0] if len(h) >= 2 else np.nan for h in H]); tl = np.array([h[-1] - h[0] for h in H])
        first = np.array([abs(h[0]) < 1e-9 for h in H])
        print(f'{name:13s}  {min(cnt)}..{max(cnt)}                              {np.nanmean(np.abs(t12 - true)):.4f}                                  {np.mean(np.abs(tl - true)):.4f}                              {first.mean():.3f}')


def interpret():
    """A request that states only: 'a staircase of 12 steps rising 2.4'. Three consistent readings, and what each added statement removes."""
    from stairs import volume_formula
    R = {'A: twelve steps, solid top at 2.4': dict(n=12, rise=2.4 / 12),
         'B: twelve risers, upper floor at 2.4, eleven treads': dict(n=11, rise=2.4 / 12),
         'C: twelve steps, 2.4 from first tread to last': dict(n=12, rise=2.4 / 11)}
    va = volume_formula(dict(R['A: twelve steps, solid top at 2.4'], run=0.3, width=1.2))
    print('reading                                               n   rise     solid top   volume    relative to A')
    for k, v in R.items():
        s = dict(v, run=0.3, width=1.2); vol = volume_formula(s)
        print(f'{k:52s}  {s["n"]:2d}  {s["rise"]:.5f}  {s["n"] * s["rise"]:8.4f}   {vol:7.4f}   {vol / va:.4f}')
    lo = volume_formula(dict(R['A: twelve steps, solid top at 2.4'], run=0.25, width=1.0)); hi = volume_formula(dict(R['A: twelve steps, solid top at 2.4'], run=0.35, width=1.5))
    print(f'reading A alone, run 0.25 to 0.35 and width 1.0 to 1.5: volume from {lo:.4f} to {hi:.4f}, ratio {hi / lo:.3f}')
    adds = {'the solid is 2.4 tall': lambda s: abs(s['n'] * s['rise'] - 2.4) < 1e-9, 'every riser is 0.2': lambda s: abs(s['rise'] - 0.2) < 1e-9,
            'there are twelve treads': lambda s: s['n'] == 12, 'there are eleven treads': lambda s: s['n'] == 11}
    for t, f in adds.items():
        print(f'added statement "{t}": readings that survive:', [k[0] for k, v in R.items() if f(v)])


if __name__ == '__main__':
    import sys
    spec = dict(n=12, rise=0.2, run=0.3, width=1.2)
    {'table': table, 'thickness': thickness}[sys.argv[1]](spec) if sys.argv[1] != 'interpret' else interpret()
