"""Stable great-circle helpers for mathutils vectors (single precision), and a check against float64.

    python3 sphere_tools.py
"""
import math
import bpy  # makes mathutils importable outside Blender
from mathutils import Vector


def angle(a, b):
    """Angle between two vectors from atan2(|a x b|, a . b); accurate for small and near-pi angles."""
    return math.atan2(a.cross(b).length, a.dot(b))


def circle_normal(a, b):
    """Unit normal of the great circle through a and b. Raises when a and b are (nearly) parallel."""
    n = a.cross(b)
    if n.length < 1e-4 * a.length * b.length:
        raise ValueError('points are nearly equal or antipodal; the circle through them is not determined')
    return n.normalized()


def arc_point(a, b, t):
    """Point at fraction t along the shorter great-circle arc from unit vector a to unit vector b."""
    th = angle(a, b)
    if th < 1e-6:
        return a.lerp(b, t).normalized()
    return (a * math.sin((1 - t) * th) + b * math.sin(t * th)) / math.sin(th)


if __name__ == '__main__':
    import numpy as np
    for th in (1e-1, 1e-3, 1e-4, 1e-6):
        a = Vector((1, 0, 0)); b = Vector((math.cos(th), math.sin(th), 0))
        print(f'theta {th:.0e}: Vector.angle rel. error {abs(a.angle(b) - th) / th:.1e}, angle() rel. error {abs(angle(a, b) - th) / th:.1e}')
    a = Vector((1, 0, 0)); b = Vector((math.cos(2.5), math.sin(2.5), 0))
    P = [arc_point(a, b, k / 100) for k in range(101)]
    steps = [angle(P[i], P[i + 1]) for i in range(100)]
    print('arc_point at 143 degrees: step ratio', max(steps) / min(steps), ' largest |length-1|', max(abs(p.length - 1) for p in P))
    try:
        circle_normal(Vector((1, 0, 0)), Vector((-1, 1e-6, 0)))
    except ValueError as e:
        print('antipodal guard:', e)
