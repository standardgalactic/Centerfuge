"""Chapter 13: spherical coordinates, great circles, and what float32 does to them.

    python3 sphere_probe.py distance|normal|interp|mesh|arrangement      (Blender's Python module for mathutils and primitives)
"""
import itertools, math, sys
import numpy as np
import bpy
from mathutils import Vector, Quaternion
from arrangement_family import family_normals, summarize

F32 = np.float32


def rel(est, true):
    return abs(est - true) / true


def distance():
    print('true angle   acos(a.b)  f64    chord 2asin(|a-b|/2)  f64   atan2(|axb|,a.b) f64 |  acos f32   chord f32   atan2 f32 | mathutils Vector.angle')
    for th in (1e-1, 1e-2, 1e-3, 1e-4, 1e-6, 1e-8):
        a = np.array([1.0, 0, 0]); b = np.array([math.cos(th), math.sin(th), 0])
        def f64():
            return (math.acos(min(1, a @ b)), 2 * math.asin(np.linalg.norm(a - b) / 2),
                    math.atan2(np.linalg.norm(np.cross(a, b)), a @ b))
        def f32():
            a3, b3 = a.astype(F32), b.astype(F32)
            d = F32(a3 @ b3)
            return (float(np.arccos(np.minimum(F32(1), d))), float(F32(2) * np.arcsin(np.linalg.norm(a3 - b3) / F32(2))),
                    float(np.arctan2(np.linalg.norm(np.cross(a3, b3)), d)))
        r64, r32 = f64(), f32()
        mu = Vector(a).angle(Vector(b))
        print(f'{th:9.0e}   ' + '  '.join(f'{rel(x, th):9.2e}' for x in r64) + ' | ' + '  '.join(f'{rel(x, th):9.2e}' for x in r32) + f' | {rel(mu, th):9.2e}')


def normal():
    """Normal of the great circle through a and b, from points rotated to generic positions.

    Truth is the rotated z axis in float64. 'f32 inputs, f64 cross' isolates the rounding of the coordinates;
    'mathutils' also rounds the cross product."""
    rng = np.random.default_rng(3)
    print('angle between a and b    median / largest error of the normal (radians)')
    print('                         f64 throughout   f32 inputs, f64 cross   mathutils (f32 throughout)   predicted ~ 6e-8 / sin(angle)')
    for label, th in (('1e-1', 1e-1), ('1e-2', 1e-2), ('1e-3', 1e-3), ('1e-4', 1e-4), ('pi-1e-2', math.pi - 1e-2), ('pi-1e-3', math.pi - 1e-3)):
        e = [[], [], []]
        for _ in range(300):
            q = rng.normal(size=4); q /= np.linalg.norm(q)
            w, x, y, z = q
            R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                          [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                          [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
            a = R @ np.array([1.0, 0, 0]); b = R @ np.array([math.cos(th), math.sin(th), 0]); true = R @ np.array([0.0, 0, 1])
            def err(n):
                n = np.asarray(n, dtype=float); n = n / np.linalg.norm(n)
                return math.atan2(np.linalg.norm(np.cross(n, true)), n @ true)
            e[0].append(err(np.cross(a, b)))
            a32, b32 = a.astype(F32).astype(float), b.astype(F32).astype(float)
            e[1].append(err(np.cross(a32, b32)))
            nm = Vector(a).cross(Vector(b)); e[2].append(err(nm[:]))
        print(f'{label:>10s}              ' + '      '.join(f'{np.median(v):.1e} / {np.max(v):.1e}' for v in e) + f'      {6e-8 / math.sin(th):.1e}')


def interp():
    print('arc between endpoints   speed ratio (largest/smallest step) for normalised linear interpolation, 200 steps')
    for deg in (30, 90, 150, 170, 179):
        th = math.radians(deg)
        a = np.array([1.0, 0, 0]); b = np.array([math.cos(th), math.sin(th), 0])
        t = np.linspace(0, 1, 201)
        P = np.array([(1 - s) * a + s * b for s in t]); P /= np.linalg.norm(P, axis=1)[:, None]
        step = np.array([math.acos(min(1, P[i] @ P[i + 1])) for i in range(200)])
        Q = [Vector(a).slerp(Vector(b), s) for s in t]
        sl = np.array([Vector(Q[i]).angle(Q[i + 1]) for i in range(200)])
        dev = max(abs(q.length - 1) for q in Q)
        print(f'{deg:5d} deg             {step.max() / step.min():10.2f}      Vector.slerp: step ratio {sl.max() / sl.min():.4f}, largest |length-1| {dev:.1e}')


def mesh():
    print('UV sphere (segments x rings)  V   F  area/4pi   volume/(4pi/3)  face area max/min')
    def stats(me):
        A = np.array([p.area for p in me.polygons])
        vol = 0.0
        for p in me.polygons:
            vs = [me.vertices[i].co for i in p.vertices]
            for k in range(1, len(vs) - 1):
                vol += vs[0].dot(vs[k].cross(vs[k + 1])) / 6
        return len(me.vertices), len(me.polygons), A.sum() / (4 * math.pi), vol / (4 * math.pi / 3), A.max() / A.min()
    for seg, ring in ((16, 8), (32, 16), (64, 32)):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=seg, ring_count=ring)
        V, F, a, v, r = stats(bpy.context.active_object.data)
        print(f'{seg:3d} x {ring:2d}                    {V:5d} {F:5d}  {a:.5f}    {v:.5f}        {r:.2f}')
    print('Icosphere (subdivisions)')
    for sub in (2, 3, 4):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.mesh.primitive_ico_sphere_add(radius=1.0, subdivisions=sub)
        V, F, a, v, r = stats(bpy.context.active_object.data)
        print(f'{sub:3d}                          {V:5d} {F:5d}  {a:.5f}    {v:.5f}        {r:.2f}')


def count(normals, tol):
    pts = []
    for a, b in itertools.combinations(range(len(normals)), 2):
        c = np.cross(normals[a], normals[b]); c = c / np.linalg.norm(c)
        for p in (c, -c):
            if not any(np.linalg.norm(p - q) < tol for q in pts):
                pts.append(p)
    return pts


def arrangement():
    deg = math.pi / 180
    for name, (al, be) in (('source', (0.0, 35 * deg)), ('teaching', (22.5 * deg, 30 * deg))):
        N64 = family_normals(al, be)
        N32 = [np.array(Vector(n)[:], dtype=np.float64) for n in N64]          # through mathutils: rounded to float32
        ang = min(math.acos(min(1, abs(N64[i] @ N64[j]))) for i, j in itertools.combinations(range(9), 2))
        P64 = count(N64, 1e-7)
        ref = np.array(P64)
        print(f'{name}: {len(P64)} vertices in float64; smallest angle between two normals {math.degrees(ang):.2f} deg (amplification 1/sin = {1 / math.sin(ang):.2f})')
        # vertices from float32 normals: position error against the float64 vertices
        worst = 0.0
        for a, b in itertools.combinations(range(9), 2):
            v32 = Vector(N32[a]).cross(Vector(N32[b])); v32.normalize()
            v64 = np.cross(N64[a], N64[b]); v64 /= np.linalg.norm(v64)
            worst = max(worst, min(np.linalg.norm(np.array(v32[:]) - v64), np.linalg.norm(np.array(v32[:]) + v64)))
        print(f'   largest vertex error using float32 normals and float32 cross products: {worst:.2e}')
        for tol in (1e-9, 1e-8, 1e-7, 1e-6, 1e-5):
            pts = []
            for a, b in itertools.combinations(range(9), 2):
                v = Vector(N32[a]).cross(Vector(N32[b])); v.normalize()
                for p in (np.array(v[:]), -np.array(v[:])):
                    if not any(np.linalg.norm(p - q) < tol for q in pts):
                        pts.append(p)
            print(f'   merge tolerance {tol:.0e}: {len(pts)} distinct vertices from float32 normals')


if __name__ == '__main__':
    {'distance': distance, 'normal': normal, 'interp': interp, 'mesh': mesh, 'arrangement': arrangement}[sys.argv[1]]()
