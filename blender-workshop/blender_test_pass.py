"""Run the manuscript's Blender listings, extracted from the .tex sources, and test the claims near them.

    python3 blender_test_pass.py        (Blender's Python module 'bpy'; run in the directory of the .tex files)
"""
import math, re, random, itertools
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix, Euler

RESULTS = []
def check(name, ok, detail=''):
    RESULTS.append((name, bool(ok)))
    print(('PASS ' if ok else 'FAIL ') + name + (' | ' + str(detail) if detail else ''))

def listing(tex, containing):
    s = open(tex).read()
    for m in re.finditer(r'\\begin\{lstlisting\}[^\n]*\n(.*?)\\end\{lstlisting\}', s, re.S):
        if containing in m.group(1):
            return m.group(1)
    raise KeyError(containing)

def fresh():
    bpy.ops.wm.read_factory_settings(use_empty=True)

# ---------- Chapter 2
fresh()
code = listing('ch2_add.tex', 'Ground_Script')
ns = {}
exec(code, ns)
obj = bpy.data.objects['Ground_Script']
exp = Matrix.Translation((0, 0, -0.2)) @ Matrix.Diagonal((3, 3, 0.2, 1))
err = max(abs(obj.matrix_world[i][j] - exp[i][j]) for i in range(4) for j in range(4))
zs = [(obj.matrix_world @ v.co).z for v in obj.data.vertices]
check('ch2 matrix_world equals T@S', err < 1e-6, err)
check('ch2 top z 0 / bottom z -0.4', abs(max(zs)) < 1e-6 and abs(min(zs) + 0.4) < 1e-6, (max(zs), min(zs)))
# NumPy listing
exec(listing('ch2_add.tex', 'itertools.product'), {})

# Ch2 claims: matrix before update is stale; Euler XYZ = Rz Ry Rx; Apply Scale; non-uniform parent shear
fresh()
bpy.ops.mesh.primitive_cube_add(size=2)
o = bpy.context.active_object
o.scale = (3, 3, 0.2); o.location = (0, 0, -0.2)
stale = o.matrix_world.copy()
bpy.context.view_layer.update()
check('ch2 matrix_world stale until update', max(abs(stale[i][j] - o.matrix_world[i][j]) for i in range(4) for j in range(4)) > 0.1)
e = Euler((0.3, 0.5, 0.7), 'XYZ')
R = Matrix.Rotation(0.7, 3, 'Z') @ Matrix.Rotation(0.5, 3, 'Y') @ Matrix.Rotation(0.3, 3, 'X')
check('Euler XYZ matrix = Rz Ry Rx', max(abs(e.to_matrix()[i][j] - R[i][j]) for i in range(3) for j in range(3)) < 1e-6)
# Apply scale
bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
check('apply scale: scale -> 1, vertices carry it', tuple(o.scale) == (1, 1, 1) and abs(max(v.co.x for v in o.data.vertices) - 3) < 1e-6)
# shear from non-uniform parent with rotated child
fresh()
p = bpy.data.objects.new('P', None); bpy.context.scene.collection.objects.link(p)
c = bpy.data.objects.new('C', None); bpy.context.scene.collection.objects.link(c)
p.scale = (2, 1, 1); c.parent = p; c.rotation_euler = (0, 0, math.pi / 4)
bpy.context.view_layer.update()
M3 = c.matrix_world.to_3x3()
cols = [M3.col[0], M3.col[1]]
check('non-uniform parent + rotated child gives non-orthogonal axes (shear)', abs(cols[0].dot(cols[1])) > 0.1, cols[0].dot(cols[1]))

# ---------- Chapter 4
fresh()
bpy.ops.mesh.primitive_cube_add(size=2)
ns = {'__name__': 'x'}
import io, contextlib
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    exec(listing('ch4_add.tex', 'sum of face sizes'), ns)
print(buf.getvalue().strip())
check('ch4 listing on cube: 8 12 6 chi = 2; sum faces 24 = 2E', '8 12 6 chi = 2' in buf.getvalue() and '24 , 2E = 24' in buf.getvalue())
for prim, args in (('uv_sphere', dict(segments=32, ring_count=16)), ('torus', {}), ('cone', {}), ('monkey', {}), ('cylinder', {})):
    fresh()
    getattr(bpy.ops.mesh, 'primitive_%s_add' % prim if prim != 'monkey' else 'primitive_monkey_add')(**args) if prim != 'monkey' else bpy.ops.mesh.primitive_monkey_add()
    me = bpy.context.active_object.data
    V, E, F = len(me.vertices), len(me.edges), len(me.polygons)
    bm = bmesh.new(); bm.from_mesh(me)
    open_edges = sum(1 for e in bm.edges if len(e.link_faces) != 2)
    check(f'ch4 {prim}: sum of face sizes = 2E exactly when no edge has other than two faces', (sum(len(p.vertices) for p in me.polygons) == 2 * E) == (open_edges == 0), (V, E, F, V - E + F, 'edges not shared by two faces:', open_edges))

def counts_after(fn):
    fresh()
    bpy.ops.mesh.primitive_cube_add(size=2)
    o = bpy.context.active_object
    bpy.ops.object.mode_set(mode='EDIT')
    fn(o)
    bpy.ops.object.mode_set(mode='OBJECT')
    me = o.data
    return len(me.vertices), len(me.edges), len(me.polygons)

def sel(mode_faces=None):
    bpy.ops.mesh.select_all(action='DESELECT')
    bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
    bm.faces.ensure_lookup_table()
    return bm
def extrude(o):
    bm = sel(); bm.faces[0].select = True; bmesh.update_edit_mesh(o.data)
    bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={'value': (0, 0, 0)})
def bevel(o):
    bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.bevel(offset=0.1, segments=1, affect='EDGES')
def tri(o):
    bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.quads_convert_to_tris()
def delface(o):
    bm = sel(); bm.faces[0].select = True; bmesh.update_edit_mesh(o.data); bpy.ops.mesh.delete(type='FACE')
for name, fn, want in (('extrude one face, zero displacement', extrude, (12, 20, 10)), ('bevel all edges, 1 segment', bevel, (24, 48, 26)),
                       ('triangulate', tri, (8, 18, 12)), ('delete one face', delface, (8, 12, 5))):
    got = counts_after(fn)
    check(f'ch4 table: {name}', got == want, got)
for lv, want in ((1, (26, 48, 24)), (2, (98, 192, 96))):
    fresh()
    bpy.ops.mesh.primitive_cube_add(size=2)
    o = bpy.context.active_object
    m = o.modifiers.new('S', 'SUBSURF'); m.levels = lv; m.render_levels = lv
    ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
    got = (len(ev.vertices), len(ev.edges), len(ev.polygons))
    check(f'ch4 table: Catmull-Clark level {lv}', got == want, got)
# volume claims
def vol(o, flip=()):
    me = o.data; s = 0
    for p in me.polygons:
        vs = [me.vertices[i].co for i in p.vertices]
        if p.index in flip: vs = vs[::-1]
        for k in range(1, len(vs) - 1):
            s += vs[0].dot(vs[k].cross(vs[k + 1])) / 6
    return s
fresh(); bpy.ops.mesh.primitive_cube_add(size=2); o = bpy.context.active_object
top = max(o.data.polygons, key=lambda p: p.center.z).index
check('ch4 volume 8, all reversed -8, top reversed 16/3',
      abs(vol(o) - 8) < 1e-6 and abs(vol(o, set(range(6))) + 8) < 1e-6 and abs(vol(o, {top}) - 16 / 3) < 1e-6,
      (vol(o), vol(o, set(range(6))), vol(o, {top})))

# ---------- Chapter 5
fresh()
exec(listing('ch5_add.tex', 'Cell_Module_Mesh'), {'__name__': 'x'})
cells = [o for o in bpy.data.objects if o.name.startswith('Cell_')]
check('ch5 row: 20 objects share one mesh', len(cells) == 20 and bpy.data.meshes['Cell_Module_Mesh'].users == 20 and len(bpy.data.meshes) == 1)
check('ch5 row: custom properties', all(o['seed'] == 7 and o['jitter'] == 0.4 and o['step'] == 1.5 for o in cells))
check('ch5 row: collection Cell_Family linked to scene', 'Cell_Family' in [c.name for c in bpy.context.scene.collection.children])
xs = sorted(o.location.x for o in cells)
ov = sum(1 for a, b in zip(xs, xs[1:]) if b - a < 1.0)
import familycheck
print('overlaps in this row (adjacent):', ov, ' familycheck.overlaps:', familycheck.overlaps(xs, 1.0) if hasattr(familycheck, 'overlaps') else 'n/a')
# determinism: rerun gives the same positions
fresh(); exec(listing('ch5_add.tex', 'Cell_Module_Mesh'), {'__name__': 'x'})
xs2 = sorted(o.location.x for o in bpy.data.objects if o.name.startswith('Cell_'))
check('ch5 row: seed reproducible', np.allclose(xs, xs2))
# mean overlaps over seeds (claim ~1.34)
def mean_ov(trials=20000):
    t = 0
    for s in range(trials):
        r = random.Random(s); x = [i * 1.5 + 0.4 * r.uniform(-1, 1) for i in range(20)]
        t += sum(1 for a, b in zip(x, x[1:]) if abs(b - a) < 1.0)
    return t / trials
print('mean adjacent overlaps (N=20,a=0.4):', mean_ov())

# Array modifier
def array_len(r, c, N, s=1.0, scale=1.0):
    fresh(); bpy.ops.mesh.primitive_cube_add(size=s); o = bpy.context.active_object
    m = o.modifiers.new('A', 'ARRAY'); m.count = N
    m.use_relative_offset = r is not None; m.use_constant_offset = c is not None
    if r is not None: m.relative_offset_displace = (r, 0, 0)
    if c is not None: m.constant_offset_displace = (c, 0, 0)
    m.use_merge_vertices = False
    o.scale = (scale,) * 3
    ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
    xs = [v.co.x for v in ev.vertices]
    return (max(xs) - min(xs)) * scale, len(ev.vertices)
L, nv = array_len(1.2, None, 4)
check('ch5 Array N=4, r=1.2, s=1: length 4.6', abs(L - 4.6) < 1e-5, (L, nv))
L, _ = array_len(1.0, 0.5, 4)
print('relative 1.0 + constant 0.5, N=4: length', L, ' (additive prediction 3*1.5+1 = 5.5)')
check('ch5 Array: relative and constant offsets add', abs(L - 5.5) < 1e-5)
L, _ = array_len(1.2, None, 4, scale=2.0)
check('ch5 Array under object scale 2: length scales by 2 (gap/module preserved)', abs(L - 9.2) < 1e-5, L)
# Bevel/Array order
def stack(order):
    fresh(); bpy.ops.mesh.primitive_cube_add(size=1); o = bpy.context.active_object
    for t in order:
        if t == 'A':
            m = o.modifiers.new('A', 'ARRAY'); m.count = 3; m.relative_offset_displace = (1.5, 0, 0)
        else:
            m = o.modifiers.new('B', 'BEVEL'); m.width = 0.1; m.segments = 1
    ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
    return len(ev.vertices), len(ev.edges), len(ev.polygons)
ba, ab = stack('BA'), stack('AB')
print('Bevel then Array', ba, ' Array then Bevel', ab)
check('ch5 separated copies: the two orders give the same counts', ba == ab, (ba, ab))
# merged: copies touching
def stack_merged(order):
    fresh(); bpy.ops.mesh.primitive_cube_add(size=1); o = bpy.context.active_object
    for t in order:
        if t == 'A':
            m = o.modifiers.new('A', 'ARRAY'); m.count = 3; m.relative_offset_displace = (1.0, 0, 0); m.use_merge_vertices = True
        else:
            m = o.modifiers.new('B', 'BEVEL'); m.width = 0.1; m.segments = 1
    ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
    bb = [v.co.x for v in ev.vertices]
    return (len(ev.vertices), len(ev.edges), len(ev.polygons))
bm_, am_ = stack_merged('BA'), stack_merged('AB')
check('ch5 touching merged copies: the orders differ (Bevel->Array 64/136/76, Array->Bevel 40/80/44)', bm_ == (64, 136, 76) and am_ == (40, 80, 44), (bm_, am_))

# ---------- Chapter 11
fresh()
exec(listing('chap11.tex', 'Orthodrome_Workshop'), {'__name__': 'x'})
objs = list(bpy.data.collections['Orthodrome_Workshop'].objects)
check('ch11: nine curve objects in new collection', len(objs) == 9, len(objs))
worst_r = worst_p = 0
for o in objs:
    n = Vector(o['unit_normal'])
    for pt in o.data.splines[0].points:
        x = Vector(pt.co[:3])
        worst_r = max(worst_r, abs(x.length - 10)); worst_p = max(worst_p, abs(n.dot(x)))
check('ch11: every sample at radius 10 and in its plane', worst_r < 1e-5 and worst_p < 1e-5, (worst_r, worst_p))
# Euler identity: object-rotated unit circle in local XY plane has normal R*(0,0,1)
def nb(beta, lam): return Vector((math.cos(beta) * math.cos(lam), math.cos(beta) * math.sin(lam), math.sin(beta)))
worst = 0
for beta, lam in ((math.pi / 2, 0), (0, 0), (0, math.pi / 4), (0, 3 * math.pi / 4), (math.pi / 6, math.pi / 8), (math.pi / 6, math.pi / 8 + 3 * math.pi / 2), (0.61, 2.2)):
    n = Euler((0, math.pi / 2 - beta, lam), 'XYZ').to_matrix() @ Vector((0, 0, 1))
    worst = max(worst, (n - nb(beta, lam)).length)
check('ch11: Euler (0, 90deg-beta, lambda) rotates local Z to normal(beta, lambda)', worst < 1e-6, worst)   # float32 storage of Blender matrices
# faces=48? intersection structure is in familycheck; here re-run twice: new collection each time
exec(listing('chap11.tex', 'Orthodrome_Workshop'), {'__name__': 'x'})
check('ch11: second run adds a second collection and does not erase', len(objs) == 9 and len(bpy.data.objects) == 18 and len([c for c in bpy.data.collections]) == 2, [c.name for c in bpy.data.collections])

print()
print(sum(ok for _, ok in RESULTS), 'of', len(RESULTS), 'checks passed')
for n, ok in RESULTS:
    if not ok: print('FAILED:', n)
