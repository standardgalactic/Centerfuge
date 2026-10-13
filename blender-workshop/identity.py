"""Chapter 26: how a recorded visit finds its site again after the scene is changed.

    python3 identity.py table
A bookmark records six things about a site; each resolver uses one of them. 'truth' is a hidden property that follows the
site through every change, and is used only to score the resolvers, never by them.
"""
import hashlib, json, random, sys
import numpy as np
import bpy
from stairs import validate, spec_json, VERSION
from stairs_blender import build_mesh, mesh_hash
from batch import sample_specs, place

N = 200


def ledger(seed=5):
    """Members as the family's record holds them, each with a persistent id assigned once."""
    specs = sample_specs(N, seed)
    return [dict(truth=i, uuid=hashlib.sha1(f'{seed}:{i}'.encode()).hexdigest()[:12], spec=validate(s)) for i, s in enumerate(specs)]


def build(members, keep_uuid=True, order=None):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    coll = bpy.data.collections.new('Generated'); bpy.context.scene.collection.children.link(coll)
    cache = {}
    idxs = list(range(len(members))) if order is None else order
    for i in idxs:
        m = members[i]; key = spec_json(m['spec'])
        if key not in cache:
            cache[key] = build_mesh(m['spec'])
        o = bpy.data.objects.new(f'Stair {i:04d}', cache[key]); o.location = place(i); coll.objects.link(o)
        o['index'] = i; o['spec'] = key; o['geom_hash'] = mesh_hash(cache[key]); o['truth'] = m['truth']
        o['uuid'] = m['uuid'] if keep_uuid else hashlib.sha1(f'fresh:{i}:{m["truth"]}'.encode()).hexdigest()[:12]
    return coll


def bookmarks(coll):
    return [dict(truth=o['truth'], name=o.name, order=list(coll.objects).index(o), index=o['index'], location=tuple(o.location), content=(o['spec'], o['geom_hash']), uuid=o['uuid']) for o in coll.objects]


def resolve(scheme, bm, coll):
    objs = list(coll.objects)
    if scheme == 'name':
        c = [o for o in objs if o.name == bm['name']]
    elif scheme == 'order':
        c = [objs[bm['order']]] if bm['order'] < len(objs) else []
    elif scheme == 'index':
        c = [o for o in objs if o['index'] == bm['index']]
    elif scheme == 'location':
        c = [o for o in objs if np.allclose(tuple(o.location), bm['location'], atol=1e-3)]
    elif scheme == 'content':
        c = [o for o in objs if (o['spec'], o['geom_hash']) == bm['content']]
    elif scheme == 'uuid':
        c = [o for o in objs if o['uuid'] == bm['uuid']]
    if not c:
        return 'missing'
    if len(c) > 1:
        return 'ambiguous'
    return 'correct' if c[0]['truth'] == bm['truth'] else 'wrong'


SCHEMES = ['name', 'order', 'index', 'location', 'content', 'uuid']


def perturbations():
    rng = random.Random(1)

    def p0(members): return build(members)
    def p1(members):
        coll = build(members)
        for o in coll.objects: o.name = o.name[::-1]
        return coll
    def p2(members):
        new = members[:3] + [dict(truth=-1, uuid='newnewnewnew', spec=validate(dict(n=5, rise=0.2, run=0.3, width=1.2)))] + members[3:]
        return build(new)
    def p3(members):
        coll = build(members)
        for o in coll.objects:
            if rng.random() < 0.3: o.location.x += 0.5
        return coll
    def p4(members):
        coll = build(members)
        for o in coll.objects:
            if rng.random() < 0.3:
                sp = json.loads(o['spec']); sp['n'] = min(sp['n'] + 1, 200); me = build_mesh(sp)
                o.data = me; o['spec'] = spec_json(sp); o['geom_hash'] = mesh_hash(me)
        return coll
    def p5a(members): return build(members, keep_uuid=False)
    def p6(members):
        coll = build(members)
        for o in list(coll.objects):
            if rng.random() < 0.1:
                d = o.copy(); coll.objects.link(d); d.location.y -= 2.0
        return coll
    def p7(members):
        order = list(range(len(members))); rng.shuffle(order); return build(members, order=order)
    return [('none', p0), ('rename every object', p1), ('insert a member at position 3', p2), ('move 30% of objects', p3),
            ('change a parameter on 30%', p4), ('regenerate; ids not recorded', p5a), ('duplicate 10%', p6), ('regenerate in another order', p7)]


def table():
    members = ledger()
    base = build(members); bms = bookmarks(base)
    print('perturbation | ' + ' | '.join(SCHEMES) + '   (percent of 200 bookmarks resolving correctly; wrong / ambiguous / missing in brackets when nonzero)')
    for name, fn in perturbations():
        coll = fn(members)
        cells = []
        for s in SCHEMES:
            res = [resolve(s, b, coll) for b in bms]
            c = {k: res.count(k) for k in ('correct', 'wrong', 'ambiguous', 'missing')}
            extra = ','.join(f'{k[0]}{v}' for k, v in c.items() if k != 'correct' and v)
            cells.append(f'{100*c["correct"]/len(res):5.1f}' + (f'[{extra}]' if extra else ''))
        print(f'{name:34s}| ' + ' | '.join(cells))


if __name__ == '__main__':
    {'table': table}[sys.argv[1]]()
