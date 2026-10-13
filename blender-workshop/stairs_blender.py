"""Chapter 22: the Blender side of the staircase constructor. Needs Blender's Python module.

    python3 stairs_blender.py check|session
"""
import json, sys
import bpy, bmesh
from stairs import validate, geometry, geometry_hash, spec_json, volume_formula, VERSION, GEN, KEYS


def generated(scene):
    c = bpy.data.collections.get(GEN)
    if c is None:
        c = bpy.data.collections.new(GEN); scene.collection.children.link(c)
    return c


def mesh_hash(me):
    """Hash of what is actually stored in the mesh (float32), so drift in the stored data is detectable."""
    verts = [tuple(v.co) for v in me.vertices]
    faces = [tuple(p.vertices) for p in me.polygons]
    return geometry_hash(verts, faces)


def build_mesh(spec, name='Stair'):
    verts, faces = geometry(spec)
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    return me


def make_stair(spec, scene=None, location=(0, 0, 0)):
    scene = scene or bpy.context.scene
    s = validate(spec); me = build_mesh(s)
    o = bpy.data.objects.new('Stair', me); o.location = location
    generated(scene).objects.link(o)
    o['constructor'] = 'make_stair'; o['version'] = VERSION; o['spec'] = spec_json(s); o['geom_hash'] = mesh_hash(me)
    return o


def rebuild_check(o):
    """Rebuild from the stored specification alone and compare with the object's stored geometry."""
    spec = json.loads(o['spec'])
    fresh = build_mesh(spec, 'tmp')
    same_stored = mesh_hash(fresh) == o['geom_hash']
    same_now = mesh_hash(fresh) == mesh_hash(o.data)
    bpy.data.meshes.remove(fresh)
    return same_stored, same_now


def ensure(spec, scene=None, location=(0, 0, 0)):
    """Return the existing generated stair with this specification, or make one: calling twice makes one object."""
    scene = scene or bpy.context.scene; key = spec_json(spec)
    for o in generated(scene).objects:
        if o.get('constructor') == 'make_stair' and o.get('spec') == key:
            return o, False
    return make_stair(spec, scene, location), True


def update(o, new_spec):
    """Change an existing stair to a new specification, keeping the object, and retire the old mesh."""
    s = validate(new_spec); old = o.data; me = build_mesh(s)
    o.data = me; o['spec'] = spec_json(s); o['geom_hash'] = mesh_hash(me)
    if old.users == 0:
        bpy.data.meshes.remove(old)
    return o


def signed_volume(me):
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); v = bm.calc_volume(signed=True); bm.free(); return v


def check():
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    specs = [dict(n=1, rise=0.2, run=0.3, width=1.0), dict(n=5, rise=0.18, run=0.28, width=1.2), dict(n=12, rise=0.175, run=0.25, width=0.9), dict(n=40, rise=0.15, run=0.3, width=2.0), dict(n=200, rise=0.1, run=0.2, width=1.0)]
    print('mesh volume against width*rise*run*n(n+1)/2:')
    for sp in specs:
        o = make_stair(sp); v = signed_volume(o.data); f = volume_formula(sp)
        bb = [c for c in o.bound_box]; top = max(c[2] for c in bb); depth = max(c[1] for c in bb)
        print(f'  n={sp["n"]:3d}: mesh {v:.6f}  formula {f:.6f}  rel diff {(v-f)/f:+.1e}  height {top:.4f} (n*rise {sp["n"]*sp["rise"]:.4f})  depth {depth:.4f} (n*run {sp["n"]*sp["run"]:.4f})  V,F {len(o.data.vertices)},{len(o.data.polygons)}')
    print('rebuild from the stored specification alone:', [rebuild_check(o) for o in generated(sc).objects])
    bad = [dict(n=0, rise=.2, run=.3, width=1), dict(n=2.5, rise=.2, run=.3, width=1), dict(n=3, rise=-.2, run=.3, width=1), dict(n=3, rise=.2, run=.3), dict(n=3, rise=.2, run=.3, width=1, colour='red'), dict(n=True, rise=.2, run=.3, width=1), dict(n=3, rise=float('nan'), run=.3, width=1)]
    for b in bad:
        try:
            validate(b); print('  accepted:', b)
        except ValueError as e:
            print('  rejected:', e)
    n0 = len(generated(sc).objects)
    a, made1 = ensure(specs[1]); b, made2 = ensure(specs[1]); c, made3 = ensure(specs[2])
    print('ensure twice with the same specification:', made1, made2, 'same object', a is b, '; objects', n0, '->', len(generated(sc).objects), '(the first spec already existed; the third did too)')
    d, made4 = ensure(dict(n=7, rise=0.18, run=0.28, width=1.2)); e, made5 = ensure(dict(width=1.2, run=0.28, rise=0.18, n=7))
    print('new spec, then the same spec with keys in another order:', made4, made5, d is e)
    meshes_before = len(bpy.data.meshes); name = d.name
    update(d, dict(n=9, rise=0.18, run=0.28, width=1.2))
    print('update in place: same object', d.name == name, '; meshes', meshes_before, '->', len(bpy.data.meshes), '; stored spec', d['spec'], '; rebuild check', rebuild_check(d))
    print('hash equal when the same specification is built in two different objects:', mesh_hash(make_stair(specs[1]).data) == mesh_hash(make_stair(specs[1]).data))


def session():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    o = make_stair(dict(n=12, rise=0.175, run=0.25, width=0.9))
    print(o['geom_hash'])


if __name__ == '__main__':
    {'check': check, 'session': session}[sys.argv[1]]()
