"""Chapter 25 measurements.   python3 export_probe.py axes|units|instances|extras|material|attrs|roundtrip|hull"""
import os, sys, json
import numpy as np
import bpy, bmesh
import glb_read

TMP = '/tmp/claude-0/-home-claude/927989f5-bbd5-524c-a738-cde2187a9709/scratchpad/exp'
os.makedirs(TMP, exist_ok=True)


def fresh():
    bpy.ops.wm.read_factory_settings(use_empty=True); return bpy.context.scene


def tetra(name='T', loc=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    me.from_pydata([(1, 2, 3), (4, 0, 0), (0, 5, 0), (0, 0, 6)], [], [(0, 2, 1), (0, 1, 3), (1, 2, 3), (2, 0, 3)]); me.update()
    o = bpy.data.objects.new(name, me); o.location = loc; bpy.context.scene.collection.objects.link(o); return o


def export_glb(path, **kw):
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', **kw)


def positions(path):
    js, bn = glb_read.read(path)
    prim = js['meshes'][0]['primitives'][0]
    return js, glb_read.accessor(js, bn, prim['attributes']['POSITION'])


def axes():
    fresh(); o = tetra()
    src = np.array([tuple(v.co) for v in o.data.vertices])
    export_glb(f'{TMP}/a.glb')
    js, p = positions(f'{TMP}/a.glb')
    print('Blender vertices:', src.tolist())
    uq = lambda a: sorted({tuple(np.round(r, 6) + 0.0) for r in a})
    print('glb vertex count', len(p), 'distinct positions', len(uq(p)), '(Blender vertices', len(src), ')')
    print('distinct glb positions:', uq(p))
    print('equal as a set to (x, z, -y) of the Blender vertices:', uq(p) == uq(np.c_[src[:, 0], src[:, 2], -src[:, 1]]))
    export_glb(f'{TMP}/b.glb', export_yup=False)
    js, p2 = positions(f'{TMP}/b.glb'); print('export_yup=False: distinct positions equal the source set:', uq(p2) == uq(src))
    # which way is up for a face normal? the face normals
    fresh(); o = tetra(loc=(10, 20, 30))
    export_glb(f'{TMP}/c.glb'); js, bn = glb_read.read(f'{TMP}/c.glb')
    print('node translation with object at (10,20,30):', js['nodes'][0].get('translation'))
    bpy.ops.wm.obj_export(filepath=f'{TMP}/a.obj')
    vs = [l.split()[1:] for l in open(f'{TMP}/a.obj') if l.startswith('v ')]
    print('obj vertices (default axes), object at origin shifted? first four of', len(vs), ':', vs[:4])


def units():
    sc = fresh(); o = tetra()
    o.data.vertices[1].co.x = 1000.0
    for sl in (1.0, 0.001, 0.01):
        sc.unit_settings.system = 'METRIC'; sc.unit_settings.scale_length = sl
        export_glb(f'{TMP}/u.glb'); js, p = positions(f'{TMP}/u.glb')
        print(f'scale_length {sl}: exported x of the vertex at Blender x=1000: {p[:, 0].max():g}')
    sc.unit_settings.scale_length = 1.0
    export_glb(f'{TMP}/u2.glb', export_apply=True); js, p = positions(f'{TMP}/u2.glb'); print('object scale 2 applied?')
    o.scale = (2, 2, 2); export_glb(f'{TMP}/u3.glb'); js, bn = glb_read.read(f'{TMP}/u3.glb'); print('node scale for object scale 2:', js['nodes'][0].get('scale'), '; vertex x max', positions(f'{TMP}/u3.glb')[1][:, 0].max())


def instances():
    from batch import sample_specs, build_family
    for share in (True, False):
        fresh()
        members, errs = build_family(sample_specs(200, 5))
        if not share:
            for o in bpy.data.collections['Generated'].objects:
                o.data = o.data.copy()
        path = f'{TMP}/i_{share}.glb'; export_glb(path)
        js, bn = glb_read.read(path)
        print(f'shared meshes in Blender: {len(set(o.data.name for o in bpy.data.objects))}' if share else 'unique copy per object', '-> glb nodes', len(js['nodes']), 'meshes', len(js['meshes']), 'accessors', len(js['accessors']), 'file bytes', os.path.getsize(path))


def extras():
    from batch import sample_specs, build_family
    fresh(); build_family(sample_specs(5, 5))
    for ex in (False, True):
        export_glb(f'{TMP}/e.glb', export_extras=ex); js, bn = glb_read.read(f'{TMP}/e.glb')
        print('export_extras', ex, '-> node 0 extras:', js['nodes'][0].get('extras'))


def material():
    from transport_blender import flow_material
    fresh(); o = tetra(); m = flow_material(); o.data.materials.append(m); o['flow'] = 0.4
    export_glb(f'{TMP}/m.glb'); js, bn = glb_read.read(f'{TMP}/m.glb')
    print('materials in glb:', json.dumps(js.get('materials')))
    m2 = bpy.data.materials.new('P'); m2.use_nodes = True
    bsdf = m2.node_tree.nodes['Principled BSDF']; bsdf.inputs['Base Color'].default_value = (0.8, 0.1, 0.1, 1); bsdf.inputs['Roughness'].default_value = 0.35; bsdf.inputs['Metallic'].default_value = 0.0
    o.data.materials.clear(); o.data.materials.append(m2)
    export_glb(f'{TMP}/m2.glb'); js, bn = glb_read.read(f'{TMP}/m2.glb'); print('principled:', json.dumps(js.get('materials')))


def attrs():
    fresh(); o = tetra()
    a = o.data.attributes.new('sides', 'INT', 'FACE'); a.data.foreach_set('value', [3, 3, 3, 3])
    b = o.data.attributes.new('height', 'FLOAT', 'POINT'); b.data.foreach_set('value', [0.1, 0.2, 0.3, 0.4])
    d = o.data.attributes.new('_height', 'FLOAT', 'POINT'); d.data.foreach_set('value', [0.1, 0.2, 0.3, 0.4])
    e = o.data.attributes.new('_sides', 'INT', 'FACE'); e.data.foreach_set('value', [3, 3, 3, 3])
    c = o.data.attributes.new('tint', 'FLOAT_COLOR', 'POINT'); c.data.foreach_set('color', [1, 0, 0, 1] * 4)
    export_glb(f'{TMP}/t.glb', export_attributes=True); js, bn = glb_read.read(f'{TMP}/t.glb')
    print('primitive attributes written:', sorted(js['meshes'][0]['primitives'][0]['attributes'].keys()))


def roundtrip():
    from stairs_blender import make_stair, mesh_hash, signed_volume
    from stairs import volume_formula
    sp = dict(n=12, rise=0.175, run=0.25, width=0.9)
    fresh(); o = make_stair(sp); h0 = o['geom_hash']; v0 = signed_volume(o.data)
    export_glb(f'{TMP}/r.glb')
    fresh(); bpy.ops.import_scene.gltf(filepath=f'{TMP}/r.glb')
    ob = [x for x in bpy.data.objects if x.type == 'MESH'][0]
    print('imported vertices', len(ob.data.vertices), 'faces', len(ob.data.polygons), '(original 52 vertices, 28 faces)')
    co = np.array([tuple(ob.matrix_world @ v.co) for v in ob.data.vertices])
    orig = np.array([(0.0, 0, 0)])
    from stairs import geometry
    verts, faces = geometry(sp); src = np.array(verts)
    # compare as point sets after sorting
    uq = lambda a: np.array(sorted({tuple(np.round(r, 5) + 0.0) for r in a}))
    A, B = uq(co), uq(src)
    print('distinct imported positions', len(A), 'distinct original', len(B), '; equal to 1e-5:', A.shape == B.shape and bool(np.allclose(A, B, atol=1e-5)))
    tri = sum(np.dot(co[p.vertices[0]], np.cross(co[p.vertices[1]], co[p.vertices[2]])) for p in ob.data.polygons) / 6.0
    print('volume from the imported triangles, orientation as imported: %.6f (formula %.6f, original mesh %.6f)' % (tri, volume_formula(sp), v0))
    print('volume by bmesh after recalculating normals on the unmerged imported mesh: %.6f' % signed_volume(ob.data))
    bm = bmesh.new(); bm.from_mesh(ob.data); n0 = len(bm.verts); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    print('after merging coincident vertices (%d -> %d) and recalculating: %.6f' % (n0, len(bm.verts), bm.calc_volume(signed=True))); bm.free()
    print('triangulated on export? original face sizes', sorted({len(f) for f in faces}), '-> imported', sorted({len(p.vertices) for p in ob.data.polygons}))


def hull():
    from scipy.spatial import ConvexHull
    from stairs import geometry, volume_formula
    print('convex-hull collision proxy of a staircase: n, stair vertices, hull vertices, hull faces (triangles), hull volume / stair volume')
    for n in (3, 6, 12, 40):
        sp = dict(n=n, rise=0.175, run=0.25, width=0.9); verts, faces = geometry(sp)
        h = ConvexHull(np.array(verts))
        print(f'  {n:3d}: {len(verts)} vertices, hull vertices {len(h.vertices)}, hull triangles {len(h.simplices)}, hull volume {h.volume:.4f}, stair volume {volume_formula(sp):.4f}, ratio {h.volume / volume_formula(sp):.3f}')


if __name__ == '__main__':
    {'axes': axes, 'units': units, 'instances': instances, 'extras': extras, 'material': material, 'attrs': attrs, 'roundtrip': roundtrip, 'hull': hull}[sys.argv[1]]()
