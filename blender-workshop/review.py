"""Chapter 28: staged review of constructed geometry, tested against defects injected into a stand-in delegate.

    python3 review.py table      (pure Python)       python3 review_blender.py check   (same stages on meshes read back from Blender)
The delegate is a function that returns vertices and faces for a specification, with one chosen defect. No model is involved:
the defects are ones that a constructed mesh can have, and the experiment asks only which review stage first sees each of them.
"""
import math
import numpy as np
from stairs import geometry, volume_formula, geometry_hash
from alternatives import columns, signed_volume, area, analytic

SPEC = dict(n=12, rise=0.2, run=0.3, width=1.2)
TOL = 1e-5


def delegate(spec, defect=None):
    V, F = geometry(spec); V = [list(v) for v in V]; F = [tuple(f) for f in F]
    n, r, u, w = spec['n'], spec['rise'], spec['run'], spec['width']; props = {'spec': dict(spec)}
    if defect == 'unit error (x100)': V = [[100 * c for c in v] for v in V]
    elif defect == 'one step too many': V, F = geometry(dict(spec, n=n + 1))
    elif defect == 'one step too few': V, F = geometry(dict(spec, n=n - 1)); V = [list(v) for v in V]
    elif defect == 'inside out': F = [tuple(reversed(f)) for f in F]
    elif defect == 'mirrored along y': V = [[v[0], n * u - v[1], v[2]] for v in V]; F = [tuple(reversed(f)) for f in F]
    elif defect == 'run and rise swapped': V, F = geometry(dict(spec, rise=u, run=r)); V = [list(v) for v in V]
    elif defect == 'one vertex NaN': V[5][2] = float('nan')
    elif defect == 'one vertex off by 0.001': V[5][2] += 1e-3
    elif defect == 'built from columns': V, F = columns(spec); V = [list(v) for v in V]
    elif defect == 'faces with their own vertices':
        NV, NF = [], []
        for f in F:
            NF.append(tuple(range(len(NV), len(NV) + len(f)))); NV += [V[i] for i in f]
        V, F = NV, NF
    elif defect == 'no provenance': props = {}
    elif defect == 'benign: vertices rotated in order':
        k = 7; perm = [(i + k) % len(V) for i in range(len(V))]; inv = {old: new for new, old in enumerate(perm)}
        V = [V[p] for p in perm]; F = [tuple(inv[i] for i in f) for f in F]
    elif defect == 'benign: faces shuffled':
        rng = np.random.default_rng(1); F = [F[i] for i in rng.permutation(len(F))]
    elif defect == 'benign: 1e-9 noise':
        rng = np.random.default_rng(2); V = [[c + rng.normal(0, 1e-9) for c in v] for v in V]
    return V, F, props


def s1_format(V, F, props, spec):
    A = np.array(V, float)
    if not np.isfinite(A).all(): return 'non-finite coordinate'
    if any(i < 0 or i >= len(V) for f in F for i in f): return 'index out of range'


def s2_closed(V, F, props, spec):
    cnt = {}
    for f in F:
        for i in range(len(f)):
            e = tuple(sorted((f[i], f[(i + 1) % len(f)]))); cnt[e] = cnt.get(e, 0) + 1
    bad = sum(1 for c in cnt.values() if c != 2)
    if bad: return f'{bad} edges without exactly two faces'


def s3_volume(V, F, props, spec):
    v = signed_volume(V, F); e = volume_formula(spec)
    if abs(v - e) > TOL * e: return f'volume {v:.4f}, expected {e:.4f}'


def s4_extent(V, F, props, spec):
    A = np.array(V, float); ext = A.max(0) - A.min(0); e = np.array([spec['width'], spec['n'] * spec['run'], spec['n'] * spec['rise']])
    if np.abs(ext - e).max() > TOL * e.max(): return 'extent differs'


def s5_area(V, F, props, spec):
    a = area(V, F); e = analytic(spec)['area']
    if abs(a - e) > TOL * e: return f'area {a:.4f}, expected {e:.4f}'


def s6_provenance(V, F, props, spec):
    if props.get('spec') != spec: return 'provenance missing or different'


def s7_reference(V, F, props, spec):
    if geometry_hash(V, F, places=4) != REF: return 'hash differs from reference'


def canon(V, F, places=4):
    """Order-free signature: the sorted set of faces, each as the cyclic order of its rounded vertex positions starting from the smallest."""
    out = []
    for f in F:
        P = [tuple(round(c, places) + 0.0 for c in V[i]) for i in f]; k = P.index(min(P)); out.append(tuple(P[k:] + P[:k]))
    return tuple(sorted(out))


def s7b_canonical(V, F, props, spec):
    if canon(V, F) != REFC: return 'canonical signature differs'


V0, F0, _ = delegate(SPEC); REF = geometry_hash(V0, F0, places=4); REFC = canon(V0, F0)
STAGES = [('format', s1_format), ('closed', s2_closed), ('volume', s3_volume), ('extent', s4_extent), ('area', s5_area),
          ('provenance', s6_provenance), ('hash', s7_reference), ('canonical', s7b_canonical)]
DEFECTS = ['none', 'unit error (x100)', 'one step too many', 'one step too few', 'inside out', 'mirrored along y', 'run and rise swapped',
           'one vertex NaN', 'one vertex off by 0.001', 'built from columns', 'faces with their own vertices', 'no provenance',
           'benign: vertices rotated in order', 'benign: faces shuffled', 'benign: 1e-9 noise']


def run(V, F, props, stages, spec=SPEC):
    for name, fn in stages:
        try:
            r = fn(V, F, props, spec)
        except Exception as e:
            r = 'check raised ' + type(e).__name__
        if r: return name, r
    return None, None


def table():
    sets = {'S1-S6 (properties)': STAGES[:6], 'S1-S6 + hash': STAGES[:7], 'S1-S6 + canonical': STAGES[:6] + [STAGES[7]]}
    print(f'{"defect":36s}' + ''.join(f'{k:>26s}' for k in sets))
    for d in DEFECTS:
        V, F, p = delegate(SPEC, None if d == 'none' else d)
        print(f'{d:36s}' + ''.join(f'{(run(V, F, p, s)[0] or "passes"):>26s}' for s in sets.values()))


def single():
    print(f'{"defect":36s}' + ''.join(f'{n:>11s}' for n, _ in STAGES))
    for d in DEFECTS:
        V, F, p = delegate(SPEC, None if d == 'none' else d)
        print(f'{d:36s}' + ''.join(f'{("x" if run(V, F, p, [st])[0] else "-"):>11s}' for st in STAGES))


def sweep():
    print('displacement of one vertex   stages that flag it')
    for e in range(-9, 0):
        d = 10.0 ** e; V, F, p = delegate(SPEC); V[5][2] += d
        print(f'{d:10.0e}                   ' + ', '.join(n for n, fn in STAGES if run(V, F, p, [(n, fn)])[0]))


if __name__ == '__main__':
    import sys
    {'table': table, 'single': single, 'sweep': sweep}[sys.argv[1] if len(sys.argv) > 1 else 'table']()
