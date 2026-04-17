#!/usr/bin/env python3
"""
probe_fields.py — explore rsvp field statistics without running Blender.

Usage:
    python probe_fields.py [--preset PRESET] [--seed S] [--samples N] [--grid G]

Prints closure, phi, and divergence stats across random and grid samples.
Use this to scan the parameter space cheaply before committing to renders.

Examples:
    python probe_fields.py --preset make_tree_operators --samples 2000
    python probe_fields.py --grid 16 --seed 7
"""

from __future__ import annotations
import argparse
import random
import sys
import math

sys.path.insert(0, ".")
import rsvp


PRESETS = {
    "make_default_rsvp_field": rsvp.make_default_rsvp_field,
    "make_tree_operators": rsvp.make_tree_operators,
    "make_landscape_operators": rsvp.make_landscape_operators,
}


def stats(values: list[float]) -> dict:
    n = len(values)
    if n == 0:
        return {}
    mean = sum(values) / n
    var = sum((v - mean) ** 2 for v in values) / n
    return {
        "min":    round(min(values), 5),
        "max":    round(max(values), 5),
        "mean":   round(mean, 5),
        "std":    round(math.sqrt(var), 5),
        "n":      n,
    }


def print_stats(label: str, values: list[float]) -> None:
    s = stats(values)
    print(f"  {label:20s}  min={s['min']:9.5f}  max={s['max']:9.5f}"
          f"  mean={s['mean']:9.5f}  std={s['std']:8.5f}  n={s['n']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe rsvp field statistics")
    parser.add_argument("--preset", default="make_default_rsvp_field",
                        choices=list(PRESETS))
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--samples", type=int, default=1000,
                        help="Random sample count")
    parser.add_argument("--grid", type=int, default=0,
                        help="If > 0, also sample a GxGxG grid")
    parser.add_argument("--bounds", type=float, default=1.2,
                        help="Sampling bounds [-B, B] per axis")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    B = args.bounds

    print(f"[probe] preset={args.preset}  seed={args.seed}  bounds=±{B}")

    preset_fn = PRESETS[args.preset]
    result = preset_fn()

    # Unpack whichever structure the preset returns
    if isinstance(result, tuple):
        phi, v_field, closure = result
    else:
        phi      = result.get("phi") or result.get("terrain")
        v_field  = result.get("v_field") or result.get("direction")
        closure  = result.get("closure")

    # Random samples
    pts = [(rng.uniform(-B, B), rng.uniform(-B, B), rng.uniform(-B, B))
           for _ in range(args.samples)]

    phi_vals     = [phi(*p) for p in pts] if phi else []
    closure_vals = [closure(*p) for p in pts] if closure else []
    div_field    = rsvp.divergence(v_field) if v_field else None
    div_vals     = [div_field(*p) for p in pts] if div_field else []

    print(f"\n  Random samples (n={args.samples}):")
    if phi_vals:     print_stats("phi",      phi_vals)
    if closure_vals: print_stats("closure",  closure_vals)
    if div_vals:     print_stats("div(v)",   div_vals)

    # Growth path quick probe
    if v_field:
        path = rsvp.trace_growth_path(
            (0.0, 0.0, 0.0), v_field,
            scalar_field=phi, steps=40, step_size=0.05, attraction=0.2
        )
        zs = [p[2] for p in path]
        print(f"\n  Growth path (40 steps from origin):")
        print(f"  {'z-range':20s}  min={min(zs):.4f}  max={max(zs):.4f}"
              f"  final=({path[-1][0]:.3f}, {path[-1][1]:.3f}, {path[-1][2]:.3f})")

    # Optional grid sample
    if args.grid > 0:
        G = args.grid
        grid_pts = [
            (
                rsvp.lerp(-B, B, ix / max(G - 1, 1)),
                rsvp.lerp(-B, B, iy / max(G - 1, 1)),
                rsvp.lerp(-B, B, iz / max(G - 1, 1)),
            )
            for ix in range(G)
            for iy in range(G)
            for iz in range(G)
        ]
        g_phi = [phi(*p) for p in grid_pts] if phi else []
        g_cl  = [closure(*p) for p in grid_pts] if closure else []
        print(f"\n  Grid samples ({G}³ = {len(grid_pts)}):")
        if g_phi: print_stats("phi",     g_phi)
        if g_cl:  print_stats("closure", g_cl)

    print()


if __name__ == "__main__":
    main()
