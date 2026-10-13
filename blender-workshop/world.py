"""Chapter 24: a stateful process kept apart from its scene. State and events are plain data; rendering is a function of state.

    python3 world.py replay|history|restart|drift32
The process is the adaptive network of Chapter 19 (16 x 16 grid, one source, one sink) with two kinds of event:
('cut', edge) forces that edge's conductance to the floor from that step on; ('restore', edge) lets it adapt again.
"""
import hashlib, sys
import numpy as np
from transport import grid, solve

N = 16
E = grid(N)
SRC, SNK = 0, N * N - 1
FLOOR = 1e-6
DT = 0.3


def initial(seed):
    D = 1.0 + 0.05 * np.random.default_rng(seed).standard_normal(len(E))
    return dict(D=np.clip(D, 0.5, None), blocked=np.zeros(len(E), bool), t=0)


def apply(state, ev):
    kind, e = ev
    b = state['blocked'].copy()
    if kind == 'cut':
        b[e] = True
    elif kind == 'restore':
        b[e] = False
    else:
        raise ValueError(kind)
    D = state['D'].copy(); D[b] = FLOOR
    return dict(D=D, blocked=b, t=state['t'])


def step(state, mu):
    p, Q = solve(N, E, state['D'], SRC, SNK)
    a = np.abs(Q) ** mu
    D = state['D'] + DT * (a / (1 + a) - state['D'])
    D[state['blocked']] = FLOOR
    return dict(D=D, blocked=state['blocked'], t=state['t'] + 1)


def run(state, mu, until, log):
    """Advance to step `until`, applying events from log (a list of (step, kind, edge)) at the start of their step."""
    pending = sorted(log, key=lambda x: x[0])
    while state['t'] < until:
        for (s, kind, e) in pending:
            if s == state['t']:
                state = apply(state, (kind, e))
        state = step(state, mu)
    return state


def state_hash(state):
    h = hashlib.sha1(state['D'].astype('<f8').tobytes()); h.update(state['blocked'].tobytes()); h.update(str(state['t']).encode())
    return h.hexdigest()[:12]


def path_edges(state, thr=0.01):
    return frozenset(np.nonzero(state['D'] > thr)[0].tolist())


if __name__ == '__main__':
    cmd = sys.argv[1]; mu = 1.5
    if cmd == 'replay':
        # find an edge on the settled path to cut
        s0 = run(initial(0), mu, 300, [])
        path = sorted(path_edges(s0)); e1, e2 = path[10], path[20]
        log = [(100, 'cut', e1), (160, 'cut', e2), (220, 'restore', e1)]
        h = state_hash(run(initial(0), mu, 400, log))
        print('final hash with log', h, '(edges cut', e1, e2, ')')
    elif cmd == 'history':
        s_none = run(initial(0), mu, 300, [])
        path = sorted(path_edges(s_none)); e1 = path[10]
        for label, log in (('no events', []), ('cut at 100, restore at 150', [(100, 'cut', e1), (150, 'restore', e1)])):
            for until in (300, 1200):
                s = run(initial(0), mu, until, log)
                same = path_edges(s) == path_edges(run(initial(0), mu, until, []))
                print(f'{label:28s} step {until:5d}: kept edges {len(path_edges(s))}, same edge set as the run with no events: {same}, max |D - D_none| {np.abs(s["D"] - run(initial(0), mu, until, [])["D"]).max():.3f}')
        # swap the order of two events at different steps
        e2 = path[20]
        a = run(initial(0), mu, 400, [(100, 'cut', e1), (160, 'cut', e2)])
        b = run(initial(0), mu, 400, [(100, 'cut', e2), (160, 'cut', e1)])
        print('two cuts in the other order: same final hash', state_hash(a) == state_hash(b), '; same final edge set', path_edges(a) == path_edges(b))
    elif cmd == 'restart':
        s0 = run(initial(0), mu, 300, []); path = sorted(path_edges(s0)); e1 = path[10]
        log = [(100, 'cut', e1), (220, 'restore', e1)]
        straight = run(initial(0), mu, 400, log)
        mid = run(initial(0), mu, 150, log)
        raw = {k: np.array(v).tobytes() for k, v in mid.items() if k != 't'}
        restored = dict(D=np.frombuffer(raw['D'], '<f8').copy(), blocked=np.frombuffer(raw['blocked'], bool).copy(), t=mid['t'])
        resumed = run(restored, mu, 400, log)
        print('straight-through', state_hash(straight), ' checkpoint at 150 then resume', state_hash(resumed))
        # a checkpoint that omits the blocked set
        broken = dict(D=restored['D'], blocked=np.zeros(len(E), bool), t=150)
        print('checkpoint without the blocked flags:', state_hash(run(broken, mu, 400, [(220, 'restore', e1)])))
    elif cmd == 'drift32':
        for mu_ in (0.8, 1.2, 1.5):
            a = initial(0); b = initial(0)
            for k in range(400):
                a = step(a, mu_)
                b = step(b, mu_); b['D'] = b['D'].astype(np.float32).astype(np.float64)
            print(f'mu={mu_}: max |D64 - D32roundtrip| after 400 steps {np.abs(a["D"] - b["D"]).max():.2e}; kept edges {len(path_edges(a))} vs {len(path_edges(b))}; same edge set {path_edges(a) == path_edges(b)}')
