"""Chapter 30: the project record. Plain data and the stateful process; no Blender.

A project is a record from which the scene, the process state and the visit readings can all be regenerated:
  habitat  : which entrance variant of the Chapter 3 habitat
  family   : seed, count, and for each member a specification and an identifier assigned once
  process  : the adaptive network of Chapter 24 with its seed, exponent, event log and end step
  visits   : (step, identifier) pairs with the reading and state hash observed at the visit
A site's reading is the conductance of the network edge attached to it, edge = (7 * index) mod (number of edges).
"""
import copy, hashlib, json, math, random
import numpy as np
import world
from stairs import validate

MU = 1.5
CHOICES = {'n': list(range(3, 15)), 'rise': [0.15, 0.175, 0.2], 'run': [0.25, 0.28, 0.3], 'width': [0.9, 1.2, 1.5]}


def sample_specs(count, seed):
    rng = random.Random(seed)
    return [validate({k: rng.choice(v) for k, v in CHOICES.items()}) for _ in range(count)]


def edge_of(index):
    return (7 * index) % len(world.E)


def make_record(entrance='centre', fam_seed=5, count=24, proc_seed=0, until=300, nvisits=10, visit_seed=11):
    s0 = world.run(world.initial(proc_seed), MU, 300, [])
    path = sorted(world.path_edges(s0)); e1, e2 = path[10], path[20]
    log = [(100, 'cut', e1), (160, 'cut', e2), (220, 'restore', e1)]
    specs = sample_specs(count, fam_seed)
    members = [dict(index=i, uuid=hashlib.sha1(f'{fam_seed}:{i}'.encode()).hexdigest()[:12], spec=sp) for i, sp in enumerate(specs)]
    rec = dict(habitat=dict(entrance=entrance), family=dict(seed=fam_seed, count=count, members=members),
               process=dict(seed=proc_seed, mu=MU, log=[list(e) for e in log], until=until), visits=[])
    rng = random.Random(visit_seed)
    steps = sorted(rng.sample(range(10, until, 10), nvisits))
    rec['visits'] = [dict(step=s, uuid=rng.choice(members)['uuid']) for s in steps]
    for v in rec['visits']:
        v.update(observe(rec, v))
    return rec


_cache = {}


def states(proc, steps):
    """State at each requested step, from one run of the process (events applied at the start of their step)."""
    key = (proc['seed'], proc['mu'], json.dumps(proc['log']), tuple(steps))
    if key in _cache: return _cache[key]
    out = {}; st = world.initial(proc['seed']); log = [tuple(e) for e in proc['log']]
    for s in sorted(set(steps)):
        st = world.run(st, proc['mu'], s, log); out[s] = st
    _cache[key] = out; return out


def observe(rec, visit):
    proc = rec['process']; idx = {m['uuid']: m['index'] for m in rec['family']['members']}
    st = states(proc, [visit['step']])[visit['step']]
    return dict(reading=float(st['D'][edge_of(idx[visit['uuid']])]), state_hash=world.state_hash(st))


def process_hash(rec):
    st = states(rec['process'], [rec['process']['until']])[rec['process']['until']]
    return world.state_hash(st)


def replay_visits(rec):
    """Recompute every visit's reading and state hash from the record's process alone, and compare with what was logged."""
    bad = []
    for k, v in enumerate(rec['visits']):
        try:
            o = observe(rec, v)
        except KeyError:
            bad.append((k, 'identifier absent from the family')); continue
        if o['state_hash'] != v['state_hash'] or o['reading'] != v['reading']: bad.append((k, 'reading or state differs'))
    return bad


def edit(rec, kind):
    r = copy.deepcopy(rec)
    if kind == 'entrance': r['habitat']['entrance'] = 'east'
    elif kind == 'family seed':
        seed = rec['family']['seed'] + 1; r['family']['seed'] = seed
        r['family']['members'] = [dict(index=i, uuid=hashlib.sha1(f'{seed}:{i}'.encode()).hexdigest()[:12], spec=sp) for i, sp in enumerate(sample_specs(rec['family']['count'], seed))]
    elif kind == 'one stair':
        m = r['family']['members'][3]; m['spec'] = validate(dict(m['spec'], n=m['spec']['n'] % 12 + 3))
    elif kind == 'extra event': r['process']['log'].append([60, 'cut', world.E.index(world.E[edge_of(5)]) if False else edge_of(5)])
    else: raise ValueError(kind)
    return r


if __name__ == '__main__':
    rec = make_record()
    print('visits:', len(rec['visits']), ' process hash at the end:', process_hash(rec), ' replay mismatches:', replay_visits(rec))
    for k in ('entrance', 'family seed', 'one stair', 'extra event'):
        r = edit(rec, k); print(f'{k:12s} process hash {process_hash(r)}  visit mismatches {len(replay_visits(r))}')
