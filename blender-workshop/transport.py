"""Chapter 19: flow on a lattice network whose conductances adapt to the flow they carry.

    python3 transport.py kirchhoff|adapt|sweep|determinism
Model: nodes of an n x n grid, unit-length edges; conductance D_e; one source node (+1) and one sink node (-1).
Flow solves sum_e D_e (p_i - p_j) = I_i. Adaptation: D <- D + dt (f(|Q|) - D), f(q) = q^mu / (1 + q^mu).
"""
import sys
import numpy as np


def grid(n):
    idx = lambda i, j: i * n + j
    E = [(idx(i, j), idx(i, j + 1)) for i in range(n) for j in range(n - 1)] + [(idx(i, j), idx(i + 1, j)) for i in range(n - 1) for j in range(n)]
    return np.array(E)


def solve(n, E, D, src, snk):
    N = n * n
    L = np.zeros((N, N))
    np.add.at(L, (E[:, 0], E[:, 0]), D); np.add.at(L, (E[:, 1], E[:, 1]), D)
    np.add.at(L, (E[:, 0], E[:, 1]), -D); np.add.at(L, (E[:, 1], E[:, 0]), -D)
    I = np.zeros(N); I[src] = 1.0; I[snk] = -1.0
    L[snk, :] = 0; L[snk, snk] = 1; I[snk] = 0.0       # ground the sink at pressure 0
    p = np.linalg.solve(L, I)
    Q = D * (p[E[:, 0]] - p[E[:, 1]])
    return p, Q


def balance_residual(n, E, Q, src, snk):
    net = np.zeros(n * n)
    np.add.at(net, E[:, 0], Q); np.add.at(net, E[:, 1], -Q)
    want = np.zeros(n * n); want[src] = 1.0; want[snk] = -1.0
    return float(np.abs(net - want).max())


def adapt(n, seed, mu, steps=400, dt=0.3):
    E = grid(n); rng = np.random.default_rng(seed)
    D = 1.0 + 0.05 * rng.standard_normal(len(E)); D = np.clip(D, 0.5, None)
    src, snk = 0, n * n - 1
    change = None
    for _ in range(steps):
        p, Q = solve(n, E, D, src, snk)
        a = np.abs(Q) ** mu
        Dn = D + dt * (a / (1 + a) - D)
        change = float(np.abs(Dn - D).max() / dt); D = Dn
    p, Q = solve(n, E, D, src, snk)
    adapt.last_change = change
    return E, D, Q, p


def summary(n, E, D, Q, thr=0.01):
    keep = D > thr
    nodes = set(E[keep].ravel().tolist())
    comps = len(nodes) - int(keep.sum())  # for a connected kept graph, cycle rank = edges - nodes + 1
    cycles = int(keep.sum()) - len(nodes) + 1
    diss = float((Q ** 2 / D).sum())
    return int(keep.sum()), cycles, float(D.sum()), diss


if __name__ == '__main__':
    cmd = sys.argv[1]; n = 16
    if cmd == 'determinism':
        a = adapt(n, 3, 1.5, steps=50)[1]; b = adapt(n, 3, 1.5, steps=50)[1]; c = adapt(n, 4, 1.5, steps=50)[1]
        print(np.array_equal(a, b), float(np.abs(a - c).max()))
    elif cmd == 'kirchhoff':
        E = grid(n); D = np.ones(len(E)); p, Q = solve(n, E, D, 0, n * n - 1)
        print('edges', len(E), 'balance residual', balance_residual(n, E, Q, 0, n * n - 1))
        print('effective resistance p_src', p[0], ' max |Q|', np.abs(Q).max())
        # flow out of source across its two edges sums to 1
        print('source edge flows', Q[(E[:, 0] == 0) | (E[:, 1] == 0)])
    elif cmd == 'adapt':
        for mu in (0.5, 1.0, 1.5, 2.0):
            E, D, Q, p = adapt(n, 0, mu)
            print(mu, summary(n, E, D, Q), 'balance', balance_residual(n, E, Q, 0, n * n - 1))
    elif cmd == 'sweep':
        print('mu  edges_kept  cycles  total_D  dissipation  last_change(max)   (mean +- sd, 10 seeds, n=16, 1500 steps)')
        for mu in (0.5, 0.8, 1.0, 1.2, 1.5, 2.0, 3.0):
            r = []
            for sd in range(10):
                E, D, Q, p = adapt(n, sd, mu, steps=1500)
                r.append(summary(n, E, D, Q) + (adapt.last_change,))
            r = np.array(r, float)
            print(mu, ' '.join(f'{r[:,i].mean():.2f}+-{r[:,i].std():.2f}' for i in range(4)), f'{r[:,4].max():.1e}')
