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


def open_cylindrical_housing(name, outer_radius, inner_radius, height, mat, segments=72):
    """Create a thick 270-degree shell with its open wedge facing the camera."""
    start = math.radians(-45)
    sweep = math.radians(270)
    vertices = []
    faces = []
    for index in range(segments + 1):
        angle = start + sweep * index / segments
        c, s = math.cos(angle), math.sin(angle)
        vertices.extend(((outer_radius * c, outer_radius * s, 0),
                         (outer_radius * c, outer_radius * s, height),
                         (inner_radius * c, inner_radius * s, 0),
                         (inner_radius * c, inner_radius * s, height)))
    for index in range(segments):
        a, b = index * 4, (index + 1) * 4
        faces.extend(((a, b, b + 1, a + 1),
                      (a + 3, b + 3, b + 2, a + 2),
                      (a + 1, b + 1, b + 3, a + 3),
                      (a + 2, b + 2, b, a)))
    last = segments * 4
    faces.extend(((0, 1, 3, 2), (last + 2, last + 3, last + 1, last)))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    body.objects.link(obj)
    apply(obj, mat)
    bevel = obj.modifiers.new("Soft housing edges", "BEVEL")
    bevel.width = 0.045
    bevel.segments = 2
    return obj


open_cylindrical_housing("Open ceramic housing", 3.35, 2.85, 6.0, shell)
for z, radius in ((0.35, 2.75), (1.7, 2.35), (3.05, 1.95), (4.4, 1.55), (5.65, 1.15)):
    torus(f"Rotor {z:.2f}", radius, 0.09, (0, 0, z), edge, collection=body)
    for arm in range(4):
        a = arm * math.pi / 2 + z * 0.3
        curve("Rotor spoke", ((0, 0, z), (radius * math.cos(a), radius * math.sin(a), z)), edge, 0.035, collection=body)

cylinder("Hyperbolation spindle", 0.34, 5.2, (0, 0, 3.0), hot, collection=body)
for i in range(45):
    z = 0.55 + i * 0.11
    radius = 2.55 - 0.27 * z
    angle = i * 0.9
    sphere(f"Material packet {i:02d}", 0.09 + (i % 3) * 0.025,
           (radius * math.cos(angle), radius * math.sin(angle), z), matter[i % 3], collection=body)

floor()
label("CENTERFUGE / DOMESTIC MATERIAL ORGAN", (0, -4.2, 0.08), 0.27)
add_camera((13.5, -16.5, 10.5), (0, 0, 2.65), 58)
add_lighting()
finish(args)
