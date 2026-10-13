"""Chapter 17: a Galton-Watson branching process, its extinction law, and a tree built from one realisation.

    python3 branching.py extinction|critical|tree|determinism
"""
import sys
import numpy as np


def gw(m, seed, max_gen=60, cap=20000):
    """Poisson(m) offspring. Returns list of (parent, depth) for every individual, root first; stops at extinction, max_gen, or cap."""
    rng = np.random.default_rng(seed)
    nodes = [(-1, 0)]; frontier = [0]
    for g in range(1, max_gen + 1):
        nxt = []
        kids = rng.poisson(m, size=len(frontier))
        for par, k in zip(frontier, kids):
            for _ in range(int(k)):
                nodes.append((par, g)); nxt.append(len(nodes) - 1)
                if len(nodes) >= cap:
                    return nodes, 'cap'
        if not nxt:
            return nodes, 'extinct'
        frontier = nxt
    return nodes, 'alive'


def q_exact(m, it=2000):
    """Smallest root of q = exp(m(q-1)) by fixed-point iteration from 0."""
    q = 0.0
    for _ in range(it):
        q = np.exp(m * (q - 1))
    return q


def layout(nodes):
    """Tidy 2D layout: y = -depth, leaves get consecutive x in depth-first order, parents sit at the mean x of their children."""
    n = len(nodes)
    kids = [[] for _ in range(n)]
    for i, (p, d) in enumerate(nodes):
        if p >= 0:
            kids[p].append(i)
    x = [0.0] * n; nxt = [0]
    stack = [(0, False)]
    while stack:
        v, done = stack.pop()
        if done:
            x[v] = float(np.mean([x[c] for c in kids[v]]))
        elif not kids[v]:
            x[v] = float(nxt[0]); nxt[0] += 1
        else:
            stack.append((v, True))
            for c in reversed(kids[v]):
                stack.append((c, False))
    return [(x[i], -float(nodes[i][1])) for i in range(n)]


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'determinism':
        a, _ = gw(1.5, 4); b, _ = gw(1.5, 4); c, _ = gw(1.5, 5)
        print(a == b, len(a), len(c))
    elif cmd == 'extinction':
        N = 2000
        print('m  q_formula  fraction_extinct(sd_binom)  outcomes: extinct/cap/alive')
        for m in (0.8, 1.0, 1.2, 1.5, 2.0):
            res = [gw(m, sd)[1] for sd in range(N)]
            f = np.mean([r == 'extinct' for r in res]); se = np.sqrt(f * (1 - f) / N)
            print(m, round(q_exact(m), 4), f'{f:.4f} +- {se:.4f}', [res.count(k) for k in ('extinct', 'cap', 'alive')])
    elif cmd == 'critical':
        # total progeny of the critical process among extinct runs: tail P(T>=t)
        N = 4000
        T = [len(gw(1.0, sd, max_gen=400, cap=100000)[0]) for sd in range(N)]
        T = np.array(T)
        for t in (2, 10, 100, 1000):
            print(t, round(float((T >= t).mean()), 4), round(float((T >= t).mean() * np.sqrt(t)), 3))
    elif cmd == 'tree':
        for sd in range(40):
            nodes, st = gw(1.5, sd, cap=400)
            print(sd, len(nodes), st, max(d for _, d in nodes))
