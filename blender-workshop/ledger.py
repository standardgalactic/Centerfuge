"""Chapter 29: a ledger of runs with provenance, and review of claims that is sensitive to defeat. Plain Python.

A run is a record of parameters, results and the environment that produced them. A claim states a scope (which runs bear on it)
and a test (what a bearing run must satisfy). Review lists the runs that defeat it and, where one categorical parameter separates
the runs that hold from the runs that do not, the narrower claim that survives.
"""
import hashlib, json, platform, sys


def file_sha(*paths):
    h = hashlib.sha1()
    for p in paths:
        with open(p, 'rb') as f: h.update(f.read())
    return h.hexdigest()[:12]


def provenance(scripts, extra=None):
    import numpy
    d = dict(script_sha=file_sha(*scripts), scripts=list(scripts), python=platform.python_version(), numpy=numpy.__version__)
    try:
        import bpy; d['bpy'] = bpy.app.version_string
    except Exception:
        d['bpy'] = None
    d.update(extra or {}); return d


def record(ledger, kind, params, result, prov):
    r = dict(id=len(ledger), kind=kind, params=params, result=result, prov=prov); ledger.append(r); return r


def save(ledger, path):
    with open(path, 'w') as f:
        for r in ledger: f.write(json.dumps(r, sort_keys=True) + '\n')


def load(path):
    with open(path) as f: return [json.loads(l) for l in f]


class Claim:
    def __init__(self, cid, text, kind, scope, holds, categorical=()):
        self.cid, self.text, self.kind, self.scope, self.holds, self.categorical = cid, text, kind, scope, holds, categorical

    def bearing(self, ledger):
        return [r for r in ledger if r['kind'] == self.kind and self.scope(r['params'])]

    def review(self, ledger, scope_name=''):
        runs = self.bearing(ledger); bad = [r for r in runs if not self.holds(r)]
        out = dict(claim=self.cid, runs=len(runs), defeaters=[r['id'] for r in bad], status='stands' if runs and not bad else ('defeated as stated' if bad else 'no evidence'))
        if bad:
            for p in self.categorical:
                vals = sorted({str(r['params'][p]) for r in runs})
                good = [v for v in vals if all(self.holds(r) for r in runs if str(r['params'][p]) == v)]
                if good: out.setdefault('survives_for', {})[p] = good
        return out


def reproduce(record_, fn, tol=0.0):
    """Re-execute a recorded run through fn(params) and compare each numeric result; returns the largest relative difference."""
    new = fn(record_['params']); worst = 0.0
    for k, v in record_['result'].items():
        if isinstance(v, (int, float)):
            worst = max(worst, abs(new[k] - v) / max(abs(v), 1e-300))
    return worst
