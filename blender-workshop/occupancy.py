"""Chapter 16: occupancy on a lattice. Random site occupancy, spanning, and a cave-smoothing cellular automaton.

    python3 occupancy.py percolation|finite|smooth|fixed|determinism
"""
import sys
import numpy as np
from scipy import ndimage

FOUR = ndimage.generate_binary_structure(2, 1)    # 4-neighbourhood
EIGHT = ndimage.generate_binary_structure(2, 2)   # 8-neighbourhood


def occupy(n, p, seed):
    """n x n grid; each site occupied independently with probability p."""
    return np.random.default_rng(seed).random((n, n)) < p


def spans(grid):
    """True if one 4-connected occupied cluster touches both top and bottom rows."""
    lab, k = ndimage.label(grid, structure=FOUR)
    top = set(lab[0][lab[0] > 0]); bot = set(lab[-1][lab[-1] > 0])
    return bool(top & bot)


def smooth_step(wall):
    """Cave rule: a cell is wall next step if at least 5 of its 8 neighbours and itself total >= 5 walls
    (count includes the cell; outside the grid counts as wall)."""
    padded = np.pad(wall, 1, constant_values=True).astype(np.uint8)
    cnt = sum(np.roll(np.roll(padded, i, 0), j, 1) for i in (-1, 0, 1) for j in (-1, 0, 1))[1:-1, 1:-1]
    return cnt >= 5


def smooth(wall, max_steps=100):
    """Iterate to a fixed point; return (grid, steps taken, reached fixed point)."""
    for s in range(max_steps):
        nxt = smooth_step(wall)
        if np.array_equal(nxt, wall):
            return wall, s, True
        wall = nxt
    return wall, max_steps, False


def open_stats(wall):
    lab, k = ndimage.label(~wall, structure=FOUR)
    if k == 0:
        return 0, 0.0, 0.0
    sizes = np.bincount(lab.ravel())[1:]
    return k, sizes.max() / (~wall).sum(), (~wall).mean()


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'percolation':
        for n in (32, 64, 128, 256):
            row = []
            for p in (0.50, 0.55, 0.58, 0.5927, 0.61, 0.65, 0.70):
                s = [spans(occupy(n, p, sd)) for sd in range(400)]
                row.append(f'{np.mean(s):.3f}')
            print(n, row)
    elif cmd == 'finite':
        # p at which spanning probability crosses 0.5, by bisection on a seed ensemble
        for n in (32, 64, 128, 256):
            lo, hi = 0.5, 0.7
            for _ in range(10):
                mid = (lo + hi) / 2
                f = np.mean([spans(occupy(n, mid, sd)) for sd in range(400)])
                lo, hi = (mid, hi) if f < 0.5 else (lo, mid)
            print(n, round((lo + hi) / 2, 4))
    elif cmd == 'smooth':
        n = 64
        print('p_wall  steps(mean sd)  fixed%  open_components(mean)  largest_frac(mean)  open_frac(mean)')
        for p in (0.40, 0.45, 0.50, 0.55, 0.60):
            r = []
            for sd in range(200):
                g, st, ok = smooth(occupy(n, p, sd))
                k, lf, of = open_stats(g)
                r.append((st, ok, k, lf, of))
            a = np.array(r, float)
            print(p, f'{a[:,0].mean():.1f} {a[:,0].std():.1f}', f'{100*a[:,1].mean():.0f}', f'{a[:,2].mean():.1f}',
                  f'{a[:,3].mean():.3f}', f'{a[:,4].mean():.3f}')
    elif cmd == 'fixed':
        g, st, ok = smooth(occupy(64, 0.45, 3))
        print(st, ok, np.array_equal(smooth_step(g), g))
    elif cmd == 'determinism':
        a = occupy(64, 0.45, 7); b = occupy(64, 0.45, 7); c = occupy(64, 0.45, 8)
        print(np.array_equal(a, b), int((a != c).sum()), a.mean())
