import hashlib
import itertools
import math

import numpy as np

# ---------------------------------------------------------------- the network
def arrangement_graph():
    """Nodes and edges of the nine-circle arrangement of Chapter 11.

    Returns node positions on the unit sphere (n x 3) and a list of edges (i, j)
    with i < j. Each great circle is split at its vertices; consecutive vertices
    along a circle are joined.
    """
    def normal(beta, lam):
        return np.array([math.cos(beta) * math.cos(lam),
                         math.cos(beta) * math.sin(lam), math.sin(beta)])
    normals = [np.array([0.0, 0.0, 1.0])]
    normals += [normal(0.0, k * math.pi / 4) for k in range(4)]
    normals += [normal(math.pi / 6, math.pi / 8 + k * math.pi / 2) for k in range(4)]

    pts = []
    for a, b in itertools.combinations(range(9), 2):
        c = np.cross(normals[a], normals[b])
        c /= np.linalg.norm(c)
        for p in (c, -c):
            if not any(np.linalg.norm(p - q) < 1e-9 for q in pts):
                pts.append(p)
    pos = np.array(pts)

    edges = set()
    for n in normals:
        ref = np.array([1.0, 0, 0]) if abs(n[0]) < 0.8 else np.array([0, 1.0, 0])
        u = np.cross(ref, n)
        u /= np.linalg.norm(u)
        v = np.cross(n, u)
        on = [i for i, p in enumerate(pos) if abs(n @ p) < 1e-9]
        on.sort(key=lambda i: math.atan2(pos[i] @ v, pos[i] @ u))
        for k in range(len(on)):
            i, j = on[k], on[(k + 1) % len(on)]
            edges.add((min(i, j), max(i, j)))
    return pos, sorted(edges)

def incidence(n, edges):
    """B[i, e] = +1 at the tail of edge e and -1 at its head: (B q)_i is the
    net outflow at node i for edge flows q (positive from tail to head)."""
    B = np.zeros((n, len(edges)))
    for e, (i, j) in enumerate(edges):
        B[i, e], B[j, e] = 1.0, -1.0
    return B

# ----------------------------------------------------------------- the update
def step(x, sigma, dt, B, kappa, lam, north, south, cap=None):
    """One explicit step x_{k+1} = F(x_k, u_k, dt; theta).

    Flow on each edge is kappa * (x_tail - x_head), optionally clipped to
    [-cap, cap]. Source sigma enters at `north`; a drain lam * x removes stock at
    `south`. Returns the new state and the drain actually applied.
    """
    q = kappa * (B.T @ x)
    if cap is not None:
        q = np.clip(q, -cap, cap)
    drain = lam * x[south]
    new = x - dt * (B @ q)
    new[north] += dt * sigma
    new[south] -= dt * drain
    return new, drain

def run(x0, sigmas, dt, B, kappa, lam, north, south, cap=None, record=False):
    x = x0.copy()
    mass, ledger_err, traj = [x.sum()], 0.0, [x.copy()]
    for s in sigmas:
        new, drain = step(x, s, dt, B, kappa, lam, north, south, cap)
        ledger_err = max(ledger_err, abs((new.sum() - x.sum()) - dt * (s - drain)))
        x = new
        mass.append(x.sum())
        if record:
            traj.append(x.copy())
    return x, ledger_err, (np.array(traj) if record else None)

def digest(x):
    return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()[:16]

if __name__ == '__main__':
    pos, edges = arrangement_graph()
    n, m = len(pos), len(edges)
    B = incidence(n, edges)
    deg = np.abs(B).sum(axis=1)
    print('nodes', n, 'edges', m, 'degrees', sorted(set(deg.astype(int))))
    north = int(np.argmax(pos[:, 2]))
    south = int(np.argmin(pos[:, 2]))
    print('poles', pos[north].round(6), pos[south].round(6), 'degrees', deg[north], deg[south])
    print('column sums of B (should be 0):', np.abs(B.sum(axis=0)).max())

    kappa, lam, sigma = 1.0, 0.5, 1.0
    L = kappa * B @ B.T
    D = np.zeros((n, n)); D[south, south] = lam
    M = L + D
    ev = np.linalg.eigvalsh(M)
    evL = np.linalg.eigvalsh(L)
    print('lambda_max(L) =', round(evL[-1], 4), ' lambda_2(L) =', round(evL[1], 5),
          ' lambda_min(M) =', round(ev[0], 5), ' lambda_max(M) =', round(ev[-1], 4))
    nonneg_bound = 1.0 / max(L[i, i] + (lam if i == south else 0.0) for i in range(n))
    stab_bound = 2.0 / ev[-1]
    print('nonnegativity bound dt <=', round(nonneg_bound, 5), ' stability bound dt <', round(stab_bound, 5))

    # steady state
    e_n = np.zeros(n); e_n[north] = sigma
    xstar = np.linalg.solve(M, e_n)
    print('steady state: x*_south =', round(xstar[south], 6), ' expected sigma/lam =', sigma / lam,
          ' min x* =', round(xstar.min(), 6), ' total =', round(xstar.sum(), 4))

    # 1. ledger, and 2. the bounds (source only, empty start; then spike, no source)
    x0 = np.zeros(n)
    spike = np.zeros(n); spike[north] = 1.0
    for dt in (0.05, nonneg_bound * 0.999, 0.13, 0.17, 0.19, 0.21, 0.25):
        steps = 300
        _, err, T1 = run(x0, [sigma] * steps, dt, B, kappa, lam, north, south, record=True)
        _, _, T2 = run(spike, [0.0] * steps, dt, B, kappa, lam, north, south, record=True)
        print(f'dt={dt:.4f}: source run ledger {err:.1e}, min {T1.min():.3e}, max |x| {np.abs(T1).max():.3e}'
              f' | spike run min {T2.min():.3e}, max |x| {np.abs(T2).max():.3e}')
    print('x* range', round(xstar.min(), 4), round(xstar.max(), 4))

    # 3. convergence to steady state
    dt = 0.1
    steps = 12000
    x, err, T = run(x0, [sigma] * steps, dt, B, kappa, lam, north, south, record=True)
    print('after', steps * dt, 'time units: max |x - x*| =', np.abs(x - xstar).max(),
          ' ledger err', err)
    for t_check in (50, 200, 600):
        k = int(t_check / dt)
        print('  t =', t_check, ' max err', np.abs(T[k] - xstar).max())

    # 4. time-step convergence against the exact linear solution at T = 2
    w, V = np.linalg.eigh(M)
    def exact(t):
        return xstar + V @ (np.exp(-w * t) * (V.T @ (x0 - xstar)))
    Tend = 2.0
    errs = []
    for dt in (0.1, 0.05, 0.025, 0.0125):
        steps = int(round(Tend / dt))
        x, _, _ = run(x0, [sigma] * steps, dt, B, kappa, lam, north, south)
        errs.append(np.abs(x - exact(Tend)).max())
    print('dt-convergence errors', [f'{e:.3e}' for e in errs],
          'ratios', [round(errs[i] / errs[i + 1], 3) for i in range(3)])

    # 5. replay, checkpoint, arithmetic-order caveat
    dt, K = 0.1, 400
    record = dict(kappa=kappa, lam=lam, dt=dt, sigmas=[sigma] * K, x0=x0.tolist())
    a, _, _ = run(np.array(record['x0']), record['sigmas'], dt, B, kappa, lam, north, south)
    b, _, _ = run(np.array(record['x0']), record['sigmas'], dt, B, kappa, lam, north, south)
    half, _, _ = run(x0, [sigma] * 200, dt, B, kappa, lam, north, south)
    c, _, _ = run(half, [sigma] * 200, dt, B, kappa, lam, north, south)
    print('replay digests', digest(a), digest(b), ' checkpoint-resume digest', digest(c))
    # same maths, different arithmetic: explicit matrix M instead of edge flows
    xx = x0.copy()
    for _ in range(K):
        xx = xx - dt * (M @ xx) + dt * e_n
    print('matrix form digest', digest(xx), ' max difference', np.abs(xx - a).max())

    # 6. history matters: same frame, same current input, different past
    K = 300
    # same last input (0.0) but different history
    s_off1 = [sigma] * 100 + [0.0] * 200
    s_off2 = [sigma] * 200 + [0.0] * 100
    x1, _, _ = run(x0, s_off1, dt, B, kappa, lam, north, south)
    x2, _, _ = run(x0, s_off2, dt, B, kappa, lam, north, south)
    print('same frame 300, same last input 0, different history: total stock',
          round(x1.sum(), 4), round(x2.sum(), 4), ' max difference', round(np.abs(x1 - x2).max(), 4))

    # 7. capacity-limited flow: nonlinear, conserved, blockage visible in the state
    sig_big, cap = 4.0, 0.3
    dt = 0.05
    T_end = 40.0
    steps = int(T_end / dt)
    x, err, T = run(x0, [sig_big] * steps, dt, B, kappa, lam, north, south, cap=cap, record=True)
    xl, errl, Tl = run(x0, [sig_big] * steps, dt, B, kappa, lam, north, south, cap=None, record=True)
    k20, k40 = int(20 / dt), steps
    slope = (T[k40][north] - T[k20][north]) / 20.0
    print('capped: ledger err', f'{err:.2e}', ' x_N at t=20,40:', round(T[k20][north], 3),
          round(T[k40][north], 3), ' slope', round(slope, 4),
          ' predicted slope sigma - 8*cap =', sig_big - 8 * cap)
    print('uncapped: x_N at t=40', round(Tl[k40][north], 3), ' x_S', round(Tl[k40][south], 3),
          ' expected x_S*', sig_big / lam, ' min x', round(Tl.min(), 4))
    print('capped min x', round(T.min(), 4), ' total stock', round(T[k40].sum(), 3))
