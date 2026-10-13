"""An external solver, written to be independent of Blender: explicit diffusion on an n by n grid with insulating obstacles.

State lives here, not in Blender. A cell is fluid where mask == 0. Flux between two fluid cells is D*(u_j - u_i)*dt/dx^2;
no flux crosses a face that touches an obstacle cell. Cells flagged in `fixed` are held at the value `level` (a source).
"""
import numpy as np

D, DT = 1.0, 0.2          # D*DT/dx^2 = 0.2 < 0.25, the stability limit of the explicit scheme in two dimensions


def step(u, mask, fixed, level, k):
    fluid = mask == 0
    out = u.copy()
    for ax in (0, 1):
        a = [slice(None)] * 2; b = [slice(None)] * 2
        a[ax] = slice(0, -1); b[ax] = slice(1, None)
        a, b = tuple(a), tuple(b)
        both = fluid[a] & fluid[b]
        f = np.where(both, k * (u[b] - u[a]), 0.0)
        out[a] += f; out[b] -= f
    out[~fluid] = 0.0
    out[fixed & fluid] = level
    return out


def advance(u, mask, fixed, level, steps):
    k = D * DT
    for _ in range(steps):
        u = step(u, mask, fixed, level, k)
    return u


def total(u, mask):
    return float(u[mask == 0].sum())
