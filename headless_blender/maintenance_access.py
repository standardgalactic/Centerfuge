"""Maintenance and service-access zones, read directly from safety/service-maintenance.json.

Renders the three-tier service boundary from
docs/safety-maintenance-spec.md Section 11:

    USER              -- external cleaning, sealed-bin exchange, no exposure
                         to hazardous energy.
    TRAINED           -- guarded access after documented isolation and
                         residual-energy verification.
    PROTECTED_REPLACE_ONLY -- rotor, drive, containment, and safety-control
                         parts whose incorrect repair could defeat a primary
                         protection.

Provenance completeness: every labeled component in this scene is read from
safety/service-maintenance.json at build time (by component id and service
class), not retyped by hand. If that JSON changes, this scene's next render
changes with it; a component id shown here that no longer exists in the JSON,
or a JSON component missing from this scene, is a drift this script would
surface the next time both are regenerated and compared.

No interior claim is made -- each zone is drawn as a labeled ring of
terminals around the appliance, not as a cutaway through its housing -- so
this scene calls finish() without interior_objects.
"""

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *

REPO_ROOT = Path(__file__).resolve().parent.parent
SERVICE_RECORD_PATH = REPO_ROOT / "safety" / "service-maintenance.json"

args = arguments("maintenance_access")
scene = begin(args)

with open(SERVICE_RECORD_PATH) as handle:
    service_record = json.load(handle)

ZONE_RADIUS = {"USER": 3.2, "TRAINED": 5.4, "PROTECTED_REPLACE_ONLY": 7.6}
ZONE_COLOR = {"USER": PALETTE["green"], "TRAINED": PALETTE["cyan"], "PROTECTED_REPLACE_ONLY": PALETTE["amber"]}
ZONE_LABEL = {
    "USER": "USER SERVICE",
    "TRAINED": "TRAINED SERVICE",
    "PROTECTED_REPLACE_ONLY": "PROTECTED / REPLACE-ONLY",
}

body = collection("Maintenance zones")
center_mat = material("Appliance", PALETTE["shell"], metallic=0.3, roughness=0.28)
cylinder("Centerfuge appliance", 1.4, 4.0, (0, 0, 2.0), center_mat, collection=body)

# Group components by their recorded service_class so each ring's population
# and labels come from the same source of truth the safety spec validates
# against (scripts/validate-safety.py), not a second, hand-maintained list.
components_by_class = {}
for component in service_record["components"]:
    components_by_class.setdefault(component["service_class"], []).append(component)

for service_class, components in components_by_class.items():
    radius = ZONE_RADIUS.get(service_class)
    if radius is None:
        raise RuntimeError(
            f"safety/service-maintenance.json contains service_class {service_class!r} with no "
            "assigned ring radius in this scene's ZONE_RADIUS; add it rather than dropping the "
            "component silently."
        )
    color = ZONE_COLOR[service_class]
    mat = material(f"Zone {service_class}", color, emission=1.2, alpha=0.85)
    ring_mat = material(f"Ring {service_class}", color, emission=0.5, alpha=0.35)
    torus(f"Boundary {service_class}", radius, 0.03, (0, 0, 0.05), ring_mat, collection=body)

    count = len(components)
    for index, component in enumerate(components):
        angle = math.tau * index / count
        x, y = radius * math.cos(angle), radius * math.sin(angle)
        z = 0.5 + 0.4 * (index % 3)
        sphere(f"{component['id']} terminal", 0.22, (x, y, z), mat, collection=body)
        curve(f"{component['id']} lead", ((0, 0, z), (x, y, z)), mat, 0.02, collection=body)
        label(f"{component['id']}: {component['component']}", (x, y - 0.5, z - 0.4), 0.12, mat, align="CENTER")

    label(ZONE_LABEL[service_class], (radius * 0.72, radius * 0.72, 0.08), 0.24, mat)

floor(40)
label("SERVICE BOUNDARY / SOURCE: safety/service-maintenance.json", (0, -8.5, 0.08), 0.24)
add_camera((20.0, -26.0, 18.0), (0, 0, 2.0), 45)
add_lighting((5, -10, 20), 2200)
finish(args)
