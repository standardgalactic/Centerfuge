"""Chapter 30: the final project in Blender, and its acceptance suite.

    python3 capstone_blender.py hash|suite
"""
import copy, hashlib, json, math, os, random, subprocess, sys, tempfile
import numpy as np
import bpy
import capstone as C
import habitat
import glb_read
import review as R
from stairs import geometry, spec_json, volume_formula
from stairs_blender import build_mesh, mesh_hash
from review import canon
import world
import ledger as L

RING = 8.0


def loc(i, n):
    a = 2 * math.pi * i / n; return (RING * math.cos(a), RING * math.sin(a), 0.0)


def build_scene(rec, order=None, names=None):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    coll, _ = habitat.build(rec['habitat']['entrance'])
    fam = bpy.data.collections.new('Generated'); bpy.context.scene.collection.children.link(fam)
    ms = rec['family']['members']; n = rec['family']['count']; cache = {}
    for i in (order if order is not None else range(len(ms))):
        m = ms[i]; key = spec_json(m['spec'])
        if key not in cache: cache[key] = build_mesh(m['spec'])
        nm = names[i] if names else f'Stair {i:04d}'
        o = bpy.data.objects.new(nm, cache[key]); o.location = loc(m['index'], n); fam.objects.link(o)
        o['uuid'] = m['uuid']; o['index'] = m['index']; o['spec'] = key; o['geom_hash'] = mesh_hash(cache[key])
    bpy.context.view_layer.update()
    return coll, fam


def habitat_hash(coll):
    h = hashlib.sha1()
    for o in sorted(coll.objects, key=lambda o: o.name):
        h.update(o.name.encode()); h.update(np.round(np.array(o.matrix_world), 4).tobytes())
        h.update(np.round(np.array([tuple(v.co) for v in o.data.vertices]), 4).tobytes())
    return h.hexdigest()[:12]


def family_state(fam):
    return {o['uuid']: (o['geom_hash'], o['spec'], tuple(round(c, 4) for c in o.location)) for o in fam.objects}


def composition(rec, coll, fam):
    h = hashlib.sha1(habitat_hash(coll).encode())
    for k, v in sorted(family_state(fam).items()): h.update(repr((k, v)).encode())
    h.update(C.process_hash(rec).encode()); return h.hexdigest()[:12]


def hash_cmd():
    rec = C.make_record(); coll, fam = build_scene(rec); print(composition(rec, coll, fam))


def suite():
    rec = C.make_record(); led = []; PR = L.provenance(['capstone.py', 'capstone_blender.py', 'stairs.py', 'habitat.py', 'world.py'])
    coll, fam = build_scene(rec); base = composition(rec, coll, fam); hb = habitat_hash(coll); fb = family_state(fam)
    print(f'baseline: habitat objects {len(coll.objects)}, family objects {len(fam.objects)}, distinct meshes {len({o.data.name for o in fam.objects})}, '
          f'visits {len(rec["visits"])}, composition hash {base}')
    # A1 rebuild
    again = composition(rec, *build_scene(rec))
    sub = subprocess.run([sys.executable, 'capstone_blender.py', 'hash'], capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__))).stdout.strip().split('\n')[-1]
    print(f'A1 rebuild: same process {again == base}, fresh process {sub == base}')
    L.record(led, 'rebuild', dict(where='same process'), dict(same=int(again == base)), PR); L.record(led, 'rebuild', dict(where='fresh process'), dict(same=int(sub == base)), PR)
    # A2 revisit after shuffled creation order and random names
    rng = random.Random(3); order = list(range(len(rec['family']['members']))); rng.shuffle(order)
    names = [f'obj_{rng.getrandbits(32):08x}' for _ in order]
    coll2, fam2 = build_scene(rec, order, names)
    ok = 0
    for v in rec['visits']:
        c = [o for o in fam2.objects if o['uuid'] == v['uuid']]
        if len(c) == 1 and c[0]['geom_hash'] == fb[v['uuid']][0] and C.observe(rec, v) == {k: v[k] for k in ('reading', 'state_hash')}: ok += 1
    L.record(led, 'rebuild', dict(where='shuffled order, random names'), dict(same=int(composition(rec, coll2, fam2) == base)), PR)
    print(f'A2 revisit after shuffled order and random names: {ok} of {len(rec["visits"])} visits return to the same site with the same reading and state;',
          f'composition hash unchanged: {composition(rec, coll2, fam2) == base}')
    # A3 edits
    print('A3 what each edit changes (counts):')
    print(f'{"edit":13s} habitat_changed  family_changed  ids_missing  process_changed  visit_mismatches  composition_changed')
    for k in ('entrance', 'family seed', 'one stair', 'extra event'):
        r = C.edit(rec, k); c3, f3 = build_scene(r); fs = family_state(f3)
        changed = sum(1 for u, v in fb.items() if u in fs and fs[u] != v); missing = sum(1 for u in fb if u not in fs)
        ch = dict(habitat=int(habitat_hash(c3) != hb), family=int(changed + missing > 0), process=int(C.process_hash(r) != C.process_hash(rec)), visits=int(len(C.replay_visits(r)) > 0))
        L.record(led, 'edit', dict(edit=k, own={'entrance': 'habitat', 'family seed': 'family', 'one stair': 'family', 'extra event': 'process'}[k]), ch, PR)
        print(f'{k:13s} {str(habitat_hash(c3) != hb):>15s} {changed:15d} {missing:12d} {str(C.process_hash(r) != C.process_hash(rec)):>16s} {len(C.replay_visits(r)):17d} {str(composition(r, c3, f3) != base):>20s}')
    # A4 export and independent read
    path = os.path.join(tempfile.mkdtemp(), 'habitat.glb')
    bpy.ops.wm.read_factory_settings(use_empty=True); coll, fam = build_scene(rec)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB')
    js, bn = glb_read.read(path)
    nodes = [n for n in js['nodes'] if 'mesh' in n]
    vols = {}
    for n in nodes:
        if not n['name'].startswith('Stair'): continue
        prim = js['meshes'][n['mesh']]['primitives'][0]
        P = glb_read.accessor(js, bn, prim['attributes']['POSITION']).astype(float); I = glb_read.accessor(js, bn, prim['indices']).ravel()
        T = I.reshape(-1, 3); a, b, c = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]
        vols[int(n['name'].split()[1][:4])] = float(np.einsum('ij,ij->i', a, np.cross(b, c)).sum() / 6)
    errs = [abs(vols[i] / volume_formula(m['spec']) - 1) for i, m in enumerate(rec['family']['members'])]
    print(f'A4 export: {len(js["nodes"])} nodes, {len(nodes)} with meshes, {len(js["meshes"])} glTF meshes (distinct specs {len({spec_json(m["spec"]) for m in rec["family"]["members"]})} + habitat parts {len(coll.objects)}); '
          f'stair volumes recovered by the independent reader: {len(vols)}, largest relative error against the formula {max(errs):.2e}')
    # A5 review stages on every member as stored in Blender
    coll, fam = build_scene(rec); fails = 0
    for o in fam.objects:
        V = [tuple(v.co) for v in o.data.vertices]; F = [tuple(p.vertices) for p in o.data.polygons]; spec = json.loads(o['spec'])
        st, _ = R.run(V, F, {'spec': spec}, R.STAGES[:6], spec)
        if st or canon(V, F) != canon(*geometry(spec)): fails += 1
    print(f'A5 review stages (format to provenance, plus canonical) on {len(fam.objects)} members: {fails} fail')
    # A6 injected defects
    o = sorted(fam.objects, key=lambda o: o['index'])[7]; me = o.data
    key = o['spec']; shared = sum(1 for x in fam.objects if x.data == me)
    me.vertices[5].co.z += 1e-3; me.update()
    fs = family_state(fam); hashchg = sum(1 for u in fs if mesh_hash(next(x for x in fam.objects if x['uuid'] == u).data) != fb[u][0])
    V = [tuple(v.co) for v in me.vertices]; F = [tuple(p.vertices) for p in me.polygons]
    print(f'A6a one vertex of one shared mesh moved by 0.001: shared by {shared} objects; objects whose stored hash now differs from the record {hashchg}; review stage that flags it: {R.run(V, F, {"spec": json.loads(key)}, R.STAGES[:6], json.loads(key))[0]}')
    coll, fam = build_scene(rec); a, b = sorted(fam.objects, key=lambda o: o['index'])[:2]; b['uuid'] = a['uuid']
    ids = [x['uuid'] for x in fam.objects]; print(f'A6b one identifier copied to a second object: unique identifiers {len(set(ids))} of {len(ids)} objects; a visit to that identifier resolves to {sum(1 for x in ids if x == a["uuid"])} objects')
    r1 = copy.deepcopy(rec); e = C.edge_of(5)
    r1['process']['log'] += [[220, 'cut', r1['process']['log'][0][2]]]
    r2 = copy.deepcopy(r1); r2['process']['log'][-2], r2['process']['log'][-1] = r2['process']['log'][-1], r2['process']['log'][-2]
    print(f'A6c two events at the same step, order swapped in the record: process hashes {C.process_hash(r1)} and {C.process_hash(r2)}')
    claims = [L.Claim('K1', 'Rebuilding from the record reproduces the composition hash.', 'rebuild', lambda p: True, lambda r: r['result']['same'] == 1, categorical=('where',)),
              L.Claim('K2', 'An edit to one component of the record changes that component and no other.', 'edit', lambda p: True,
                      lambda r: all(v == (1 if k == r['params']['own'] else 0) for k, v in r['result'].items()), categorical=('edit',))]
    for c in claims:
        v = c.review(led); print(f'A7 {c.cid}: {v["status"]}, bearing runs {v["runs"]}, defeating runs {v["defeaters"]}, narrower claim: {v.get("survives_for", "none needed")}')
    for r in led:
        if r['kind'] == 'edit': print('   ', r['params']['edit'], r['result'])


if __name__ == '__main__':
    globals()[{'hash': 'hash_cmd'}.get(sys.argv[-1], sys.argv[-1])]()
