"""
Field composition and differential operators.

All operators are higher-order functions: they consume fields and return fields.
No state, no side effects. Safe to compose arbitrarily.
"""

from __future__ import annotations
from typing import Callable

from .vec import Vec3, v_add, v_mul, v_dot
from .fields import ScalarFn, VectorFn, EntropyCap


# ---------------------------------------------------------------------------
# Composition
# ---------------------------------------------------------------------------

def add_scalar_fields(*fields: ScalarFn) -> ScalarFn:
    def f(x: float, y: float, z: float) -> float:
        return sum(field(x, y, z) for field in fields)
    return f


def mul_scalar_fields(*fields: ScalarFn) -> ScalarFn:
    def f(x: float, y: float, z: float) -> float:
        out = 1.0
        for field in fields:
            out *= field(x, y, z)
        return out
    return f


def add_vector_fields(*fields: VectorFn) -> VectorFn:
    def f(x: float, y: float, z: float) -> Vec3:
        out: Vec3 = (0.0, 0.0, 0.0)
        for field in fields:
            out = v_add(out, field(x, y, z))
        return out
    return f


# ---------------------------------------------------------------------------
# Differential operators
# ---------------------------------------------------------------------------

def scalar_gradient(field: ScalarFn, eps: float = 1e-3) -> VectorFn:
    def grad(x: float, y: float, z: float) -> Vec3:
        dx = (field(x + eps, y, z) - field(x - eps, y, z)) / (2.0 * eps)
        dy = (field(x, y + eps, z) - field(x, y - eps, z)) / (2.0 * eps)
        dz = (field(x, y, z + eps) - field(x, y, z - eps)) / (2.0 * eps)
        return (dx, dy, dz)
    return grad


def divergence(vector_field: VectorFn, eps: float = 1e-3) -> ScalarFn:
    def div(x: float, y: float, z: float) -> float:
        dfx = (vector_field(x + eps, y, z)[0] - vector_field(x - eps, y, z)[0]) / (2.0 * eps)
        dfy = (vector_field(x, y + eps, z)[1] - vector_field(x, y - eps, z)[1]) / (2.0 * eps)
        dfz = (vector_field(x, y, z + eps)[2] - vector_field(x, y, z - eps)[2]) / (2.0 * eps)
        return dfx + dfy + dfz
    return div


def curl(vector_field: VectorFn, eps: float = 1e-3) -> VectorFn:
    def c(x: float, y: float, z: float) -> Vec3:
        dFz_dy = (vector_field(x, y + eps, z)[2] - vector_field(x, y - eps, z)[2]) / (2.0 * eps)
        dFy_dz = (vector_field(x, y, z + eps)[1] - vector_field(x, y, z - eps)[1]) / (2.0 * eps)
        dFx_dz = (vector_field(x, y, z + eps)[0] - vector_field(x, y, z - eps)[0]) / (2.0 * eps)
        dFz_dx = (vector_field(x + eps, y, z)[2] - vector_field(x - eps, y, z)[2]) / (2.0 * eps)
        dFy_dx = (vector_field(x + eps, y, z)[1] - vector_field(x - eps, y, z)[1]) / (2.0 * eps)
        dFx_dy = (vector_field(x, y + eps, z)[0] - vector_field(x, y - eps, z)[0]) / (2.0 * eps)
        return (
            dFz_dy - dFy_dz,
            dFx_dz - dFz_dx,
            dFy_dx - dFx_dy,
        )
    return c


# ---------------------------------------------------------------------------
# RSVP-specific compositions
# ---------------------------------------------------------------------------

def closure_field(
    phi: ScalarFn,
    v_field: VectorFn,
    alpha: float = 0.5,
    beta: float = 0.5,
    gamma: float = 0.25,   # advection weight; was hardcoded 0.25 in original
) -> ScalarFn:
    """
    Scalar closure measure:  alpha*phi - beta*div(v) + gamma*(grad(phi)·v)

    Positive values indicate regions where the scalar field is self-sustaining
    against the vector flow — the RSVP 'closure' criterion.
    """
    grad_phi = scalar_gradient(phi)
    div_v = divergence(v_field)

    def f(x: float, y: float, z: float) -> float:
        g = grad_phi(x, y, z)
        adv = v_dot(g, v_field(x, y, z))
        return alpha * phi(x, y, z) - beta * div_v(x, y, z) + gamma * adv

    return f


def capped_field(field: ScalarFn, cap: EntropyCap) -> ScalarFn:
    def f(x: float, y: float, z: float) -> float:
        return cap.apply(field(x, y, z))
    return f
