"""Chapter 29: runs of the shell experiments recorded with provenance, and the review of three claims.

    python3 ledger_blender.py initial|defeat|reproduce|tamper
Writes ledger.jsonl in the working directory (initial) and reads it afterwards.
"""
import copy, json, math, os, sys
import numpy as np
import bpy, bmesh
import ledger as L
from synestia import volume_analytic
from synestia_blender import shell_mesh, mesh_volume
import degrade as D

SCRIPTS = ['synestia.py', 'synestia_blender.py', 'degrade.py', 'ledger_blender.py']
PATH = 'ledger.jsonl'


def vol_err(f, nmaj, nmin):
    me = shell_mesh('s', f, nmaj, nmin); v = mesh_volume(me); bpy.data.meshes.remove(me); return v / volume_analytic(f) - 1


def run_doubling(p):
    """p: f, policy, n. Error at n and at the doubled resolution; ratio = error(n) / error(2n)."""
    n, f = p['n'], p['f']
    a0 = (n, n); a1 = {'both': (2 * n, 2 * n), 'nmin_only': (n, 2 * n), 'nmaj_only': (2 * n, n)}[p['policy']]
    e0, e1 = vol_err(f, *a0), vol_err(f, *a1)
    return dict(err0=e0, err1=e1, ratio=e0 / e1)


def run_hole(p):
    me = shell_mesh('s', p['f'], p['nmaj'], p['nmin']); h = D.hole_ray(me) if False else None
    D.F = p['f']; D.A, D.B = D.semi_axes(p['f']); D.HOLE = D.R0 - D.A
    h = D.hole_ray(me); bpy.data.meshes.remove(me); return dict(hole_err=h)


def run_collapse(p):
    """Volume error of a uniform grid and of collapse decimation, at about the same triangle count."""
    D.F = p['f']; D.A, D.B = D.semi_axes(p['f']); D.HOLE = D.R0 - D.A
    ntri = p['ntri']; nmaj = int(round(math.sqrt(ntri / 3))); nmin = int(round(1.5 * nmaj)); nmin += nmin % 2
    me = shell_mesh('u', p['f'], nmaj, nmin); bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.to_mesh(me); bm.free()
    eg = mesh_volume(me) / volume_analytic(p['f']) - 1; tg = len(me.polygons)
    sc = bpy.data.scenes.new('S'); fine = shell_mesh('fine', p['f'], 128, 128)
    o = bpy.data.objects.new('f', fine); sc.collection.objects.link(o)
    bm = bmesh.new(); bm.from_mesh(fine); bmesh.ops.triangulate(bm, faces=bm.faces[:]); bm.to_mesh(fine); bm.free()
    md = o.modifiers.new('d', 'DECIMATE'); md.decimate_type = 'COLLAPSE'; md.ratio = ntri / len(fine.polygons)
    sc.view_layers[0].update(); ev = o.evaluated_get(sc.view_layers[0].depsgraph); m2 = ev.to_mesh()
    ec = mesh_volume(m2) / volume_analytic(p['f']) - 1; tc = len(m2.polygons); ev.to_mesh_clear()
    bpy.data.objects.remove(o); bpy.data.scenes.remove(sc)
    return dict(grid_err=eg, grid_tris=tg, collapse_err=ec, collapse_tris=tc)


FUNCS = {'doubling': run_doubling, 'hole': run_hole, 'collapse': run_collapse}

CLAIMS = [
    L.Claim('C1', 'The error of the mesh volume falls by a factor between 3.5 and 4.5 when the resolution is doubled.', 'doubling',
            lambda p: True, lambda r: 3.5 <= r['result']['ratio'] <= 4.5, categorical=('policy',)),
    L.Claim('C2', 'A shell of at least 12 major segments keeps the hole radius within 5 percent, whatever the number of minor segments.', 'hole',
            lambda p: p['nmaj'] >= 12, lambda r: abs(r['result']['hole_err']) < 0.05, categorical=('nmin_parity',)),
    L.Claim('C3', 'At equal triangle count, collapse decimation of a fine mesh has a smaller volume error than a uniform grid.', 'collapse',
            lambda p: True, lambda r: abs(r['result']['collapse_err']) < abs(r['result']['grid_err']), categorical=('f',)),
]


def add(ledger, kind, params):
    return L.record(ledger, kind, params, FUNCS[kind](params), L.provenance(SCRIPTS))


def initial():
    led = []
    for n in (8, 16, 32, 64):
        add(led, 'doubling', dict(f=0.05, policy='both', n=n))
    for nmaj in (12, 16, 32, 64):
        for nmin in (6, 8, 16, 32):
            add(led, 'hole', dict(f=0.05, nmaj=nmaj, nmin=nmin, nmin_parity='even'))
    for ntri in (144, 384, 768, 1536, 3072):
        add(led, 'collapse', dict(f=0.05, ntri=ntri))
    L.save(led, PATH); show(led)


def show(led):
    for c in CLAIMS:
        r = c.review(led); print(f'{c.cid}: {r["status"]:20s} runs {r["runs"]:3d}  defeaters {r["defeaters"]}  {r.get("survives_for", "")}')


def defeat():
    led = L.load(PATH); n0 = len(led)
    print('before:'); show(led)
    # runs chosen to look for defeat: other policies, odd minor counts, other contour levels
    for pol in ('nmin_only', 'nmaj_only'):
        for n in (8, 16, 32, 64): add(led, 'doubling', dict(f=0.05, policy=pol, n=n))
    for n in (128, 256, 512): add(led, 'doubling', dict(f=0.05, policy='both', n=n))
    for f in (0.5, 0.2, 0.02):
        for n in (8, 16, 32): add(led, 'doubling', dict(f=f, policy='both', n=n))
    for nmin in (7, 9, 17, 33):
        for nmaj in (16, 64): add(led, 'hole', dict(f=0.05, nmaj=nmaj, nmin=nmin, nmin_parity='odd'))
    for f in (0.5, 0.2, 0.02):
        for ntri in (144, 768, 3072): add(led, 'collapse', dict(f=f, ntri=ntri))
    L.save(led, PATH); print(f'after {len(led) - n0} further runs:'); show(led)
    for c in CLAIMS:
        r = c.review(led)
        for i in r['defeaters'][:6]:
            x = led[i]; print(f'   {c.cid} defeated by run {i}: {x["params"]} -> {x["result"]}')
        if len(r['defeaters']) > 6: print(f'   ... and {len(r["defeaters"]) - 6} more')


def reproduce():
    led = L.load(PATH); rng = np.random.default_rng(0)
    pick = rng.choice(len(led), 12, replace=False)
    worst = max(L.reproduce(led[i], FUNCS[led[i]['kind']]) for i in pick)
    print(f're-executed {len(pick)} of {len(led)} recorded runs: largest relative difference {worst:.2e}')
    print('script hash recorded in the ledger:', {r['prov']['script_sha'] for r in led}, ' hash of the scripts now:', L.file_sha(*SCRIPTS))


def tamper():
    led = L.load(PATH); i = next(r['id'] for r in led if r['kind'] == 'doubling' and r['params']['n'] == 64 and r['params']['policy'] == 'both' and r['params']['f'] == 0.05)
    bad = copy.deepcopy(led); bad[i]['result']['ratio'] = 2.0; bad[i]['result']['err1'] = bad[i]['result']['err0'] / 2.0
    print('narrowed claim from the original ledger:', CLAIMS[0].review(led).get('survives_for'), '| from the altered ledger:', CLAIMS[0].review(bad).get('survives_for', 'none'))
    print('altered record, re-executed: relative difference', f'{L.reproduce(bad[i], FUNCS["doubling"]):.3f}', '| original record:', f'{L.reproduce(led[i], FUNCS["doubling"]):.2e}')


if __name__ == '__main__':
    globals()[sys.argv[-1]]()
