"""Exploded scientific model of a gnotobiotic hyperball/cognet."""

import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *

args = arguments("hyperbolation_cognet")
begin(args)

core_mat = material("Material core", PALETTE["amber"], metallic=0.1, roughness=0.55, emission=0.7)
fiber_mats = [material("Identity yarn", PALETTE["cyan"], roughness=0.38, emission=1.1),
              material("Provenance yarn", PALETTE["violet"], roughness=0.38, emission=1.1),
              material("Compatibility yarn", PALETTE["green"], roughness=0.38, emission=1.1)]
membrane = material("Sterile membrane", (0.32, 0.7, 0.85, 1), roughness=0.18, alpha=0.18)

sphere("Recovered material", 1.05, (0, 0, 2.7), core_mat)
for layer in range(3):
    radius = 1.25 + layer * 0.38
    mat = fiber_mats[layer]
    for strand in range(10):
        points = []
        phase = strand * math.tau / 10
        tilt = (strand % 5 - 2) * 0.13
        for j in range(90):
            u = math.pi * j / 89
            v = phase + 5.5 * u + tilt * math.sin(3 * u)
            points.append((radius * math.sin(u) * math.cos(v),
                           radius * math.sin(u) * math.sin(v),
                           2.7 + radius * math.cos(u)))
        curve(f"Layer {layer + 1} strand {strand}", points, mat, 0.025 + layer * 0.006)

sphere("Gnotobiotic envelope", 2.32, (0, 0, 2.7), membrane)
for angle, text, z, mat in ((-0.72, "IDENTITY", 3.8, fiber_mats[0]),
                            (-0.18, "PROVENANCE", 2.8, fiber_mats[1]),
                            (0.42, "COMPATIBILITY", 1.8, fiber_mats[2])):
    start = (2.0 * math.cos(angle), -2.0, z)
    curve(f"Callout {text}", (start, (4.0, -2.0, z)), mat, 0.025)
    label(text, (4.2, -2.0, z), 0.28, mat, rotation=(math.pi / 2, 0, 0), align="LEFT")

floor(24)
label("COGNET / MATERIAL PLUS RECOVERABLE HISTORY", (0, -4.0, 0.08), 0.27)
add_camera((13.5, -17.0, 9.5), (0, 0, 2.45), 58)
add_lighting((3, -6, 11), 1600)
finish(args)
