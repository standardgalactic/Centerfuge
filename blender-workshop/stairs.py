"""Chapter 22: a reusable constructor with a validated specification and recorded provenance.

    python3 stairs.py check|session      (check needs Blender's Python module)
A staircase of n solid steps: step k covers run (k-1)*run .. k*run along y, has height k*rise, and spans width along x.
"""
import hashlib, json, sys

KEYS = {'n': int, 'rise': float, 'run': float, 'width': float}
VERSION = 1
GEN = 'Generated'


def validate(spec):
    """Return a cleaned copy of the specification or raise ValueError saying which entry is wrong."""
    extra = set(spec) - set(KEYS)
    if extra:
        raise ValueError(f'unknown keys {sorted(extra)}')
    out = {}
    for k, t in KEYS.items():
        if k not in spec:
            raise ValueError(f'missing {k}')
        v = spec[k]
        if t is int:
            if isinstance(v, bool) or v != int(v):
                raise ValueError(f'{k} must be a whole number, got {v!r}')
            v = int(v)
            if not 1 <= v <= 200:
                raise ValueError(f'{k} must be from 1 to 200, got {v}')
        else:
            v = float(v)
            if not 0.01 <= v <= 100.0:
                raise ValueError(f'{k} must be from 0.01 to 100, got {v}')
        out[k] = v
    return out


def geometry(spec):
    """Vertices and faces (lists) of the staircase prism; pure Python, no Blender needed."""
    s = validate(spec); n, r, u, w = s['n'], s['rise'], s['run'], s['width']
    prof = [(0.0, 0.0), (n * u, 0.0), (n * u, n * r)]
    for k in range(n, 1, -1):
        prof += [((k - 1) * u, k * r), ((k - 1) * u, (k - 1) * r)]
    prof += [(0.0, r)]
    m = len(prof)
    verts = [(0.0, y, z) for y, z in prof] + [(w, y, z) for y, z in prof]
    faces = [tuple(range(m - 1, -1, -1)), tuple(range(m, 2 * m))]            # caps (x=0 faces -x, x=w faces +x)
    faces += [(i, (i + 1) % m, m + (i + 1) % m, m + i) for i in range(m)]   # sides
    return verts, faces


def volume_formula(spec):
    s = validate(spec); n = s['n']
    return s['width'] * s['rise'] * s['run'] * n * (n + 1) / 2


def geometry_hash(verts, faces, places=5):
    h = hashlib.sha1()
    for v in verts:
        h.update(','.join(f'{c:.{places}f}' for c in v).encode())
    h.update(json.dumps(faces).encode())
    return h.hexdigest()[:12]


def spec_json(spec):
    return json.dumps(validate(spec), sort_keys=True)
