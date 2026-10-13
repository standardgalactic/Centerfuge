"""Chapter 18: periodic Voronoi cells, Lloyd relaxation, and the statistics of a foam-like arrangement.

    python3 foam.py euler|relax|lewis|determinism
"""
import sys
import numpy as np
from scipy.spatial import Voronoi


def cells(pts):
    """Voronoi cells of pts in the unit torus. Returns a list of (n,2) vertex arrays (counter-clockwise, unclipped, may leave [0,1)^2)."""
    n = len(pts)
    shifts = [(i, j) for i in (-1, 0, 1) for j in (-1, 0, 1)]
    big = np.vstack([pts + np.array(s) for s in shifts])
    vor = Voronoi(big)
    c0 = shifts.index((0, 0)) * n
    out = []
    for k in range(n):
        reg = vor.regions[vor.point_region[c0 + k]]
        v = vor.vertices[reg]
        ang = np.arctan2(v[:, 1] - pts[k, 1], v[:, 0] - pts[k, 0])
        out.append(v[np.argsort(ang)])
    return out


def area(poly):
    x, y = poly[:, 0], poly[:, 1]
    return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def centroid(poly):
    x, y = poly[:, 0], poly[:, 1]; x1, y1 = np.roll(x, -1), np.roll(y, -1)
    cr = x * y1 - x1 * y; A = cr.sum() / 2
    return np.array([((x + x1) * cr).sum(), ((y + y1) * cr).sum()]) / (6 * A)


def lloyd(pts, steps):
    for _ in range(steps):
        pts = np.array([centroid(c) for c in cells(pts)]) % 1.0
    return pts


def sides(poly, tol=1e-9):
    """Number of distinct vertices (a zero-length edge is not a side)."""
    keep = [0]
    for i in range(1, len(poly)):
        if np.linalg.norm(poly[i] - poly[keep[-1]]) > tol:
            keep.append(i)
    if len(keep) > 1 and np.linalg.norm(poly[keep[0]] - poly[keep[-1]]) <= tol:
        keep.pop()
    return len(keep)


def stats(pts):
    cs = cells(pts); s = np.array([sides(c) for c in cs]); a = np.array([area(c) for c in cs])
    return s, a


if __name__ == '__main__':
    cmd = sys.argv[1]
    N = 400
    if cmd == 'determinism':
        a = np.random.default_rng(3).random((N, 2)); b = np.random.default_rng(3).random((N, 2))
        print(np.array_equal(a, b), np.array_equal(stats(a)[0], stats(b)[0]))
    elif cmd == 'euler':
        for sd in range(5):
            s, a = stats(np.random.default_rng(sd).random((N, 2)))
            print(sd, 'mean sides', s.mean(), 'sum area', round(a.sum(), 12), 'min area', round(a.min(), 6))
    elif cmd == 'relax':
        print('steps  mean_sides  sd_sides  frac6  area_CV  (mean +- sd over 20 seeds)')
        for st in (0, 1, 2, 5, 10, 20, 50):
            r = []
            for sd in range(20):
                s, a = stats(lloyd(np.random.default_rng(sd).random((N, 2)), st))
                r.append((s.mean(), s.std(), (s == 6).mean(), a.std() / a.mean()))
            r = np.array(r)
            print(st, ' '.join(f'{r[:,i].mean():.3f}+-{r[:,i].std():.3f}' for i in range(4)))
    elif cmd == 'lewis':
        S = []; A = []
        for sd in range(20):
            s, a = stats(np.random.default_rng(sd).random((N, 2))); S += list(s); A += list(a / a.mean())
        S = np.array(S); A = np.array(A)
        for n in range(3, 11):
            m = S == n
            print(n, int(m.sum()), round(float(A[m].mean()), 3) if m.any() else None)
        sl = np.polyfit(S[(S >= 4) & (S <= 8)], A[(S >= 4) & (S <= 8)], 1); print('linear fit area vs sides (4..8):', sl)
