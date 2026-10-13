import random
import statistics

def spacing(size, relative=0.0, constant=0.0):
    """Centre-to-centre spacing when relative and constant offsets add."""
    return relative * size + constant

def extent(n, size, step):
    """Total length of n modules of the given size at centre spacing step."""
    return (n - 1) * step + size

def positions(n, step, jitter, seed):
    """Module centres: i*step plus a uniform jitter in [-jitter, jitter]."""
    rng = random.Random(seed)
    u = [rng.uniform(-1.0, 1.0) for _ in range(n)]
    return [i * step + jitter * u[i] for i in range(n)], u

def overlaps(centres, size):
    """Number of adjacent pairs of modules that actually overlap.

    Modules of length `size` centred at c and c' overlap when |c' - c| < size.
    The absolute value matters when jitter is large enough for centres to cross.
    """
    return sum(1 for a, b in zip(centres, centres[1:]) if abs(b - a) < size)

def overlaps_signed(centres, size):
    """Adjacent pairs whose signed gap (b - a) is below size; ignores crossing."""
    return sum(1 for a, b in zip(centres, centres[1:]) if b - a < size)

def _tri_cdf(x, a):
    """CDF of T = e2 - e1, e1 and e2 independent uniform on [-a, a] (a > 0)."""
    if x <= -2 * a:
        return 0.0
    if x >= 2 * a:
        return 1.0
    if x <= 0:
        return (x + 2 * a) ** 2 / (8 * a ** 2)
    return 1.0 - (2 * a - x) ** 2 / (8 * a ** 2)

def p_signed(size, step, jitter):
    """P(signed gap < 0) for one adjacent pair, i.e. P(step + T < size).

    For 0 <= t <= 2a, with t = step - size, this equals (2a - t)^2 / (8 a^2).
    """
    return _tri_cdf(size - step, jitter)

def p_overlap(size, step, jitter):
    """Exact P(|step + T| < size): actual overlap, allowing centres to cross.

    Equals p_signed whenever 2*jitter <= step, because then step + T > 0 and no
    pair of centres can cross.
    """
    return _tri_cdf(size - step, jitter) - _tri_cdf(-size - step, jitter)

def p_both(size, step, jitter, grid=200000):
    """P(two consecutive gaps both overlap), by quadrature over the shared offset.

    Valid when 2*jitter <= step. Gaps i and i+1 share the offset e of the module
    between them: gap i overlaps when e_prev > e + t and gap i+1 when e_next < e - t.
    """
    a, t = jitter, step - size
    total = 0.0
    for k in range(grid):
        e = -a + (k + 0.5) * (2 * a) / grid
        g1 = min(1.0, max(0.0, (a - (e + t)) / (2 * a)))
        g2 = min(1.0, max(0.0, ((e - t) + a) / (2 * a)))
        total += g1 * g2
    return total / grid

def count_variance(n, size, step, jitter):
    """Exact variance of the overlap count for n modules (valid if 2*jitter <= step).

    Events are one-dependent: only adjacent gaps share an offset.
    """
    g = n - 1
    p = p_overlap(size, step, jitter)
    q = p_both(size, step, jitter)
    return g * p * (1 - p) + 2 * (g - 1) * (q - p * p)

def ensemble(n, size, step, jitter, seeds):
    counts = [overlaps(positions(n, step, jitter, s)[0], size) for s in seeds]
    return statistics.mean(counts), statistics.pstdev(counts)

if __name__ == '__main__':
    print(spacing(1.0, relative=1.2), extent(4, 1.0, 1.2))      # 1.2 4.6
    print(p_overlap(1.0, 1.5, 0.4))                              # 0.0703125
    seeds = range(200000)
    m, sd = ensemble(20, 1.0, 1.5, 0.4, seeds)
    print(round(m, 3), round(sd, 3), round(19 * p_overlap(1.0, 1.5, 0.4), 3))
    # independent-event variance versus exact one-dependent variance
    p = p_overlap(1.0, 1.5, 0.4)
    print(round((19 * p * (1 - p)) ** 0.5, 3), round(count_variance(20, 1.0, 1.5, 0.4) ** 0.5, 3))
    for a in (0.1, 0.25, 0.4, 0.55, 0.75):
        print(a, round(p_overlap(1.0, 1.5, a), 4))
    print([overlaps(positions(20, 1.5, 0.4, s)[0], 1.0) for s in range(8)])
    # crossing case: step 1.0, size 1.0, jitter 1.5 (2a > step)
    a_, st, sz = 1.5, 1.0, 1.0
    est = sum(overlaps(positions(2, st, a_, s)[0], sz) for s in range(400000)) / 400000
    est_signed = sum(overlaps_signed(positions(2, st, a_, s)[0], sz) for s in range(400000)) / 400000
    print(round(p_overlap(sz, st, a_), 4), round(est, 4), round(p_signed(sz, st, a_), 4), round(est_signed, 4))
    # common seeds versus independent seeds across two jitter levels
    n, size, step = 20, 1.0, 1.5
    diffs_same, diffs_indep = [], []
    for s in range(20000):
        u = positions(n, step, 1.0, s)[1]
        lo = overlaps([i * step + 0.3 * u[i] for i in range(n)], size)
        hi = overlaps([i * step + 0.4 * u[i] for i in range(n)], size)
        diffs_same.append(hi - lo)
        lo2 = overlaps(positions(n, step, 0.3, s)[0], size)
        hi2 = overlaps(positions(n, step, 0.4, s + 10 ** 6)[0], size)
        diffs_indep.append(hi2 - lo2)
    print(round(statistics.mean(diffs_same), 3), round(statistics.pstdev(diffs_same), 3),
          round(statistics.mean(diffs_indep), 3), round(statistics.pstdev(diffs_indep), 3))
    N = 10000
    print(8 * N, 12 * N, 6 * N, 2 * N)
