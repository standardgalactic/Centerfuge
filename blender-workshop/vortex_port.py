"""Seeded Python port of the particle update in Centerfuge's vortex sorter.

Source: experiments/vortex_sorting_lab/index.html in standardgalactic/Centerfuge,
commit b0648ff. The port reproduces the update rule only (spawn, radial step,
threshold capture); it is not the original code. The original uses
Math.random() and a variable time step equal to the elapsed frame time, capped
at 0.05 s. Here the generator is seeded and the step is fixed.
"""
import math
import random
import statistics

MASS = {'light': 0.55, 'medium': 1.0, 'heavy': 1.65}
HUB_R, R_MAX, CAP = 12.0, 185.0, 160

def run_particle(cls, rot, intake, turb, t1, t2, dt, rng, noise='linear'):
    """Follow one particle until capture. Returns (outlet, time).

    noise='linear' multiplies the random term by frame = 60*dt, as in the source.
    noise='sqrt' multiplies it by sqrt(frame), the diffusive scaling.
    """
    rotation, drag, turbulence = rot / 100.0, intake / 100.0 * 0.55, turb / 100.0
    frame = dt * 60.0
    scale = frame if noise == 'linear' else math.sqrt(frame)
    drift = (MASS[cls] * rotation - drag) * frame
    r = (t1 + t2) / 2 + (rng.random() - 0.5) * (t2 - t1) * 0.3
    t = 0.0
    while True:
        r += drift + (rng.random() - 0.5) * turbulence * 1.3 * scale
        t += dt
        if r <= t1:
            return 'fines', t
        if r >= t2:
            return 'overflow', t
        r = max(HUB_R, min(R_MAX - 2, r))   # never changes r for slider ranges

def noise_variance(dt, turb, horizon, trials, seed, noise='linear'):
    """Variance of r after `horizon` seconds of pure noise (no drift, no capture)."""
    rng = random.Random(seed)
    frame = dt * 60.0
    scale = frame if noise == 'linear' else math.sqrt(frame)
    steps = int(round(horizon / dt))
    finals = []
    for _ in range(trials):
        r = 0.0
        for _ in range(steps):
            r += (rng.random() - 0.5) * (turb / 100.0) * 1.3 * scale
        finals.append(r)
    return statistics.pvariance(finals)

def system(seconds, dt, rot, intake, turb, t1, t2, seed):
    """Whole chamber with intake, cap, and counters. Returns a ledger dict."""
    rng = random.Random(seed)
    rotation, drag, turbulence = rot / 100.0, intake / 100.0 * 0.55, turb / 100.0
    frame = dt * 60.0
    names = list(MASS)
    particles, acc = [], 0.0
    bins = {'fines': 0, 'overflow': 0}
    attempts = accepted = 0
    for _ in range(int(round(seconds / dt))):
        acc += dt * (0.3 + intake / 100.0 * 5.7)
        while acc >= 1:
            attempts += 1
            if len(particles) < CAP:
                cls = names[int(rng.random() * 3)]
                particles.append([cls, (t1 + t2) / 2 + (rng.random() - 0.5) * (t2 - t1) * 0.3])
                accepted += 1
            acc -= 1
        survivors = []
        for p in particles:
            p[1] += (MASS[p[0]] * rotation - drag + (rng.random() - 0.5) * turbulence * 1.3) * frame
            if p[1] <= t1:
                bins['fines'] += 1
            elif p[1] >= t2:
                bins['overflow'] += 1
            else:
                survivors.append(p)
        particles = survivors
    return dict(attempts=attempts, accepted=accepted, rejected=attempts - accepted,
                inside=len(particles), fines=bins['fines'], overflow=bins['overflow'])

def outcome_table(dt, noise, trials, seed, **p):
    rng = random.Random(seed)
    out = {}
    for cls in MASS:
        res = [run_particle(cls, dt=dt, rng=rng, noise=noise, **p) for _ in range(trials)]
        out[cls] = (sum(o == 'overflow' for o, _ in res) / trials,
                    statistics.mean(t for _, t in res))
    return out

if __name__ == '__main__':
    default = dict(rot=55, intake=45, turb=18, t1=55, t2=140)
    # drift per second of each class at the default sliders
    for cls in MASS:
        print(cls, 'drift per second at defaults:',
              round((MASS[cls] * 0.55 - 0.45 * 0.55) * 60, 3))
    # 1. ledger
    for intake in (45, 100):
        s = system(300, 1 / 60, 55, intake, 18, 55, 140, seed=1)
        print('ledger intake', intake, s,
              'accepted == inside + captured:', s['accepted'] == s['inside'] + s['fines'] + s['overflow'])
    # 2. pure-noise variance after 1 s versus dt (turbulence 100)
    for dt in (1 / 120, 1 / 60, 1 / 30, 0.05):
        theory = (1.3 * 1.0) ** 2 / 12 * 3600 * 1.0 * dt
        print('dt', round(dt, 4), 'linear var', round(noise_variance(dt, 100, 1.0, 20000, 3), 3),
              'theory', round(theory, 3), '| sqrt var', round(noise_variance(dt, 100, 1.0, 20000, 3, 'sqrt'), 3))
    # 3. outcome sensitivity: light-particle overflow fraction, noisy setting
    p = dict(rot=30, intake=55, turb=100, t1=55, t2=140)
    print('settings', p)
    for noise in ('linear', 'sqrt'):
        for dt in (1 / 120, 1 / 60, 1 / 30, 0.05):
            tab = outcome_table(dt, noise, 20000, 11, **p)
            print(noise, round(dt, 4), {k: (round(v[0], 4), round(v[1], 2)) for k, v in tab.items()})
