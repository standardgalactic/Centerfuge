"""
Growth trajectory operators.

trace_growth_path and branch_paths produce lists of Vec3 points suitable
for conversion to Blender curves or for driving particle systems.
"""

from __future__ import annotations
import random
from typing import Sequence

from .vec import Vec3, v_add, v_mul, v_cross, v_length, v_normalize
from .fields import ScalarFn, VectorFn
from .operators import scalar_gradient


def trace_growth_path(
    start: Vec3,
    direction_field: VectorFn,
    scalar_field: ScalarFn | None = None,
    step_size: float = 0.05,
    steps: int = 100,
    attraction: float = 0.25,
) -> list[Vec3]:
    """
    Euler-integrate along direction_field from start.

    If scalar_field is provided its gradient is blended in with weight
    `attraction`, pulling the path toward field maxima (useful for canopy
    clustering or root-to-nutrient attraction).
    """
    points: list[Vec3] = [start]
    pos = start
    grad = scalar_gradient(scalar_field) if scalar_field is not None else None

    for _ in range(steps):
        direction = direction_field(*pos)
        if grad is not None:
            direction = v_add(direction, v_mul(grad(*pos), attraction))
        direction = v_normalize(direction)
        pos = v_add(pos, v_mul(direction, step_size))
        points.append(pos)

    return points


def branch_paths(
    root_path: Sequence[Vec3],
    direction_field: VectorFn,
    branch_probability: float = 0.08,
    max_branches: int = 8,
    step_size: float = 0.04,
    branch_steps: int = 40,
    lateral_strength: float = 0.65,
    rng: random.Random | None = None,
) -> list[list[Vec3]]:
    """
    Generate lateral branches from a root path.

    Each branch starts from a randomly selected interior point of root_path
    and integrates with a laterally-offset direction field.

    The lateral offset is computed once per branch and captured correctly
    into the closure — avoiding the late-binding trap via a default-argument
    capture pattern.
    """
    rng = rng or random.Random()
    branches: list[list[Vec3]] = []

    for point in root_path[1:-1]:
        if len(branches) >= max_branches:
            break
        if rng.random() > branch_probability:
            continue

        base = direction_field(*point)

        # Compute lateral once; fall back to y-cross if base is near-vertical
        lateral_seed = v_cross(base, (0.0, 0.0, 1.0))
        if v_length(lateral_seed) < 1e-6:
            lateral_seed = v_cross(base, (0.0, 1.0, 0.0))
        lateral = v_mul(v_normalize(lateral_seed), lateral_strength)

        # Capture lateral in default arg — prevents late-binding across iterations
        def branched_dir(
            x: float, y: float, z: float,
            _lat: Vec3 = lateral,
        ) -> Vec3:
            return v_add(direction_field(x, y, z), _lat)

        branches.append(
            trace_growth_path(point, branched_dir, step_size=step_size, steps=branch_steps)
        )

    return branches
