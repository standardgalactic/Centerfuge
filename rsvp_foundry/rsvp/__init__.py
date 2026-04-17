"""
rsvp — RSVP field and operator suite for procedural geometry.

Public API is flat: import what you need directly from rsvp.
"""

from .vec import (
    Vec3,
    v_add, v_sub, v_mul, v_dot, v_cross,
    v_length, v_normalize,
    lerp, smoothstep, sigmoid,
)
from .fields import (
    ScalarFn, VectorFn,
    Basin, DirectionalBias, HarmonicField, EntropyCap,
)
from .operators import (
    add_scalar_fields, mul_scalar_fields, add_vector_fields,
    scalar_gradient, divergence, curl,
    closure_field, capped_field,
)
from .sampling import GridSpec, sample_scalar_grid, seed_points_from_field
from .terrain import sample_height_map, terrain_field, residue_profile, tower_radius
from .growth import trace_growth_path, branch_paths
from .seams import seam_displacement, seam_obstruction_metric
from .presets import (
    make_default_rsvp_field,
    make_tree_operators,
    make_landscape_operators,
    make_seam_operators,
)

__all__ = [
    "Vec3", "ScalarFn", "VectorFn",
    "v_add", "v_sub", "v_mul", "v_dot", "v_cross",
    "v_length", "v_normalize", "lerp", "smoothstep", "sigmoid",
    "Basin", "DirectionalBias", "HarmonicField", "EntropyCap",
    "add_scalar_fields", "mul_scalar_fields", "add_vector_fields",
    "scalar_gradient", "divergence", "curl",
    "closure_field", "capped_field",
    "GridSpec", "sample_scalar_grid", "seed_points_from_field",
    "sample_height_map", "terrain_field", "residue_profile", "tower_radius",
    "trace_growth_path", "branch_paths",
    "seam_displacement", "seam_obstruction_metric",
    "make_default_rsvp_field", "make_tree_operators",
    "make_landscape_operators", "make_seam_operators",
]
