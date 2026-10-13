"""Chapter 27: coupling Blender geometry to an external diffusion solver.

    python3 coupling_blender.py raster|stale|lag|replay|restart
"""
import hashlib, sys, time
import numpy as np
import bpy
from mathutils import Matrix
from coupling import Solver, SolverError, load, digest, validate
import solver as S

CUBE_V = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]


def cube_mesh():
    me = bpy.data.meshes.new('cube')
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me.from_pydata(CUBE_V, [], faces); return me


def box(scene, mesh, name, loc, half, rot_z=0.0):
    o = bpy.data.objects.new(name, mesh); scene.collection.objects.link(o)
    o.location = (loc[0], loc[1], 0); o.scale = (half[0], half[1], 1); o.rotation_euler = (0, 0, rot_z)
    return o


SC = None


def refresh():
    SC.view_layers[0].update()


def rasterise(objs, n, h):
    """Mask of an n by n grid of cell size h: 1 where a cell centre lies inside any object's local cube |x|,|y| <= 1."""
    g = (np.arange(n) + 0.5) * h
    X, Y = np.meshgrid(g, g, indexing='ij')
    P = np.stack([X.ravel(), Y.ravel(), np.zeros(n * n), np.ones(n * n)])
    mask = np.zeros(n * n, bool)
    for o in objs:
        M = np.array(o.matrix_world.inverted())
        L = M @ P
        mask |= (np.abs(L[0]) <= 1) & (np.abs(L[1]) <= 1)
    return mask.reshape(n, n).astype(np.uint8)


def scene():
    global SC
    SC = bpy.data.scenes.new('S'); return SC


def raster():
    sc = scene(); me = cube_mesh(); rng = np.random.default_rng(3)
    print('cells per unit   mean |rel error|   max |rel error|   (rotated box 20 x 8, 30 degrees, 40 random offsets)')
    for r in (1, 2, 4, 8, 16, 32):
        errs = []
        for _ in range(40):
            loc = (15 + rng.random(), 15 + rng.random())
            o = box(sc, me, 'b', loc, (10, 4), np.radians(30)); refresh()
            n = 32 * r; m = rasterise([o], n, 1.0 / r)
            errs.append(abs(m.sum() / r ** 2 - 160.0) / 160.0)
            bpy.data.objects.remove(o)
        print(f'{r:5d}            {np.mean(errs):.5f}           {np.max(errs):.5f}')


def stale():
    sc = scene(); me = cube_mesh()
    o = box(sc, me, 'b', (10, 10), (2, 2)); refresh()
    n, h = 32, 1.0; a = rasterise([o], n, h)
    o.location = (20, 10, 0)
    b = rasterise([o], n, h)           # no update since the move
    refresh(); c = rasterise([o], n, h)
    print('cells before move:', int(a.sum()), ' after move without update: same mask =', bool(np.array_equal(a, b)),
          ' after update: same as before =', bool(np.array_equal(a, c)), ' column of centre now', int(np.argmax(c.sum(1))))
    o.location = (5, 10, 0)
    bpy.context.view_layer.update()
    print('after update of the context view layer (a different scene), matrix_world x:', round(o.matrix_world[0][3], 3))
    refresh(); print('after update of the object\'s own scene, matrix_world x:', round(o.matrix_world[0][3], 3))


N = 48; LEVEL = 100.0; STEPS = 2400; RATE = 1 / 400.0; THR = 5.0
NEAR = (20, 24); FAR = (30, 24); FARTHR = 1.0


def world():
    sc = scene(); me = cube_mesh()
    wall = [box(sc, me, 'wall-low', (24, 10), (1, 10)), box(sc, me, 'wall-high', (24, 38), (1, 10))]
    door = box(sc, me, 'door', (24, 24), (1, 4)); refresh()
    fixed = np.zeros((N, N), bool); fixed[3:5, 22:26] = True
    return wall, door, fixed


def set_door(door, a):
    door.scale = (1, max(4 * (1 - a), 1e-6), 1); refresh()


def control(thr, a, u, delta):
    return min(1.0, a + RATE * delta) if u[NEAR] >= thr else a


def opened_at(rec, delta):
    return next(i for i, x in enumerate(rec['a']) if x > 0) * delta


class Log:
    def __init__(self): self.entries = []


def run(delta, thr=THR, solver=None, log=None, replay=None, crash_at=None, recover=None):
    """Staggered coupling with exchange interval delta (solver steps). Returns a record of the run."""
    wall, door, fixed = world(); own = solver is None and replay is None
    if replay is None and solver is None: solver = Solver(timeout=20)
    a = 0.0; u = np.zeros((N, N)); rec = {'far': [], 'a': [], 'exch': 0, 'times': np.zeros(3)}
    ck = None
    if solver is not None:
        solver.advance(np.zeros((N, N), np.uint8), fixed, LEVEL, 0, op='reset')
    first_far = None; prev = 0.0
    for k in range(STEPS // delta):
        t0 = time.perf_counter()
        a = control(thr, a, u, delta); set_door(door, a)
        mask = rasterise(wall + [door], N, 1.0); t1 = time.perf_counter()
        if replay is not None:
            e = replay[k]
            if e['mask'] != digest(mask): raise RuntimeError(f'replay diverged at exchange {k}')
            u = e['u']
        else:
            if crash_at is not None and k == crash_at:
                solver.stop(); solver = Solver(timeout=20)
                if recover == 'load': load(solver, mask, fixed, u)
                elif recover == 'reset': solver.advance(mask, fixed, LEVEL, 0, op='reset')
            hd, h, b = solver.advance(mask, fixed, LEVEL, delta)
            err = validate(hd, h, b, N, level=LEVEL, checks=('id', 'shape', 'finite', 'bounds'))
            if err: raise SolverError(err)
            u = np.frombuffer(b, dtype=np.float64).reshape(N, N).copy()
            if log is not None: log.append({'mask': digest(mask), 'u': u.copy()})
        t2 = time.perf_counter()
        rec['times'] += (t1 - t0, t2 - t1, 0); rec['exch'] += 1
        v = u[FAR]; step = (k + 1) * delta
        if first_far is None and v >= FARTHR:
            pv = prev; first_far = (step - delta) + delta * (FARTHR - pv) / (v - pv)
        prev = v; rec['a'].append(a)
    rec.update(a_final=a, far_final=float(u[FAR]), mass=S.total(u, mask), first_far=first_far, u=u,
               trace=digest(np.array(rec['a'])))
    if own and solver is not None: solver.stop()
    return rec


def lag():
    global RATE
    for rate in (1 / 400.0, 1 / 40.0):
        RATE = rate
        print(f'door opens at rate 1/{round(1/rate)} per step')
        print('delta  exchanges  door_from_step  t_far(steps)  far@2400   mass@2400   t_raster_ms  t_solver_ms  (per exchange)')
        for d in (1, 5, 25, 100, 400):
            r = run(d)
            print(f'{d:5d}  {r["exch"]:8d}  {opened_at(r, d):13d}  {r["first_far"]:11.1f}  {r["far_final"]:9.4f}  {r["mass"]:10.3f}  '
                  f'{1000*r["times"][0]/r["exch"]:9.3f}  {1000*r["times"][1]/r["exch"]:9.3f}')


def replay():
    lg = []; r = run(25, log=lg)
    import io
    buf = io.BytesIO(); np.savez_compressed(buf, *[e['u'] for e in lg])
    print('live run: exchanges', len(lg), ' trace', r['trace'], ' far', r['far_final'], ' log size (compressed fields, KB):', round(buf.tell() / 1024))
    r2 = run(25, replay=lg)
    print('replay without solver: trace', r2['trace'], ' far', r2['far_final'], ' identical trace:', r['trace'] == r2['trace'], ' identical field:', np.array_equal(r['u'], r2['u']))
    try:
        run(25, thr=6.0, replay=lg); print('changed threshold: replay did not notice')
    except RuntimeError as e:
        print('changed threshold 5 -> 6:', e)


def restart():
    ref = run(25)
    for rec in ('load', 'reset'):
        r = run(25, crash_at=40, recover=rec)
        print(f'solver killed at exchange 40, recovery={rec:5s}: final far {r["far_final"]:.6f} (uninterrupted {ref["far_final"]:.6f}), '
              f'field identical: {np.array_equal(r["u"], ref["u"])}, door trace identical: {r["trace"] == ref["trace"]}, mass {r["mass"]:.3f} vs {ref["mass"]:.3f}')


if __name__ == '__main__':
    globals()[sys.argv[-1]]()
