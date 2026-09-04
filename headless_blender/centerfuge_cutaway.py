"""Cutaway model of the domestic Centerfuge appliance."""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *

args = arguments("centerfuge_cutaway")
scene = begin(args)

shell = material("Ceramic housing", PALETTE["shell"], metallic=0.35, roughness=0.24)
edge = material("Cyan field", PALETTE["cyan"], metallic=0.15, roughness=0.22, emission=3.0)
hot = material("Hyperbolator", PALETTE["amber"], metallic=0.1, roughness=0.3, emission=2.5)
matter = [material("Organic", PALETTE["green"], emission=0.5),
          material("Mineral", PALETTE["cyan"], emission=0.5),
          material("Polymer", PALETTE["violet"], emission=0.5)]

body = collection("Housing and rotors")

housing = open_cylindrical_housing("Open ceramic housing", 3.35, 2.85, 6.0, shell, body)
tag_role(housing, EXTERIOR_SHELL_ROLE)

interior_objects = []
for z, radius in ((0.35, 2.75), (1.7, 2.35), (3.05, 1.95), (4.4, 1.55), (5.65, 1.15)):
    interior_objects.append(tag_role(torus(f"Rotor {z:.2f}", radius, 0.09, (0, 0, z), edge, collection=body), INTERIOR_ROLE))
    for arm in range(4):
        a = arm * math.pi / 2 + z * 0.3
        spoke = curve("Rotor spoke", ((0, 0, z), (radius * math.cos(a), radius * math.sin(a), z)), edge, 0.035, collection=body)
        interior_objects.append(tag_role(spoke, INTERIOR_ROLE))

interior_objects.append(tag_role(cylinder("Hyperbolation spindle", 0.34, 5.2, (0, 0, 3.0), hot, collection=body), INTERIOR_ROLE))
for i in range(45):
    z = 0.55 + i * 0.11
    radius = 2.55 - 0.27 * z
    angle = i * 0.9
    packet = sphere(f"Material packet {i:02d}", 0.09 + (i % 3) * 0.025,
                     (radius * math.cos(angle), radius * math.sin(angle), z), matter[i % 3], collection=body)
    interior_objects.append(tag_role(packet, INTERIOR_ROLE))


floor()
label("CENTERFUGE / DOMESTIC MATERIAL ORGAN", (0, -4.2, 0.08), 0.27)
add_camera((13.5, -16.5, 10.5), (0, 0, 2.65), 58)
add_lighting()
# Non-occlusion invariant (see common.verify_visibility): this scene's name and
# label claim a "cutaway" that exposes the rotor stack and hyperbolation
# spindle. That claim is admissible only if those interior_objects are proven
# reachable by an unobstructed camera ray through the housing's open wedge --
# not merely because the housing was authored with an opening. finish() raises
# if fewer than 60% of sampled interior points are actually visible, which
# would mean the "cutaway" is really an opaque occluder placed out of frame.
finish(args, interior_objects=interior_objects)
