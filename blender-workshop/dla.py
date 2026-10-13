"""Diffusion-limited aggregation on a square lattice: the rule, a fast version, and measurements.

    python3 dla.py check|dimension|stickiness|anisotropy|window        (numba for the ensembles; the rule itself is dla_py)
"""
import math, sys, random
import numpy as np


def dla_py(n, seed, p_stick=1.0):
    """Grow a cluster of n particles from a seed at the origin. One walker at a time starts on a circle just outside
    the cluster, takes unit steps along the axes, is discarded if it strays beyond three launch radii, and joins the
    cluster, with probability p_stick, whenever it stands next to an occupied site."""
    rng = random.Random(seed)
    occupied = {(0, 0)}
    order = [(0, 0)]
    r_max = 0.0
    while len(order) < n:
        r_launch = r_max + 5.0
        a = rng.random() * 2 * math.pi
        x, y = round(r_launch * math.cos(a)), round(r_launch * math.sin(a))
        kill = 3.0 * r_launch
        while True:
            dx, dy = ((1, 0), (-1, 0), (0, 1), (0, -1))[rng.randrange(4)]
            x, y = x + dx, y + dy
            if x * x + y * y > kill * kill:
                break
            if ((x + 1, y) in occupied or (x - 1, y) in occupied or (x, y + 1) in occupied or (x, y - 1) in occupied) \
                    and (p_stick >= 1.0 or rng.random() < p_stick):
                occupied.add((x, y)); order.append((x, y))
                r_max = max(r_max, math.hypot(x, y))
                break
    return np.array(order)


try:
    from numba import njit

    @njit(cache=True)
    def _dla_nb(n, seed, p_stick, size):
        np.random.seed(seed)
        half = size // 2
        grid = np.zeros((size, size), dtype=np.uint8)
        grid[half, half] = 1
        out = np.zeros((n, 2), dtype=np.int64)
        count = 1
        r_max = 0.0
        while count < n:
            r_launch = r_max + 5.0
            a = np.random.random() * 2 * math.pi
            x = int(round(r_launch * math.cos(a))); y = int(round(r_launch * math.sin(a)))
            kill2 = (3.0 * r_launch) ** 2
            while True:
                k = np.random.randint(0, 4)
                if k == 0: x += 1
                elif k == 1: x -= 1
                elif k == 2: y += 1
                else: y -= 1
                if x * x + y * y > kill2:
                    break
                if grid[half + x + 1, half + y] or grid[half + x - 1, half + y] or grid[half + x, half + y + 1] or grid[half + x, half + y - 1]:
                    if p_stick >= 1.0 or np.random.random() < p_stick:
                        grid[half + x, half + y] = 1
                        out[count, 0] = x; out[count, 1] = y; count += 1
                        r = math.sqrt(x * x + y * y)
                        if r > r_max: r_max = r
                        break
        return out

    def dla(n, seed, p_stick=1.0):
        size = int(2 * (3.0 * (6.0 + 1.2 * math.sqrt(n) * (n ** 0.30)) + 10)) // 2 * 2 + 1
        return _dla_nb(n, seed, p_stick, max(size, 401))
except ImportError:                                                         # pure Python fallback
    dla = dla_py


def gyration(pts):
    c = pts.mean(axis=0)
    return float(np.sqrt(((pts - c) ** 2).sum(axis=1).mean()))


def dimension(pts, lo=100, hi=None, k=24):
    """Fit log N = D log Rg + c over cluster sizes lo..hi, using the first N particles at k log-spaced N."""
    hi = hi or len(pts)
    Ns = np.unique(np.round(np.geomspace(lo, hi, k)).astype(int))
    Rg = np.array([gyration(pts[:n]) for n in Ns])
    D, c = np.polyfit(np.log(Rg), np.log(Ns), 1)
    return float(D)


def harmonic(pts, m, rmin_frac=0.5):
    """Amplitude of the m-fold angular harmonic of the outer part of the cluster; ~1/sqrt(n) for an isotropic cloud."""
    r = np.hypot(pts[:, 0], pts[:, 1]); sel = r > rmin_frac * r.max()
    th = np.arctan2(pts[sel, 1], pts[sel, 0])
    return float(abs(np.exp(1j * m * th).mean())), int(sel.sum())


def check():
    a = dla(1500, 5); b = dla(1500, 5); c = dla(1500, 6)
    print('same seed gives the same cluster:', bool((a == b).all()), '; sites shared with seed 6:', len(set(map(tuple, a)) & set(map(tuple, c))), 'of 1500')
    print('first five sites, seed 5:', a[:5].tolist())
    print('pure Python rule and the fast version are different generators, so compare statistics:')
    Dp = [dimension(dla_py(700, s), lo=60) for s in range(10)]
    Df = [dimension(dla(700, 100 + s), lo=60) for s in range(10)]
    print(f'  N=700, 10 seeds each: pure Python D = {np.mean(Dp):.3f} +/- {np.std(Dp, ddof=1):.3f}; fast version D = {np.mean(Df):.3f} +/- {np.std(Df, ddof=1):.3f}')


def dimension_table():
    Ds, A4, A2, Rgs = [], [], [], []
    for s in range(20):
        pts = dla(3000, 1000 + s)
        Ds.append(dimension(pts, lo=100)); Rgs.append(gyration(pts))
    Ds = np.array(Ds)
    print(f'N=3000, 20 seeds, fit over N in [100,3000]: D = {Ds.mean():.3f}, sd across seeds {Ds.std(ddof=1):.3f}, standard error {Ds.std(ddof=1)/math.sqrt(20):.3f}; range {Ds.min():.3f}..{Ds.max():.3f}')
    print(f'  radius of gyration at N=3000: mean {np.mean(Rgs):.1f}, sd {np.std(Rgs, ddof=1):.1f}')


def stickiness():
    print('p_stick   D (N=2000, fit N in [100,2000], 12 seeds)   Rg at N=2000   seconds')
    import time
    for p in (1.0, 0.5, 0.1, 0.02):
        t = time.time(); Ds = []; R = []
        for s in range(12):
            pts = dla(2000, 2000 + s, p); Ds.append(dimension(pts, lo=100)); R.append(gyration(pts))
        print(f'{p:6.2f}    {np.mean(Ds):.3f} +/- {np.std(Ds, ddof=1):.3f}                         {np.mean(R):6.1f}        {time.time() - t:.1f}')


def anisotropy():
    n = 3000
    a4 = []; a2 = []; a1 = []; ns = []
    for s in range(20):
        pts = dla(n, 3000 + s)
        h4, k = harmonic(pts, 4); h2, _ = harmonic(pts, 2); h8, _ = harmonic(pts, 8)
        a4.append(h4); a2.append(h2); a1.append(h8); ns.append(k)
    print(f'outer-cluster angular harmonics, N={n}, 20 seeds (outer half of radius; about {int(np.mean(ns))} particles)')
    print(f'  4-fold amplitude {np.mean(a4):.3f} +/- {np.std(a4, ddof=1):.3f}; 2-fold {np.mean(a2):.3f} +/- {np.std(a2, ddof=1):.3f}; 8-fold {np.mean(a1):.3f} +/- {np.std(a1, ddof=1):.3f}')
    rng = np.random.default_rng(0)
    iso = [abs(np.exp(1j * 4 * rng.uniform(0, 2 * np.pi, int(np.mean(ns)))).mean()) for _ in range(2000)]
    print(f'  isotropic cloud of the same size: 4-fold amplitude {np.mean(iso):.3f} +/- {np.std(iso):.3f}')


def window():
    print('fit window                 D (mean of 20 seeds, N=3000)   sd across seeds')
    clusters = [dla(3000, 1000 + s) for s in range(20)]
    for lo, hi in ((20, 200), (100, 600), (200, 1000), (500, 3000), (1000, 3000), (100, 3000)):
        Ds = [dimension(c, lo=lo, hi=hi) for c in clusters]
        print(f'N in [{lo:4d},{hi:4d}]            {np.mean(Ds):.3f}                        {np.std(Ds, ddof=1):.3f}')


if __name__ == '__main__':
    {'check': check, 'dimension': dimension_table, 'stickiness': stickiness, 'anisotropy': anisotropy, 'window': window}[sys.argv[1]]()
