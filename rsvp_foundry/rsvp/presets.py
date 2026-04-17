"""
Preset builders. Each returns a dict of named field objects ready for use
in a headless bpy script.

These are starting points, not final configurations. Compose your own
fields from the primitives when a preset's defaults don't match the asset.
"""

from __future__ import annotations

from .fields import Basin, DirectionalBias, HarmonicField, EntropyCap
from .fields import ScalarFn, VectorFn
from .operators import (
    add_scalar_fields, add_vector_fields,
    scalar_gradient, closure_field, capped_field,
)
from .terrain import terrain_field
from .seams import seam_displacement, seam_obstruction_metric


def make_default_rsvp_field() -> tuple[ScalarFn, VectorFn, ScalarFn]:
    """phi, v_field, closure — a general-purpose coupled field triple."""
    phi = add_scalar_fields(
        Basin(center=(0.0, 0.0, 0.0), amplitude=1.2, radius=1.4).scalar(),
        HarmonicField(weights=(0.6, 0.8, 0.3), frequencies=(2.0, 3.0, 4.0), amplitude=0.35).scalar(),
    )
    v_field = add_vector_fields(
        DirectionalBias(direction=(1.0, 0.2, 0.0), strength=0.8, curl=0.35).vector(),
    )
    closure = capped_field(
        closure_field(phi, v_field),
        EntropyCap(threshold=1.0, softness=5.0),
    )
    return phi, v_field, closure


def make_tree_operators() -> dict[str, object]:
    """
    Upward-biased field set for tree trunk and branch generation.

    Note: the gradient of phi is intentionally NOT added to v_field here.
    Near the basin center the gradient is near-zero, which would weaken the
    vertical trunk bias precisely where it should be strongest. If you want
    canopy-attraction behaviour, blend scalar_gradient(phi) in manually with
    a small weight (0.1–0.2) only in the branch phase, not the trunk phase.
    """
    phi = add_scalar_fields(
        Basin(center=(0.0, 0.0, 0.2), amplitude=1.0, radius=1.0).scalar(),
        HarmonicField(weights=(0.2, 0.2, 0.8), frequencies=(1.5, 1.8, 3.5), amplitude=0.2).scalar(),
    )
    v_field = DirectionalBias(direction=(0.0, 0.0, 1.0), strength=1.0, curl=0.25).vector()
    return {
        "phi": phi,
        "v_field": v_field,
        "closure": closure_field(phi, v_field),
        "grad_phi": scalar_gradient(phi),   # expose for optional branch attraction
    }


def make_landscape_operators() -> dict[str, object]:
    basin = Basin(center=(0.0, 0.0, 0.0), amplitude=1.1, radius=1.8)
    harmonic = HarmonicField(weights=(1.0, 0.8, 0.0), frequencies=(1.2, 2.6, 0.0), amplitude=0.4)
    directional = DirectionalBias(direction=(1.0, 0.25, 0.0), strength=0.6, curl=0.15)
    cap = EntropyCap(threshold=1.2, softness=4.5)
    return {
        "terrain": terrain_field(basin, harmonic, directional, cap),
        "direction": directional.vector(),
    }


def make_seam_operators() -> dict[str, object]:
    return {
        "displace": seam_displacement,
        "metric": seam_obstruction_metric,
    }
