"""Chapter 21 measurements.   python3 ch21_probe.py build|validate|winding|precision|attributes"""
import sys, time, statistics
import numpy as np
import bpy, bmesh
from mesh_tools import mesh_from_arrays, report


def grid(n):
    xs, ys = np.meshgrid(np.arange(n + 1), np.arange(n + 1)); v = np.c_[xs.ravel(), ys.ravel(), np.zeros((n + 1) ** 2)]
    i, j = np.meshgrid(np.arange(n), np.arange(n), indexing='ij'); i = i.ravel(); j = j.ravel()
    idx = lambda a, b: a * (n + 1) + b
    f = np.c_[idx(i, j), idx(i, j + 1), idx(i + 1, j + 1), idx(i + 1, j)]
    return v, f


def build():
    for n in (50, 100, 200, 400):
        v, f = grid(n); vl = v.tolist(); fl = [tuple(map(int, r)) for r in f]
        t = {}
        for label in ('from_pydata', 'foreach_set'):
            ts = []
            for r in range(3):
                bpy.ops.wm.read_factory_settings(use_empty=True)
                t0 = time.perf_counter()
                if label == 'from_pydata':
                    me = bpy.data.meshes.new('m'); me.from_pydata(vl, [], fl); me.update()
                else:
                    me = mesh_from_arrays('m', v, f)
                ts.append(time.perf_counter() - t0)
            t[label] = statistics.median(ts)
        rep = report(me)
        print(f'{n*n:7d} quads: from_pydata {t["from_pydata"]*1000:8.1f} ms   foreach_set {t["foreach_set"]*1000:7.1f} ms   ratio {t["from_pydata"]/t["foreach_set"]:.1f}   (V {rep["V"]}, E {rep["E"]}, F {rep["F"]}, area {rep["area"]})')
    # identical result check
    v, f = grid(30)
    a = bpy.data.meshes.new('a'); a.from_pydata(v.tolist(), [], [tuple(map(int, r)) for r in f]); a.update()
    b = mesh_from_arrays('b', v, f)
    ca = np.empty(len(a.vertices) * 3, np.float32); a.vertices.foreach_get('co', ca)
    cb = np.empty(len(b.vertices) * 3, np.float32); b.vertices.foreach_get('co', cb)
    ea = sorted(tuple(sorted(e.vertices)) for e in a.edges); eb = sorted(tuple(sorted(e.vertices)) for e in b.edges)
    print('same coordinates:', bool((ca == cb).all()), '; same edges:', ea == eb, '; same polygon vertex lists:', all(tuple(p.vertices) == tuple(q.vertices) for p, q in zip(a.polygons, b.polygons)))


def validate():
    cases = {
        'clean quad': ([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], [(0, 1, 2, 3)]),
        'repeated vertex in a face': ([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], [(0, 1, 1, 2)]),
        'duplicate face': ([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], [(0, 1, 2, 3), (0, 1, 2, 3)]),
        'loose vertex': ([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (5, 5, 5)], [(0, 1, 2, 3)]),
        'zero-area triangle': ([(0, 0, 0), (1, 0, 0), (2, 0, 0)], [(0, 1, 2)]),
        'coincident vertices': ([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (1, 0, 0), (1, 1, 0), (2, 0, 0), (2, 1, 0)], [(0, 1, 2, 3), (4, 6, 7, 5)]),
    }
    for name, (v, f) in cases.items():
        me = bpy.data.meshes.new('t')
        try:
            me.from_pydata(v, [], f)
        except Exception as e:
            print(f'{name}: from_pydata raised {type(e).__name__}'); continue
        before = (len(me.vertices), len(me.edges), len(me.polygons))
        changed = me.validate(verbose=False)
        after = (len(me.vertices), len(me.edges), len(me.polygons))
        print(f'{name}: V,E,F {before} -> validate() returned {changed} -> {after}')


def winding():
    def cube(inward):
        h = 0.5; v = [(x, y, z) for x in (-h, h) for y in (-h, h) for z in (-h, h)]
        f = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
        if inward: f = [tuple(reversed(q)) for q in f]
        me = bpy.data.meshes.new('c'); me.from_pydata(v, [], f); me.update(); return me
    for label, inward in (('outward as written', False), ('reversed', True)):
        me = cube(inward)
        bm = bmesh.new(); bm.from_mesh(me)
        v0 = bm.calc_volume(signed=True)
        n0 = [p.normal.dot(p.center) for p in me.polygons]
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        v1 = bm.calc_volume(signed=True)
        print(f'{label}: signed volume {v0:+.3f}; normal.centre sign of faces {"+" if min(n0) > 0 else "-" if max(n0) < 0 else "mixed"}; after recalc_face_normals {v1:+.3f}')
        bm.free()


def precision():
    print('offset X, requested x = X + 0.001, stored x, error, float32 spacing at X')
    for X in (1e2, 1e3, 1e4, 1e5, 1e6, 1e7):
        me = bpy.data.meshes.new('p'); me.from_pydata([(X + 0.001, 0, 0)], [], [])
        back = me.vertices[0].co.x
        print(f'{X:9.0e} {X+0.001:16.4f} {back:16.4f}  err {back-(X+0.001):+.4f}  spacing {float(np.spacing(np.float32(X))):.4g}')
    print('object location (also float32?):')
    o = bpy.data.objects.new('o', None); o.location = (1e7 + 0.3, 0, 0); print(' ', o.location.x)


def attributes():
    me = bpy.data.meshes.new('a'); v = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]; me.from_pydata(v, [], [(0, 1, 2, 3)]); me.update()
    at = me.attributes.new('height', 'FLOAT', 'POINT')
    print('attribute length', len(at.data), '(vertices', len(me.vertices), ')')
    at.data.foreach_set('value', [0.0, 1.0, 2.0, 3.0])
    out = np.empty(4, np.float32); at.data.foreach_get('value', out); print('read back', out.tolist())
    try:
        at.data.foreach_set('value', [1.0, 2.0])
        print('short array accepted; values now', [d.value for d in at.data])
    except Exception as e:
        print('short array raised', type(e).__name__, str(e)[:80])
    again = me.attributes.new('height', 'FLOAT', 'POINT')
    print('second attribute with the same name: name is', again.name, '; count of attributes named like it:', sum(1 for a in me.attributes if a.name.startswith('height')))
    f = me.attributes.new('sides', 'INT', 'FACE'); print('FACE attribute length', len(f.data))
    c = me.attributes.new('tint', 'FLOAT_COLOR', 'POINT'); print('color attribute value length', len(c.data[0].color))
    print('domains', sorted((a.name, a.domain, a.data_type) for a in me.attributes if not a.name.startswith('.')))


if __name__ == '__main__':
    {'build': build, 'validate': validate, 'winding': winding, 'precision': precision, 'attributes': attributes}[sys.argv[1]]()
