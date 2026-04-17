"""
Terrain, landscape, and architectural profile operators.

These combine field primitives into geometry-ready outputs:
height maps, terrain scalars, tower radius profiles, and residue curves.
"""

from __future__ import annotations
import math

from .vec import Vec3, lerp
from .fields import ScalarFn, VectorFn, Basin, HarmonicField, DirectionalBias, EntropyCap
from .operators import scalar_gradient


# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------

def sample_height_map(
    field: ScalarFn,
    nx: int,
    ny: int,
    bounds_min: tuple[float, float] = (-1.0, -1.0),
    bounds_max: tuple[float, float] = (1.0, 1.0),
    z_scale: float = 1.0,
) -> list[list[float]]:
    """Rasterise field at z=0 into a 2-D height map (nx rows, ny columns)."""
    xmin, ymin = bounds_min
    xmax, ymax = bounds_max

    return [
        [z_scale * field(lerp(xmin, xmax, ix / max(nx - 1, 1)),
                         lerp(ymin, ymax, iy / max(ny - 1, 1)),
                         0.0)
         for iy in range(ny)]
        for ix in range(nx)
    ]


# ---------------------------------------------------------------------------
# Terrain composition
# ---------------------------------------------------------------------------

def terrain_field(
    basin: Basin,
    harmonic: HarmonicField,
    directional: DirectionalBias,
    cap: EntropyCap,
    ridge_strength: float = 0.35,
) -> ScalarFn:
    """
    Compose a terrain scalar from standard RSVP primitives.

    Ridge contribution is the L1 norm of the horizontal flow components,
    producing elevation bumps along flow-aligned ridges.
    """
    b = basin.scalar()
    h = harmonic.scalar()
    v = directional.vector()

    def f(x: float, y: float, z: float) -> float:
        base = b(x, y, z) + h(x, y, z)
        flow = v(x, y, z)
        ridge = ridge_strength * (abs(flow[0]) + abs(flow[1]))
        return cap.apply(base + ridge)

    return f


# ---------------------------------------------------------------------------
# Architectural profiles
# ---------------------------------------------------------------------------

def residue_profile(t: float, lam: float = 0.9, rings: int = 5) -> float:
    """
    Lacunary sum modelling residue oscillation along a normalised [0,1] axis.

    Inspired by positive-geometry residue structure: each ring contributes
    a geometrically-decayed harmonic, producing a self-similar ripple profile.
    """
    return sum((lam ** k) * math.sin((2.0 ** k) * math.pi * t) for k in range(1, rings + 1))


def tower_radius(
    z: float,
    base_radius: float = 1.0,
    taper: float = 0.6,
    residue: float = 0.12,
    lam: float = 0.9,
) -> float:
    """
    Radius of a tower cross-section at normalised height z ∈ [0, 1].

    Linear taper with residue-profile corrugation. Clamps to 0.05 minimum
    so the top never degenerates to a point.
    """
    t = max(0.0, min(1.0, z))
    return max(0.05, base_radius * (1.0 - taper * t) + residue * residue_profile(t, lam=lam))
