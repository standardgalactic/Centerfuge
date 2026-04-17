"""Field primitives. Each produces a callable ScalarFn or VectorFn."""

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Callable

from .vec import Vec3, v_add, v_mul, v_cross, v_normalize, sigmoid

ScalarFn = Callable[[float, float, float], float]
VectorFn = Callable[[float, float, float], Vec3]


@dataclass(frozen=True)
class Basin:
    """Gaussian attractive well in scalar space."""
    center: Vec3 = (0.0, 0.0, 0.0)
    amplitude: float = 1.0
    radius: float = 1.0

    def scalar(self) -> ScalarFn:
        cx, cy, cz = self.center
        r2 = max(self.radius * self.radius, 1e-9)

        def f(x: float, y: float, z: float) -> float:
            dx, dy, dz = x - cx, y - cy, z - cz
            return self.amplitude * math.exp(-(dx*dx + dy*dy + dz*dz) / r2)

        return f


@dataclass(frozen=True)
class DirectionalBias:
    """Uniform flow with optional curl around the flow axis."""
    direction: Vec3 = (1.0, 0.0, 0.0)
    strength: float = 1.0
    curl: float = 0.0
    origin: Vec3 = (0.0, 0.0, 0.0)

    def vector(self) -> VectorFn:
        base = v_normalize(self.direction)
        ox, oy, oz = self.origin

        def f(x: float, y: float, z: float) -> Vec3:
            radial = (x - ox, y - oy, z - oz)
            twist = v_cross(base, radial)
            return v_add(v_mul(base, self.strength), v_mul(v_normalize(twist), self.curl))

        return f


@dataclass(frozen=True)
class HarmonicField:
    """Separable sinusoidal scalar field."""
    weights: Vec3 = (1.0, 1.0, 1.0)
    frequencies: Vec3 = (1.0, 1.0, 1.0)
    phase: Vec3 = (0.0, 0.0, 0.0)
    amplitude: float = 1.0

    def scalar(self) -> ScalarFn:
        wx, wy, wz = self.weights
        fx, fy, fz = self.frequencies
        px, py, pz = self.phase

        def f(x: float, y: float, z: float) -> float:
            return self.amplitude * (
                wx * math.sin(fx * x + px)
                + wy * math.sin(fy * y + py)
                + wz * math.sin(fz * z + pz)
            )

        return f


@dataclass(frozen=True)
class EntropyCap:
    """Soft or hard amplitude limit modelling entropy ceiling."""
    threshold: float = 1.0
    softness: float = 8.0
    mode: str = "sigmoid"   # "sigmoid" | "hard"

    def apply(self, value: float) -> float:
        if self.mode == "hard":
            return max(-self.threshold, min(self.threshold, value))
        if self.threshold == 0:
            return 0.0
        scaled = value / self.threshold
        return self.threshold * (2.0 * sigmoid(scaled, self.softness) - 1.0)
