"""Particle-like visualization of rotation, classification, and radial routing."""

import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *

args = arguments("material_sorting_vortex")
begin(args)

colors = (PALETTE["green"], PALETTE["cyan"], PALETTE["violet"], PALETTE["amber"])
mats = [material(f"Class {i}", c, roughness=0.3, emission=1.4) for i, c in enumerate(colors)]
guide = material("Field guide", (0.1, 0.2, 0.28, 1), metallic=0.3, roughness=0.25, emission=0.6)

for lane in range(7):
    points = []
    phase = lane * 0.82
    for step in range(70):
        t = step / 69
        r = 0.3 + 4.7 * t
        a = phase + t * math.tau * 2.35
        points.append((r * math.cos(a), r * math.sin(a), 0.5 + t * 4.7))
    curve(f"Vortex trajectory {lane}", points, mats[lane % 4], 0.032)

for i in range(120):
    cls = i % 4
    t = random.random()
    radius = 0.4 + 4.4 * t
    angle = cls * math.pi / 2 + t * math.tau * 2.3 + random.gauss(0, 0.13)
    z = 0.55 + 4.6 * t + random.gauss(0, 0.08)
    sphere(f"Packet {i:03d} class {cls}", 0.065 + random.random() * 0.07,
           (radius * math.cos(angle), radius * math.sin(angle), z), mats[cls])

for i, mat in enumerate(mats):
    angle = i * math.pi / 2
    start = (4.5 * math.cos(angle), 4.5 * math.sin(angle), 4.9)
    end = (7.0 * math.cos(angle), 7.0 * math.sin(angle), 4.9)
    curve(f"Sorted output {i}", (start, end), mat, 0.12)
    cylinder(f"Output bin {i}", 0.75, 0.75, (end[0], end[1], 4.55), mat)

for r in (1.5, 3.0, 4.5):
    torus(f"Classification radius {r}", r, 0.025, (0, 0, 0.45 + r), guide)
floor(32)
label("UNSORTED INPUT  →  ROTATION  →  LABELED OUTPUT", (0, -5.8, 0.08), 0.29)
add_camera((15.0, -20.0, 15.0), (0, 0, 2.7), 55)
add_lighting((4, -8, 14), 1500)
finish(args)
