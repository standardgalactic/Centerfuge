"""Figure 14.1: distance to the lattice, separation of vertices, and the count a tolerance reports."""
import itertools, math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from arrangement_family import family_normals, summarize

D = math.pi / 180
OI = {'a': '#0072B2', 'b': '#E69F00', 'c': '#CC79A7'}
deltas = 10 ** np.linspace(-6, -1, 11)
fig, ax = plt.subplots(1, 2, figsize=(9.2, 3.5), constrained_layout=True)
for (beta, col) in ((20, OI['a']), (35, OI['b']), (50, OI['c'])):
    seps = []
    for d in deltas:
        P = np.array(summarize(family_normals(d, beta * D))['vertices'])
        seps.append(min(np.linalg.norm(p - q) for p, q in itertools.combinations(P, 2)))
    ax[0].loglog(deltas, seps, 'o-', color=col, ms=4, lw=1.4, label=f'$\\beta={beta}^\\circ$')
ax[0].axhline(1e-7, color='0.4', lw=1, ls='--'); ax[0].text(1.2e-6, 1.5e-7, 'merge tolerance $10^{-7}$', fontsize=8, color='0.3')
ax[0].legend(fontsize=8, frameon=False, loc='upper left')
ax[0].set_xlabel('distance $\\delta$ of $\\alpha$ from the lattice (radians)'); ax[0].set_ylabel('smallest separation of distinct vertices')
ax[0].set_title('Separation shrinks in proportion to $\\delta$', fontsize=10)
ds = 10 ** np.linspace(-8.5, -4, 46)
for tol, col, lab in ((1e-9, OI['a'], '$10^{-9}$'), (1e-7, OI['b'], '$10^{-7}$'), (1e-5, OI['c'], '$10^{-5}$')):
    cnt = []
    for d in ds:
        N = family_normals(d, 35 * D); pts = []
        for a, b in itertools.combinations(range(9), 2):
            c = np.cross(N[a], N[b]); c /= np.linalg.norm(c)
            for p in (c, -c):
                if not any(np.linalg.norm(p - q) < tol for q in pts): pts.append(p)
        cnt.append(len(pts))
    ax[1].semilogx(ds, cnt, 's-', color=col, ms=3.5, lw=1.2, label=f'tolerance {lab}')
ax[1].set_xlabel('distance $\\delta$ of $\\alpha$ from the lattice (radians)'); ax[1].set_ylabel('vertices counted')
ax[1].set_title('The count changes where $\\delta$ is about the tolerance', fontsize=10)
ax[1].legend(fontsize=8, frameon=False, loc='center left')
for a in ax:
    a.spines[['top', 'right']].set_visible(False)
fig.savefig('figs/fig14_boundary.png', dpi=170)
