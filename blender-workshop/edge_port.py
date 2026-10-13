"""Seeded, side-effect-free port of the update rules in Centerfuge's Entropy's Edge.

Source: projects/entropy_edge/entropy_edge.py, commit b0648ff. The original keeps
its state in a module-level dict, prints from inside the update, and draws from the
unseeded global random generator. The port keeps the same rules and the same order
of random draws, so a seeded run is comparable to the original, but it returns the
new state instead of mutating a global, and the generator is part of the state.

Full state: (turn, energy, entropy, buildings, tiles, generator).
Projection: (turn, energy, entropy, buildings), which excludes tiles and generator.
"""
import copy
import random

COST = {'factory': 5, 'lab': 4}


def initial_state(seed, energy=10, buildings=()):
    return {'turn': 0, 'energy': energy, 'entropy': 0.0,
            'buildings': list(buildings), 'tiles': {'(0,0)': {'scan': 'home'}},
            'rng': random.Random(seed)}


def step(state, command):
    """One command. Returns (new_state, message). The input state is not modified."""
    s = copy.deepcopy(state)
    op, *arg = command.split()
    if op == 'end':
        s['turn'] += 1
        prod = sum(2 if b == 'factory' else 0 for b in s['buildings'])
        science = sum(1 if b == 'lab' else 0 for b in s['buildings'])
        s['energy'] += 1 + prod
        s['entropy'] += 0.1 * prod + 0.05 * science
        return s, 'end'
    if op == 'build':
        kind = arg[0]
        cost = COST.get(kind, 999)
        if s['energy'] < cost:
            return s, 'refused'          # state unchanged: a refusal is not a transition
        s['energy'] -= cost
        s['buildings'].append(kind)
        return s, 'built'
    if op == 'scan':
        x = s['rng'].randint(-2, 2)
        y = s['rng'].randint(-2, 2)
        s['tiles'][f'({x},{y})'] = {'scan': s['rng'].choice(['mineral', 'oasis', 'void'])}
        return s, 'scanned'
    raise ValueError(command)


def run(state, commands):
    for c in commands:
        state, _ = step(state, c)
    return state


def projection(state):
    return (state['turn'], state['energy'], round(state['entropy'], 9), tuple(state['buildings']))


def full(state):
    return projection(state) + (tuple(sorted((k, v['scan']) for k, v in state['tiles'].items())),)
