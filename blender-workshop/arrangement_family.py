"""Combinatorics of the nine-circle family: fixed five plus a configurable four.

The fixed five are the equator (normal +Z) and four polar circles whose normals
are horizontal at azimuths k*pi/4. The configurable four have normals at
elevation beta and azimuths alpha + j*pi/2. Everything is counted from the
normals alone, so the same function describes any arrangement in the family.
"""
import itertools
import math

import numpy as np

TOL = 1e-9


def normal(beta, lam):
    return np.array([math.cos(beta) * math.cos(lam),
                     math.cos(beta) * math.sin(lam), math.sin(beta)])


def family_normals(alpha, beta):
    fixed = [np.array([0.0, 0.0, 1.0])] + [normal(0.0, k * math.pi / 4) for k in range(4)]
    flexible = [normal(beta, alpha + j * math.pi / 2) for j in range(4)]
    return fixed + flexible


def blender_euler_normal(x_deg, y_deg, z_deg):
    """Normal of a torus whose axis is local Z, after Blender's XYZ Euler rotation
    R = Rz Ry Rx (Chapter 2). Used to read an arrangement off a script."""
    x, y, z = (math.radians(a) for a in (x_deg, y_deg, z_deg))
    Rx = np.array([[1, 0, 0], [0, math.cos(x), -math.sin(x)], [0, math.sin(x), math.cos(x)]])
    Ry = np.array([[math.cos(y), 0, math.sin(y)], [0, 1, 0], [-math.sin(y), 0, math.cos(y)]])
    Rz = np.array([[math.cos(z), -math.sin(z), 0], [math.sin(z), math.cos(z), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx @ np.array([0.0, 0.0, 1.0])


def vertices(normals):
    """Distinct intersection points of the circles, merged at tolerance TOL."""
    pts = []
    for a, b in itertools.combinations(range(len(normals)), 2):
        c = np.cross(normals[a], normals[b])
        if np.linalg.norm(c) < TOL:
            raise ValueError(f"circles {a} and {b} coincide")
        c = c / np.linalg.norm(c)
        for p in (c, -c):
            if not any(np.linalg.norm(p - q) < 1e-7 for q in pts):
                pts.append(p)
    return np.array(pts)


def summarize(normals):
    n = len(normals)
    pts = vertices(normals)
    on = [[i for i, nv in enumerate(normals) if abs(nv @ p) < 1e-7] for p in pts]
    mult = [len(s) for s in on]
    V, E = len(pts), sum(mult)
    F = 2 - V + E
    hist = {}
    for m in mult:
        hist[m] = hist.get(m, 0) + 1
    # Every pair of circles meets in two antipodal points, so n(n-1) pair-points
    # are shared out among the vertices, a vertex of multiplicity m absorbing C(m,2).
    pair_points = sum(math.comb(m, 2) for m in mult)
    # Faces lost relative to general position: C(m-1, 2) for each vertex.
    loss = sum(math.comb(m - 1, 2) for m in mult)
    return dict(V=V, E=E, F=F, chi=V - E + F, hist=dict(sorted(hist.items())),
                pair_points=pair_points, expected_pair_points=n * (n - 1),
                general_position_F=n * n - n + 2, F_from_loss=n * n - n + 2 - loss,
                vertices=pts, circles_at=on)


def sampled_faces(normals, samples=2_000_000, seed=0):
    """Independent face count: distinct sign patterns over random points of the sphere.
    A sampled count can only undercount (a very small face may be missed)."""
    rng = np.random.default_rng(seed)
    P = rng.normal(size=(samples, 3))
    P /= np.linalg.norm(P, axis=1, keepdims=True)
    signs = (P @ np.array(normals).T) > 0
    codes = signs.astype(np.int64) @ (1 << np.arange(len(normals)))
    return len(np.unique(codes))


if __name__ == '__main__':
    deg = math.pi / 180
    cases = {
        'source script (alpha=0, beta=35)': family_normals(0.0, 35 * deg),
        'teaching case (alpha=22.5, beta=30)': family_normals(22.5 * deg, 30 * deg),
        'alpha=0, beta=30': family_normals(0.0, 30 * deg),
        'alpha=22.5, beta=35': family_normals(22.5 * deg, 35 * deg),
    }
    for name, nv in cases.items():
        s = summarize(nv)
        print(f"{name:38s} V={s['V']} E={s['E']} F={s['F']} chi={s['chi']} mult={s['hist']} "
              f"pairs {s['pair_points']}/{s['expected_pair_points']} F(loss)={s['F_from_loss']} "
              f"sampled F={sampled_faces(nv)}")
    # the source script read off its Euler angles rather than from the family formula
    script = [(0, 0, 0)] + [(0, 90, z) for z in (0, 45, 90, 135)] + [(55, 0, z) for z in (0, 90, 180, 270)]
    nv = [blender_euler_normal(*a) for a in script]
    s = summarize(nv)
    print('source read from Euler angles:', s['V'], s['E'], s['F'], s['hist'])
    # which alpha and beta change the counts? sweep.
    print('sweep over alpha (beta=35):')
    for a in (0, 5, 10, 15, 22.5, 30, 45, 60, 67.5, 90):
        s = summarize(family_normals(a * deg, 35 * deg))
        print(f"  alpha={a:5.1f}  V={s['V']:3d} E={s['E']:3d} F={s['F']:3d} mult={s['hist']}")
    print('sweep over beta (alpha=22.5):')
    for b in (1, 10, 20, 30, 35, 45, 60, 80, 89):
        s = summarize(family_normals(22.5 * deg, b * deg))
        print(f"  beta={b:5.1f}  V={s['V']:3d} E={s['E']:3d} F={s['F']:3d} mult={s['hist']}")
    # classification of the source arrangement's vertices by the circles through them
    s = summarize(cases['source script (alpha=0, beta=35)'])
    labels = ['Eq', 'P0', 'P1', 'P2', 'P3', 'I0', 'I1', 'I2', 'I3']
    kinds = {}
    for p, on in zip(s['vertices'], s['circles_at']):
        key = '+'.join(labels[i] for i in on)
        kinds[key] = kinds.get(key, 0) + 1
    print('source vertex types:', kinds)
    s = summarize(cases['teaching case (alpha=22.5, beta=30)'])
    kinds = {}
    for p, on in zip(s['vertices'], s['circles_at']):
        if len(on) > 2:
            key = '+'.join(labels[i] for i in on)
            kinds[key] = kinds.get(key, 0) + 1
    print('teaching vertices with m>2:', kinds)
