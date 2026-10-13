"""Checks for the Entropy's Edge case study (Chapter 6). Run: python3 edge_check.py"""
import contextlib
import copy
import io
import json
import random
import sys

from edge_port import COST, full, initial_state, projection, run, step

ORIGINAL_DIR = '/home/claude/standardgalactic/centerfuge/projects/entropy_edge'


def original_run(commands, seed):
    """Run the unmodified original module under a fixed global seed."""
    sys.path.insert(0, ORIGINAL_DIR)
    import entropy_edge as ee
    random.seed(seed)
    ee.state.update({'turn': 0, 'energy': 10, 'entropy': 0.0,
                     'tiles': {'(0,0)': {'scan': 'home'}}, 'buildings': []})
    with contextlib.redirect_stdout(io.StringIO()):
        for c in commands:
            p = c.split()
            {'end': lambda: ee.end_turn(), 'scan': lambda: ee.scan(),
             'build': lambda: ee.build(p[1])}[p[0]]()
    return json.loads(json.dumps(ee.state))


def random_commands(rng, n):
    pool = ['end', 'end', 'scan', 'build factory', 'build lab']
    return [rng.choice(pool) for _ in range(n)]


def as_dict(state):
    return {'turn': state['turn'], 'energy': state['energy'], 'entropy': state['entropy'],
            'tiles': state['tiles'], 'buildings': state['buildings']}


if __name__ == '__main__':
    gen = random.Random(2024)

    # 1. The port reproduces the original, command for command, under the same seed.
    bad = 0
    for trial in range(300):
        cmds = random_commands(gen, 40)
        a = original_run(cmds, trial)
        b = as_dict(run(initial_state(trial), cmds))
        bad += (a != b)
    print('1. port equals original on 300 random 40-command runs: mismatches =', bad)

    # 2. Projection versus full state across seeds, same commands.
    cmds = ['build factory', 'end', 'scan', 'end', 'scan', 'scan', 'end', 'end', 'build lab', 'end']
    finals = [run(initial_state(s), cmds) for s in range(200)]
    proj = {projection(f) for f in finals}
    fulls = {full(f) for f in finals}
    print('2. 200 seeds, one command list: distinct projections =', len(proj),
          ' distinct full states =', len(fulls))
    print('   projection:', next(iter(proj)))
    same_a = full(run(initial_state(7), cmds)) == full(run(initial_state(7), cmds))
    print('   same seed twice gives identical full state:', same_a)
    # checkpoint and resume: the generator is part of the state, so it must be copied
    mid = run(initial_state(7), cmds[:5])
    resumed = run(copy.deepcopy(mid), cmds[5:])
    print('   checkpoint after 5 commands then resume equals uninterrupted run:',
          full(resumed) == full(run(initial_state(7), cmds)))

    # 3. Scans overwrite tiles, including home. k scans, 25 possible tiles.
    for k in (3, 10, 25):
        trials, keys, home_lost = (10000 if k < 25 else 3000), 0, 0
        for t in range(trials):
            s = initial_state(t)
            s = run(s, ['scan'] * k)
            keys += len(s['tiles'])
            home_lost += s['tiles']['(0,0)']['scan'] != 'home'
        p_home = 1 - (24 / 25) ** k
        print(f'3. k={k:2d} scans: mean tiles {keys / trials:.3f} (formula {1 + 24 * p_home:.3f}),'
              f' P(home overwritten) {home_lost / trials:.4f} (formula {p_home:.4f})')

    # 4. Initial conditions behind the closed form.
    f, l, T, e0 = 2, 1, 10, 10
    pre = initial_state(0, energy=e0, buildings=['factory'] * f + ['lab'] * l)
    pre = run(pre, ['end'] * T)
    print('4a. buildings present at the start, e0=10, T=10:', pre['energy'], round(pre['entropy'], 9),
          ' closed form', e0 + T * (1 + 2 * f), round(T * (0.2 * f + 0.05 * l), 9))
    # affordable version of the question: one factory and one lab cost 9 in total
    pre = run(initial_state(0, buildings=['factory', 'lab']), ['end'] * T)
    paid0 = run(initial_state(0), ['build factory', 'build lab'] + ['end'] * T)
    late = run(initial_state(0), ['end'] * 3 + ['build factory', 'build lab'] + ['end'] * (T - 3))
    print('4b. one factory + one lab, T=10: present', pre['energy'], round(pre['entropy'], 9),
          '| paid at turn 0', paid0['energy'], round(paid0['entropy'], 9),
          '| paid after 3 turns', late['energy'], round(late['entropy'], 9))
    # the general formula: building b completed after t_b end-turns contributes (T - t_b) turns
    rng = random.Random(5)
    ok = 0
    n = 500
    for _ in range(n):
        T = rng.randint(5, 25)
        sched = sorted((rng.randint(0, T), rng.choice(['factory', 'lab'])) for _ in range(rng.randint(0, 4)))
        s, cmds, i = initial_state(0, energy=60), [], 0
        pred_e, pred_s, t = 60 + T, 0.0, 0
        valid = True
        for tb, kind in sched:
            pred_e += (2 * (T - tb) if kind == 'factory' else 0) - COST[kind]
            pred_s += (0.2 if kind == 'factory' else 0.05) * (T - tb)
        events = [(tb, 'build ' + kind) for tb, kind in sched]
        cmds = []
        done = 0
        for turn in range(T + 1):
            cmds += [c for tb, c in events if tb == turn]
            if turn < T:
                cmds.append('end')
        s = run(s, cmds)
        ok += (s['energy'] == pred_e and abs(s['entropy'] - pred_s) < 1e-9)
    print('4c. general formula e0 + T + sum 2(T-t_b)[factory] - costs; entropy sum rate*(T-t_b):', ok, 'of', n, 'agree')

    # 5. Growth under a greedy policy, and what entropy does to it.
    print('5. build a factory whenever one is affordable, before each end of turn')
    for T in (3, 6, 9, 12):
        s = initial_state(0)
        for _ in range(T):
            while s['energy'] >= COST['factory']:
                s, _ = step(s, 'build factory')
            s, _ = step(s, 'end')
        print(f'   T={T:2d} energy {s["energy"]:4d} buildings {len(s["buildings"]):3d} entropy {s["entropy"]:.3f}')
