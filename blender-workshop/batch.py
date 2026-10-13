"""Chapter 23: generate a family of staircases from a seeded sampler, with a manifest from which the family can be rebuilt.

    python3 batch.py generate N SEED manifest.json
    python3 batch.py verify manifest.json
    python3 batch.py inject            (failure handling test)
    python3 batch.py scale
Needs Blender's Python module.
"""
import hashlib, json, random, sys, time
import bpy
from stairs import validate, spec_json, VERSION, GEN
from stairs_blender import generated, build_mesh, mesh_hash

CHOICES = {'n': list(range(3, 15)), 'rise': [0.15, 0.175, 0.2], 'run': [0.25, 0.28, 0.3], 'width': [0.9, 1.2, 1.5]}


def sample_specs(count, seed):
    rng = random.Random(seed)
    return [{k: rng.choice(v) for k, v in CHOICES.items()} for _ in range(count)]


def place(i, per_row=25, pitch=4.0):
    return ((i % per_row) * pitch, (i // per_row) * pitch, 0.0)


def build_family(specs, scene=None, on_error='stop'):
    """Validate every specification first. on_error='stop': build nothing if any is invalid. 'skip': build the valid ones."""
    scene = scene or bpy.context.scene
    cleaned, errors = [], []
    for i, sp in enumerate(specs):
        try:
            cleaned.append((i, validate(sp)))
        except ValueError as e:
            errors.append((i, str(e)))
    if errors and on_error == 'stop':
        return [], errors
    coll = generated(scene); cache = {}; members = []
    for i, sp in cleaned:
        key = spec_json(sp)
        if key not in cache:
            cache[key] = build_mesh(sp, 'Stair')
        me = cache[key]
        o = bpy.data.objects.new(f'Stair {i:04d}', me); o.location = place(i); coll.objects.link(o)
        o['constructor'] = 'make_stair'; o['version'] = VERSION; o['spec'] = key; o['index'] = i; o['geom_hash'] = mesh_hash(me)
        members.append(dict(index=i, spec=json.loads(key), geom_hash=o['geom_hash'], location=list(place(i))))
    return members, errors


def manifest(members, seed, count):
    body = dict(constructor='make_stair', version=VERSION, seed=seed, count=count, members=members)
    text = json.dumps(body, sort_keys=True)
    body['manifest_hash'] = hashlib.sha1(text.encode()).hexdigest()[:12]
    return body


def verify(man):
    """Rebuild every member from the manifest alone and compare geometry hashes; returns (agree, total)."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    members, errs = build_family([m['spec'] for m in man['members']])
    ok = sum(1 for a, b in zip(members, man['members']) if a['geom_hash'] == b['geom_hash'] and a['spec'] == b['spec'])
    body = {k: v for k, v in man.items() if k != 'manifest_hash'}
    h = hashlib.sha1(json.dumps(body, sort_keys=True).encode()).hexdigest()[:12]
    return ok, len(man['members']), h == man['manifest_hash'], errs


def main():
    cmd = sys.argv[1]
    if cmd == 'generate':
        N, seed, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        bpy.ops.wm.read_factory_settings(use_empty=True)
        t = time.perf_counter()
        members, errs = build_family(sample_specs(N, seed))
        dt = time.perf_counter() - t
        man = manifest(members, seed, N)
        json.dump(man, open(out, 'w'), sort_keys=True)
        print(f'N={N} seed={seed}: objects {len(generated(bpy.context.scene).objects)}, distinct meshes {len({m["geom_hash"] for m in members})}, bpy meshes {len(bpy.data.meshes)}, build {dt*1000:.0f} ms, manifest hash {man["manifest_hash"]}, manifest bytes {len(json.dumps(man))}')
    elif cmd == 'verify':
        man = json.load(open(sys.argv[2]))
        t = time.perf_counter(); r = verify(man); dt = time.perf_counter() - t
        print(f'rebuilt from manifest in a fresh process: {r[0]} of {r[1]} members agree, manifest hash intact: {r[2]}, errors {len(r[3])}, {dt*1000:.0f} ms')
    elif cmd == 'inject':
        specs = sample_specs(50, 3)
        specs[7] = dict(specs[7], n=0); specs[20] = dict(specs[20], rise=-1.0); specs[41] = {k: v for k, v in specs[41].items() if k != 'width'}
        for mode in ('stop', 'skip'):
            bpy.ops.wm.read_factory_settings(use_empty=True)
            members, errs = build_family(specs, on_error=mode)
            print(f'on_error={mode}: objects built {len(members)}, errors reported {[(i, e) for i, e in errs]}, collection objects {len(bpy.data.collections[GEN].objects) if GEN in bpy.data.collections else 0}')
        print('indices of built members under skip keep their position in the batch:', [m['index'] for m in members][:9])
    elif cmd == 'scale':
        for N in (100, 1000, 5000):
            ts = []
            for r in range(3):
                bpy.ops.wm.read_factory_settings(use_empty=True)
                specs = sample_specs(N, 1)
                t = time.perf_counter(); members, _ = build_family(specs); ts.append(time.perf_counter() - t)
            ts.sort()
            print(f'N={N}: median {ts[1]*1000:.0f} ms ({ts[1]/N*1e6:.0f} us per member), range {ts[0]*1000:.0f} to {ts[2]*1000:.0f} ms, distinct specs {len({spec_json(m["spec"]) for m in members})}, meshes {len(bpy.data.meshes)}, objects {len(bpy.data.objects)}')


if __name__ == '__main__':
    main()
