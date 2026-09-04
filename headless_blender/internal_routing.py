"""Internal routing: gated ducts carrying separated fractions out of the core.

Renders docs/operating-model.md Section 6.5 ("Routing"): a separator does not
produce useful material until the correct fraction is captured without
cross-contamination, through verified gates, ducts, buffers, and bins. Each
fraction is drawn with its provisional identity tuple

    f_i = (c_i_hat, q_i, sigma_i, U_i)

labeled next to its bin, and each gate is colored to show its recorded state
(open/closed) rather than left ambiguous.

This scene *does* claim an interior view -- the ducts run inside the housing
before they reach the gap -- so, like centerfuge_cutaway.py, it tags roles and
passes interior_objects to finish() so common.verify_visibility empirically
checks that the ducts are visible through the housing's open wedge rather
than merely modeled as if they were.
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *

args = arguments("internal_routing")
scene = begin(args)

shell = material("Routing housing", PALETTE["shell"], metallic=0.3, roughness=0.26)
core_mat = material("Separation core", PALETTE["amber"], metallic=0.2, roughness=0.3, emission=2.0)
gate_open = material("Gate open", PALETTE["green"], emission=2.2)
gate_closed = material("Gate closed", (0.7, 0.1, 0.08, 1.0), emission=1.8)
fraction_mats = [material("Fraction A", PALETTE["cyan"], emission=1.4),
                 material("Fraction B", PALETTE["violet"], emission=1.4),
                 material("Fraction C", PALETTE["green"], emission=1.4)]
duct_mat = material("Duct wall", (0.2, 0.24, 0.28, 1.0), metallic=0.4, roughness=0.3)

body = collection("Routing housing")

housing = open_cylindrical_housing("Open routing housing", 2.6, 2.15, 3.2, shell, body, start_deg=-40, sweep_deg=280)
tag_role(housing, EXTERIOR_SHELL_ROLE)

interior_objects = [tag_role(torus("Separation core", 1.7, 0.18, (0, 0, 0.5), core_mat, collection=body), INTERIOR_ROLE)]

# Fractions f_i, each with a provisional identity tuple. Gates are drawn where
# each duct crosses the housing's inner radius, and colored by a recorded
# open/closed state rather than always shown open -- a gate is a controlled
# boundary, not a decoration.
fractions = (
    {"name": "f1", "class": "polymer", "q": 0.94, "sigma": 0.03, "gate": "open", "angle": -20, "z": 1.6},
    {"name": "f2", "class": "metal", "q": 0.88, "sigma": 0.05, "gate": "open", "angle": 90, "z": 1.9},
    {"name": "f3", "class": "unresolved", "q": 0.41, "sigma": 0.22, "gate": "closed", "angle": 200, "z": 1.4},
)
for i, frac in enumerate(fractions):
    mat = fraction_mats[i % len(fraction_mats)]
    a = math.radians(frac["angle"])
    inner_point = (2.0 * math.cos(a), 2.0 * math.sin(a), frac["z"])
    gate_point = (2.4 * math.cos(a), 2.4 * math.sin(a), frac["z"])
    outer_point = (4.6 * math.cos(a), 4.6 * math.sin(a), frac["z"])

    duct = curve(f"Duct {frac['name']}", (inner_point, gate_point, outer_point), duct_mat, 0.11, collection=body)
    interior_objects.append(tag_role(duct, INTERIOR_ROLE))

    gate_state_mat = gate_open if frac["gate"] == "open" else gate_closed
    bpy.ops.mesh.primitive_cube_add(location=gate_point, scale=(0.16, 0.16, 0.28))
    gate_obj = bpy.context.object
    gate_obj.name = f"Gate {frac['name']} ({frac['gate']})"
    apply(gate_obj, gate_state_mat)
    move_to(gate_obj, body)
    interior_objects.append(tag_role(gate_obj, INTERIOR_ROLE))

    # A re-observation checkpoint: docs/operating-model.md Section 6.5 --
    # "No fraction proceeds merely because its intended bin is full. It
    # proceeds because the batch is re-observed after collection." This
    # sphere is that checkpoint, distinct from the gate itself.
    checkpoint = sphere(f"Checkpoint {frac['name']}", 0.14,
                         ((gate_point[0] + outer_point[0]) / 2, (gate_point[1] + outer_point[1]) / 2, frac["z"]),
                         duct_mat, collection=body)

    bin_obj = cylinder(f"Bin {frac['name']}", 0.55, 0.9, (outer_point[0], outer_point[1], frac["z"] - 0.35), mat, collection=body)
    label(f"{frac['name']}: {frac['class']}  q={frac['q']:.2f}  sigma={frac['sigma']:.2f}  gate={frac['gate']}",
          (outer_point[0], outer_point[1] - 0.7, 0.08), 0.16, mat)

floor(28)
label("SEPARATION CORE / GATED DUCTS / LABELED FRACTIONS", (0, -5.6, 0.08), 0.27)
add_camera((11.5, -14.5, 9.0), (0, 0, 1.5), 58)
add_lighting((3, -7, 10), 1400)
finish(args, interior_objects=interior_objects)
