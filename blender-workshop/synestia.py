"""Prologue: a prescribed Gaussian-torus density field, its contour surfaces, and what the contour level decides.

    python3 synestia.py table|hole|mesh      (mesh needs Blender's Python module)
Units are arbitrary: R0 = 1 is the ring radius. Nothing here is a calculation of a planetary body.
"""
import math, sys
import numpy as np
from scipy import integrate

R0, SR, SZ = 1.0, 0.35, 0.15


def rho(R, z, rho0=1.0):
    return rho0 * np.exp(-(R - R0) ** 2 / (2 * SR ** 2) - z ** 2 / (2 * SZ ** 2))


def k_of(f):
    """Contour rho = f*rho0 is the ellipse (R-R0)^2/SR^2 + z^2/SZ^2 = k^2 with k = sqrt(2 ln(1/f))."""
    return math.sqrt(2 * math.log(1 / f))


def semi_axes(f):
    k = k_of(f); return k * SR, k * SZ


def total_mass():
    """Mass of the whole field on R >= 0: 2 pi * sqrt(2 pi) SZ * int_0^inf R exp(-(R-R0)^2/2SR^2) dR."""
    I = integrate.quad(lambda R: R * math.exp(-(R - R0) ** 2 / (2 * SR ** 2)), 0, np.inf)[0]
    return 2 * math.pi * math.sqrt(2 * math.pi) * SZ * I


def enclosed_mass(f):
    """Mass inside the contour surface rho >= f*rho0, for R >= 0 (valid also when the hole has closed)."""
    k = k_of(f)
    def inner(R):
        zmax = SZ * math.sqrt(max(0.0, k * k - (R - R0) ** 2 / SR ** 2))
        # int_{-zmax}^{zmax} exp(-z^2/2SZ^2) dz
        zi = SZ * math.sqrt(2 * math.pi) * math.erf(zmax / (SZ * math.sqrt(2)))
        return 2 * math.pi * R * math.exp(-(R - R0) ** 2 / (2 * SR ** 2)) * zi
    lo, hi = max(0.0, R0 - k * SR), R0 + k * SR
    return integrate.quad(inner, lo, hi)[0]


def volume_analytic(f):
    a, b = semi_axes(f)
    return 2 * math.pi ** 2 * R0 * a * b if a < R0 else None


if __name__ == '__main__':
    cmd = sys.argv[1]
    M = total_mass()
    if cmd == 'table':
        print('total mass', round(M, 5))
        print('f      k      a      b     hole_radius  volume   mass_fraction')
        for f in (0.6, 0.3, 0.1, 0.03, 0.0169, 0.01, 0.003):
            a, b = semi_axes(f); v = volume_analytic(f)
            print(f, round(k_of(f), 3), round(a, 3), round(b, 3), round(R0 - a, 3), None if v is None else round(v, 4), round(enclosed_mass(f) / M, 4))
    elif cmd == 'hole':
        k = R0 / SR; print('hole closes at f =', math.exp(-k * k / 2), 'k =', k)
