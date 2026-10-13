"""Driver for an external solver process, with validation and a replay log. Plain Python, no Blender.

    python3 coupling.py transport     # cost of moving arrays through a pipe, a text format and a file
    python3 coupling.py faults        # which checks catch which misbehaviour
"""
import hashlib, json, os, queue, subprocess, sys, tempfile, threading, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


class SolverError(Exception):
    pass


class Solver:
    def __init__(self, timeout=10.0):
        self.timeout = timeout; self.count = 0; self.version = None; self.start()

    def start(self):
        self.p = subprocess.Popen([sys.executable, os.path.join(HERE, 'solver_server.py')], cwd=HERE,
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.q = queue.Queue()
        threading.Thread(target=self._reader, args=(self.p,), daemon=True).start()

    def _reader(self, p):
        try:
            while True:
                line = p.stdout.readline()
                if not line:
                    self.q.put(('eof', None, None)); return
                h = json.loads(line); n = h.get('n', 0)
                nb = h['nbytes'] if 'nbytes' in h else 8 * n * n
                body = p.stdout.read(nb)
                self.q.put(('msg', h, body))
        except Exception as e:
            self.q.put(('err', repr(e), None))

    def stop(self):
        try: self.p.stdin.close()
        except Exception: pass
        self.p.kill(); self.p.wait()

    def raw(self, header, body=b''):
        self.count += 1; header = dict(header, id=self.count)
        try:
            self.p.stdin.write((json.dumps(header) + '\n').encode()); self.p.stdin.write(body); self.p.stdin.flush()
        except (BrokenPipeError, OSError) as e:
            raise SolverError(f'send failed: {e!r}')
        try:
            kind, h, b = self.q.get(timeout=self.timeout)
        except queue.Empty:
            raise SolverError('timeout')
        if kind != 'msg':
            raise SolverError(f'solver process ended ({kind})')
        return header, h, b

    def advance(self, mask, fixed, level, steps, op='advance', fault=None):
        n = mask.shape[0]
        body = mask.astype(np.uint8).tobytes() + fixed.astype(np.uint8).tobytes()
        hd, h, b = self.raw({'op': op, 'n': n, 'steps': steps, 'level': level, 'fault': fault}, body)
        return hd, h, b


def load(solver, mask, fixed, u):
    n = mask.shape[0]
    body = mask.astype(np.uint8).tobytes() + fixed.astype(np.uint8).tobytes() + np.ascontiguousarray(u, dtype=np.float64).tobytes()
    return solver.raw({'op': 'load', 'n': n}, body)


def digest(*arrays):
    m = hashlib.sha1()
    for a in arrays: m.update(np.ascontiguousarray(a).tobytes())
    return m.hexdigest()[:12]


def validate(hd, h, b, n, mass_before=None, mask=None, has_source=True, level=None, shadow=None, checks=('id', 'shape', 'finite', 'bounds', 'mass', 'shadow')):
    """Return the name of the first failed check, or None. Each check is separate so that their coverage can be measured."""
    if 'id' in checks and h['id'] != hd['id']: return 'id'
    if 'shape' in checks and (h['n'] != n or len(b) != 8 * n * n): return 'shape'
    if not set(checks) & {'finite', 'bounds', 'mass', 'shadow'}: return None
    if len(b) != 8 * n * n: return 'unusable'
    u = np.frombuffer(b, dtype=np.float64).reshape(n, n)
    if 'finite' in checks and not np.isfinite(u).all(): return 'finite'
    if 'bounds' in checks and level is not None and (u.min() < -1e-9 or u.max() > level + 1e-9): return 'bounds'
    if 'mass' in checks and mass_before is not None and not has_source:
        if abs(float(u[mask == 0].sum()) - mass_before) > 1e-9 * max(1.0, abs(mass_before)): return 'mass'
    if 'shadow' in checks and shadow is not None and not np.array_equal(u, shadow): return 'shadow'
    return None


def transport():
    s = Solver(timeout=60)
    print('floats   pipe_ms   text_ms   file_ms   text_bytes/float')
    for m in (10**3, 10**4, 10**5, 10**6):
        a = np.random.default_rng(1).normal(size=m)
        def t_pipe():
            hd, h, b = s.raw({'op': 'echo', 'n': 0, 'nbytes': 8 * m}, a.tobytes())
            return np.array_equal(np.frombuffer(b, dtype=np.float64), a)
        def t_text():
            txt = json.dumps(a.tolist()).encode()
            hd, h, b = s.raw({'op': 'echo', 'n': 0, 'nbytes': len(txt)}, txt)
            back = np.array(json.loads(b)); return np.array_equal(back, a), len(txt) / m
        def t_file():
            with tempfile.TemporaryDirectory() as d:
                f = os.path.join(d, 'a.npy'); np.save(f, a)
                s.raw({'op': 'echofile', 'n': 0, 'path': f}); back = np.load(f + '.out.npy')
            return np.array_equal(back, a)
        res = []
        for fn in (t_pipe, t_text, t_file):
            ts = []
            for _ in range(5):
                t0 = time.perf_counter(); r = fn(); ts.append(time.perf_counter() - t0)
            ok = r[0] if isinstance(r, tuple) else r
            res.append((1000 * float(np.median(ts)), ok, r[1] if isinstance(r, tuple) else None))
        print(f'{m:<8d} {res[0][0]:8.2f}  {res[1][0]:8.2f}  {res[2][0]:8.2f}   {res[1][2]:.1f}   exact: pipe={res[0][1]} text={res[1][1]} file={res[2][1]}')
    t0 = time.perf_counter()
    for _ in range(200): s.raw({'op': 'echo', 'n': 0, 'nbytes': 8}, b'\0' * 8)
    print('latency, 8-byte round trip through the pipe (ms):', round(1000 * (time.perf_counter() - t0) / 200, 3))
    t0 = time.perf_counter(); s2 = Solver(); s2.raw({'op': 'echo', 'n': 0, 'nbytes': 8}, b'\0' * 8)
    print('start a new solver process and complete one call (ms):', round(1000 * (time.perf_counter() - t0), 1)); s2.stop(); s.stop()


FAULTS = [None, 'crash', 'hang', 'stale', 'shape', 'nan', 'overshoot', 'bias', 'transpose', 'transpose-symmetric']
CHECKS = ('id', 'shape', 'finite', 'bounds', 'mass', 'shadow')


def faults():
    import solver as S
    n = 32
    print('A cell reads x where that single check flags the fault, n/a where the reply cannot be evaluated by that check; "driver" means the driver itself raised before any check.')
    print(f'{"fault":20s}' + ''.join(f'{c:>8s}' for c in CHECKS))
    for f in FAULTS:
        sym = f == 'transpose-symmetric'
        mask = np.zeros((n, n), np.uint8)
        if not sym: mask[:, 16] = 1; mask[10:14, 16] = 0
        fixed = np.zeros((n, n), bool); fixed[16 if not sym else n // 2, 2 if not sym else n // 2] = True
        if sym: fixed[n // 2 - 1, n // 2 - 1] = True; fixed[n // 2, n // 2 - 1] = True; fixed[n // 2 - 1, n // 2] = True
        s = Solver(timeout=2.0)
        try:
            s.advance(mask, fixed, 100.0, 1, op='reset'); s.advance(mask, fixed, 100.0, 50)
            nofix = np.zeros((n, n), bool)
            hd, h, b = s.advance(mask, nofix, 0.0, 0)
            ref = np.frombuffer(b, dtype=np.float64).reshape(n, n).copy(); before = float(ref[mask == 0].sum())
            shadow = S.advance(ref.copy(), mask, nofix, 0.0, 20)
            fl = f.replace('-symmetric', '') if f else None
            hd, h, b = s.advance(mask, nofix, 0.0, 20, fault=fl)
            row = []
            for c in CHECKS:
                r = validate(hd, h, b, n, before, mask, False, 100.0, shadow, (c,))
                row.append('n/a' if r == 'unusable' else ('x' if r else '-'))
        except SolverError:
            row = ['driver'] * len(CHECKS)
        finally:
            s.stop()
        print(f'{str(f):20s}' + ''.join(f'{c:>8s}' for c in row))


if __name__ == '__main__':
    {'transport': transport, 'faults': faults}[sys.argv[1]]()
