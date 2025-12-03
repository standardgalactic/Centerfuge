import bpy
import math

# Delta–Sigma Cognitive Modulators (static)
# - Four curved edges with varying thickness and brightness to suggest bitstreams.

# Clear meshes and curves
for obj in list(bpy.context.scene.objects):
    if obj.type in {'MESH', 'CURVE'}:
        bpy.data.objects.remove(obj, do_unlink=True)

def make_curve(name, points, color, thickness):
    curve_data = bpy.data.curves.new(name, type='CURVE')
    curve_data.dimensions = '3D'
    spline = curve_data.splines.new('POLY')
    spline.points.add(len(points) - 1)
    for idx, p in enumerate(points):
        spline.points[idx].co = (p[0], p[1], p[2], 1.0)
    curve_data.bevel_depth = thickness
    curve_obj = bpy.data.objects.new(name, curve_data)

    mat = bpy.data.materials.new(f"Mat_{name}")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Emission"].default_value = color
        bsdf.inputs["Emission Strength"].default_value = 6.0
        bsdf.inputs["Base Color"].default_value = color
    curve_data.materials.append(mat)

    bpy.context.scene.collection.objects.link(curve_obj)
    return curve_obj

# Create 4 arcs around origin
r = 6.0
for i in range(4):
    a0 = i * (math.pi / 2.0)
    a1 = a0 + math.pi / 2.0
    mid = (a0 + a1) / 2.0
    pts = [
        (r * math.cos(a0), r * math.sin(a0), 1.0),
        (r * math.cos(mid), r * math.sin(mid), 2.0),
        (r * math.cos(a1), r * math.sin(a1), 1.0),
    ]
    color = (
        0.5 + 0.5 * math.cos(a0),
        0.5 + 0.5 * math.sin(a0),
        0.7,
        1.0,
    )
    thickness = 0.05 + 0.03 * i
    make_curve(f"DS_Arc_{i}", pts, color, thickness)

print("[v3.1] Delta–sigma static arcs created.")
