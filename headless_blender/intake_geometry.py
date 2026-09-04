"""Intake and quarantine geometry: the presentation chamber's admission decision.

This scene renders the four-way intake decision from
docs/operating-model.md Section 6.1:

    D(x) in {ADMIT(p), DIVERT(q), AUDIT, REFUSE}

No object reaches the rotating core directly; everything first enters the
closable presentation/quarantine chamber (safety/service-maintenance.json
SVC-003), which is characterized by the sensor set named in the same section
(mass, dimension, moisture, magnetic response, electrical activity, and
imaging). This scene does not claim to expose anything hidden behind the
chamber wall -- it is a schematic of the decision and its sensors, not a
cutaway -- so it calls finish() without interior_objects and is exempt from
the non-occlusion check by construction, not by omission.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *

args = arguments("intake_geometry")
scene = begin(args)

chamber_mat = material("Presentation chamber", PALETTE["shell"], metallic=0.3, roughness=0.28)
sensor_mat = material("Sensor lead", PALETTE["paper"], roughness=0.5, emission=0.4)
decision_mats = {
    "ADMIT": material("Admit", PALETTE["green"], emission=1.6),
    "DIVERT": material("Divert", PALETTE["violet"], emission=1.6),
    "AUDIT": material("Audit", PALETTE["cyan"], emission=1.6),
    "REFUSE": material("Refuse", PALETTE["amber"], emission=1.6),
}

body = collection("Intake chamber")

# The chamber itself: a closable box, not a cutaway. Its geometry is a plain
# beveled cube because this scene's epistemic claim is only "here is a
# closable chamber with these sensors and these four exits" -- not "here is
# what the chamber's mechanism looks like inside."
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 1.1), scale=(1.6, 1.6, 1.1))
chamber = bpy.context.object
chamber.name = "Presentation and quarantine chamber"
apply(chamber, chamber_mat)
move_to(chamber, body)
bevel = chamber.modifiers.new("Chamber edges", "BEVEL")
bevel.width = 0.05
bevel.segments = 2
label("PRESENTATION / QUARANTINE", (0, -2.0, 0.08), 0.22)

# Sensors named in operating-model.md Section 6.1, arranged around the
# chamber and connected by a labeled lead so the render can be read as a
# wiring/observation diagram rather than decoration.
sensors = (
    ("MASS", (-2.6, -1.6, 1.9)),
    ("DIMENSION", (2.6, -1.6, 1.9)),
    ("MOISTURE", (-2.6, 1.6, 1.9)),
    ("MAGNETIC", (2.6, 1.6, 1.9)),
    ("ELECTRICAL", (-2.6, 0.0, 2.9)),
    ("IMAGING", (2.6, 0.0, 2.9)),
)
for text, location in sensors:
    sphere(f"Sensor {text}", 0.18, location, sensor_mat, collection=body)
    curve(f"Lead {text}", (location, (location[0] * 0.35, location[1] * 0.35, 1.6)), sensor_mat, 0.02, collection=body)
    label(text, (location[0], location[1] - 0.3, location[2] - 0.35), 0.16, sensor_mat)

# The four-way decision. Each path is labeled with the exact predicate name
# used in the operating model so the render and the spec cannot drift apart.
decisions = (
    ("ADMIT(p)", (-5.2, -4.8, 0.5), "ADMIT"),
    ("DIVERT(q)", (5.2, -4.8, 0.5), "DIVERT"),
    ("AUDIT", (-5.2, 4.8, 0.5), "AUDIT"),
    ("REFUSE", (5.2, 4.8, 0.5), "REFUSE"),
)
for text, end, key in decisions:
    mat = decision_mats[key]
    start = (0, 0, 0.6)
    mid = (end[0] * 0.5, end[1] * 0.5, 0.55)
    curve(f"Path {key}", (start, mid, end), mat, 0.09, collection=body)
    sphere(f"Terminal {key}", 0.42, end, mat, collection=body)
    label(text, (end[0], end[1] - 0.7, 0.08), 0.28, mat)

floor(30)
label("INTAKE / ADMIT, DIVERT, AUDIT, OR REFUSE", (0, -6.4, 0.08), 0.3)
add_camera((14.0, -18.5, 13.5), (0, 0, 1.7), 55)
add_lighting((3, -8, 13), 1500)
finish(args)
