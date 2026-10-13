"""The solver as a separate process. Messages on stdin/stdout: one JSON header line, then raw bytes.

Request header: {"id", "op", "n", "steps", "level", "fault"}; body: mask (uint8 n*n), fixed (uint8 n*n).
Ops: load (replace the stored field with the one sent after the masks), reset (zero the field), advance (run `steps` steps with the given mask), echo (return the body unchanged, for transport tests).
Reply header: {"id", "ok", "n", "version"}; body: field (float64 n*n).
The `fault` field exists only to test the driver: it makes this server misbehave in a stated way.
"""
import json, sys, time
import numpy as np
from solver import advance

VERSION = 'diffuse-1'
u = None


def reply(h, body=b''):
    sys.stdout.buffer.write((json.dumps(h) + '\n').encode()); sys.stdout.buffer.write(body); sys.stdout.buffer.flush()


def main():
    global u
    rd = sys.stdin.buffer
    while True:
        line = rd.readline()
        if not line:
            return
        h = json.loads(line); n = h['n']
        if h['op'] == 'echofile':
            np.save(h['path'] + '.out.npy', np.load(h['path'])); reply({'id': h['id'], 'ok': True, 'n': 0, 'nbytes': 0}); continue
        if h['op'] == 'echo':
            body = rd.read(h['nbytes']); reply({'id': h['id'], 'ok': True, 'n': n, 'nbytes': len(body)}, body); continue
        mask = np.frombuffer(rd.read(n * n), dtype=np.uint8).reshape(n, n)
        fixed = np.frombuffer(rd.read(n * n), dtype=np.uint8).reshape(n, n).astype(bool)
        if h['op'] == 'load':
            u = np.frombuffer(rd.read(8 * n * n), dtype=np.float64).reshape(n, n).copy(); reply({'id': h['id'], 'ok': True, 'n': n, 'version': VERSION}, u.tobytes()); continue
        if h['op'] == 'reset' or u is None or u.shape != (n, n):
            u = np.zeros((n, n))
        if h['op'] == 'advance':
            f = h.get('fault')
            if f == 'crash': sys.exit(3)
            if f == 'hang': time.sleep(60)
            u = advance(u, mask, fixed, h['level'], h['steps'])
        out = u.copy(); rid = h['id']; shape = n
        f = h.get('fault')
        if f == 'nan': out[n // 2, n // 2] = float('nan')
        if f == 'stale': rid = h['id'] - 1
        if f == 'shape': shape = n - 1; out = out[:n - 1, :n - 1].copy()
        if f == 'bias': out = out + 1e-6
        if f == 'transpose': out = out.T.copy()
        if f == 'overshoot': out = out * 1.5
        reply({'id': rid, 'ok': True, 'n': shape, 'version': VERSION}, out.tobytes())


main()
