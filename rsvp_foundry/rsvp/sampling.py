"""
Sampling utilities: grid evaluation, point seeding from field thresholds.

These are the bridge between continuous field algebra and discrete geometry
lists that Blender scripts can iterate over.
"""

from __future__ import annotations
import random
from dataclasses import dataclass

from .vec import Vec3, lerp
from .fields import ScalarFn


@dataclass(frozen=True)
class GridSpec:
    nx: int
    ny: int
    nz: int
    bounds_min: Vec3 = (-1.0, -1.0, -1.0)
    bounds_max: Vec3 = (1.0, 1.0, 1.0)


def sample_scalar_grid(field: ScalarFn, grid: GridSpec) -> list[list[list[float]]]:
    """Evaluate field on a regular 3-D grid. Returns [ix][iy][iz] indexing."""
    xmin, ymin, zmin = grid.bounds_min
    xmax, ymax, zmax = grid.bounds_max

    return [
        [
            [
                field(
                    lerp(xmin, xmax, ix / max(grid.nx - 1, 1)),
                    lerp(ymin, ymax, iy / max(grid.ny - 1, 1)),
                    lerp(zmin, zmax, iz / max(grid.nz - 1, 1)),
                )
                for iz in range(grid.nz)
            ]
            for iy in range(grid.ny)
        ]
        for ix in range(grid.nx)
    ]


def seed_points_from_field(
    field: ScalarFn,
    count: int,
    bounds_min: Vec3 = (-1.0, -1.0, -1.0),
    bounds_max: Vec3 = (1.0, 1.0, 1.0),
    threshold: float = 0.0,
    max_tries: int = 100_000,
    rng: random.Random | None = None,
) -> list[Vec3]:
    """
    Rejection-sample `count` points where field >= threshold.

    Returns however many points were found within max_tries attempts —
    callers should check len(result) == count if exact count is required.
    """
    rng = rng or random.Random()
    out: list[Vec3] = []
    tries = 0

    while len(out) < count and tries < max_tries:
        tries += 1
        x = rng.uniform(bounds_min[0], bounds_max[0])
        y = rng.uniform(bounds_min[1], bounds_max[1])
        z = rng.uniform(bounds_min[2], bounds_max[2])
        if field(x, y, z) >= threshold:
            out.append((x, y, z))

    return out
