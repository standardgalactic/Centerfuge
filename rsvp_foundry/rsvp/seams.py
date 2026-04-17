"""
Seam and obstruction operators for TARTAN-style gluing artifacts.

seam_displacement maps a point to its displaced position near a seam plane.
seam_obstruction_metric returns [0,1] proximity to a seam (1 = on seam).
"""

from __future__ import annotations
import math

from .vec import Vec3, smoothstep

_AXES = {"x": 0, "y": 1, "z": 2}


def seam_displacement(
    x: float,
    y: float,
    z: float,
    seam_axis: str = "x",
    seam_position: float = 0.0,
    width: float = 0.15,
    offset: Vec3 = (0.15, 0.0, 0.0),
    twist: float = 0.0,
) -> Vec3:
    """
    Displace a point near a seam plane.

    The seam sits at `seam_position` along `seam_axis`. Points within
    `width` on either side are blended toward the offset position.
    An optional `twist` angle (radians) rotates the displaced point
    around the seam axis.

    Twist evaluation uses simultaneous assignment — both new coordinates
    are computed from the pre-assignment values, so ordering is safe.
    """
    idx = _AXES[seam_axis]
    coord = (x, y, z)[idx]
    blend = smoothstep(-width, width, coord - seam_position)
    centered = 2.0 * blend - 1.0

    px, py, pz = x, y, z
    ox, oy, oz = offset
    px += ox * centered
    py += oy * centered
    pz += oz * centered

    if twist != 0.0:
        angle = twist * centered
        c, s = math.cos(angle), math.sin(angle)
        if seam_axis == "x":
            py, pz = c * py - s * pz, s * py + c * pz   # simultaneous: safe
        elif seam_axis == "y":
            px, pz = c * px - s * pz, s * px + c * pz
        else:
            px, py = c * px - s * py, s * px + c * py

    return (px, py, pz)


def seam_obstruction_metric(
    x: float,
    y: float,
    z: float,
    seam_axis: str = "x",
    seam_position: float = 0.0,
    width: float = 0.15,
) -> float:
    """
    Return proximity to seam in [0, 1]. 1.0 = on seam, 0.0 = far from seam.

    Useful as a mask for material blending or constraint strength modulation.
    """
    idx = _AXES[seam_axis]
    coord = (x, y, z)[idx]
    return 1.0 - smoothstep(0.0, width, abs(coord - seam_position))
