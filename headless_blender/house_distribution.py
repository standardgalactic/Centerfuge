"""House-scale visualization of repair, food, clothing, and recovery flows."""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *

args = arguments("house_distribution")
begin(args)

wall = material("House structure", (0.11, 0.15, 0.18, 1), metallic=0.05, roughness=0.55)
center = material("Centerfuge", PALETTE["amber"], metallic=0.25, roughness=0.25, emission=2.2)
flows = [material("Repair flow", PALETTE["cyan"], emission=1.4),
         material("Food flow", PALETTE["green"], emission=1.4),
         material("Clothing flow", PALETTE["violet"], emission=1.4),
         material("Recovery flow", PALETTE["amber"], emission=1.4)]

# A roofless dollhouse: slab, perimeter walls, and four rooms.
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0.15), scale=(6.2, 5.0, 0.15))
apply(bpy.context.object, wall)
for location, scale in (((0, 5, 1.6), (6.3, 0.12, 1.6)), ((0, -5, 1.6), (6.3, 0.12, 1.6)),
                        ((6.2, 0, 1.6), (0.12, 5.0, 1.6)), ((-6.2, 0, 1.6), (0.12, 5.0, 1.6)),
                        ((0, 2.8, 1.1), (4.3, 0.08, 1.1)), ((0, -2.8, 1.1), (4.3, 0.08, 1.1))):
    bpy.ops.mesh.primitive_cube_add(location=location, scale=scale)
    apply(bpy.context.object, wall)

cylinder("Domestic Centerfuge", 1.0, 4.2, (0, 0, 2.25), center)
for z in (0.8, 1.7, 2.6, 3.5):
    torus("Centerfuge rotor", 1.15, 0.055, (0, 0, z), flows[int(z) % 4])

destinations = ((-4.6, 3.8, 1.1, "REPAIR"), (4.6, 3.8, 1.1, "FOOD"),
                (4.6, -3.8, 1.1, "CLOTHING"), (-4.6, -3.8, 1.1, "RECOVERY"))
for index, (x, y, z, name) in enumerate(destinations):
    points = ((0, 0, 1.4 + index * 0.48), (x * 0.35, y * 0.35, 0.6), (x, y, z))
    curve(f"{name.title()} conduit", points, flows[index], 0.11)
    sphere(f"{name.title()} terminal", 0.42, (x, y, z), flows[index])
    label(name, (x, y - 0.55, 0.35), 0.3, flows[index])
    for packet in range(6):
        t = (packet + 1) / 7
        px = x * t
        py = y * t
        pz = (1.4 + index * 0.48) * (1 - t) + z * t - 0.35 * math.sin(math.pi * t)
        sphere(f"{name.title()} packet {packet}", 0.08, (px, py, pz), flows[index])

label("A HOUSE WITH A MATERIAL METABOLISM", (0, -5.45, 0.08), 0.31)
add_camera((14.5, -19.0, 16.5), (0, 0, 1.15), 53)
add_lighting((4, -6, 16), 1800)
finish(args)
