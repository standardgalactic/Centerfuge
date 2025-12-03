import bpy
import math
import mathutils

# Clear meshes & curves
for obj in list(bpy.context.scene.objects):
    if obj.type in {"MESH", "CURVE"}:
        bpy.data.objects.remove(obj, do_unlink=True)

def plenum_cell_at(loc, name_prefix, hue_shift=0.0):
    # Simple variant of plenum cell: core + halo + a short ribbon
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=loc)
    core = bpy.context.active_object
    core.name = f"{name_prefix}_Phi"
    mat = bpy.data.materials.new(f"Mat_{name_prefix}_Phi")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Emission"].default_value = (0.3 + hue_shift, 0.8, 1.0 - hue_shift, 1.0)
    bsdf.inputs["Emission Strength"].default_value = 5.0
    core.data.materials.append(mat)

    # small halo of points
    for i in range(20):
        ang = 2*math.pi * i / 20
        r = 1.6
        x = loc[0] + r*math.cos(ang)
        y = loc[1] + r*math.sin(ang)
        z = loc[2] + 0.2*math.sin(4*ang)
        bpy.ops.mesh.primitive_ico_sphere_add(radius=0.12, location=(x,y,z))
        h = bpy.context.active_object
        h.name = f"{name_prefix}_halo_{i}"
        hmat = bpy.data.materials.new(f"Mat_{name_prefix}_halo_{i}")
        hmat.use_nodes = True
        hbsdf = hmat.node_tree.nodes["Principled BSDF"]
        hbsdf.inputs["Emission"].default_value = (1.0, 0.4+hue_shift, 0.4, 1.0)
        hbsdf.inputs["Emission Strength"].default_value = 4.0
        h.data.materials.append(hmat)

    return core

# Triangle positions
r = 6.0
positions = [
    (0.0, r, 0.0),
    (-5.5, -3.0, 0.0),
    (5.5, -3.0, 0.0),
]

cells = []
for idx, pos in enumerate(positions):
    cells.append(plenum_cell_at(pos, f"Cell{idx}", hue_shift=0.2*idx))

# Connect cells with curves (lamphrodynamic filaments)
pairs = [(0,1), (1,2), (2,0)]
for idx, (a, b) in enumerate(pairs):
    p0 = mathutils.Vector(positions[a])
    p1 = mathutils.Vector(positions[b])
    mid = (p0 + p1) / 2
    mid.z += 2.0

    pts = [p0, mid, p1]
    curve_data = bpy.data.curves.new(f"Link_{idx}", 'CURVE')
    curve_data.dimensions = '3D'
    spline = curve_data.splines.new('POLY')
    spline.points.add(2)
    for i, p in enumerate(pts):
        spline.points[i].co = (p[0], p[1], p[2], 1.0)
    curve_data.bevel_depth = 0.12
    curve_obj = bpy.data.objects.new(f"Link_{idx}", curve_data)
    bpy.context.scene.collection.objects.link(curve_obj)

    m = bpy.data.materials.new(f"Mat_Link_{idx}")
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Emission"].default_value = (0.5, 0.9, 1.0, 1.0)
    bsdf.inputs["Emission Strength"].default_value = 7.0
    curve_data.materials.append(m)

print("[v3.2] Three-cell RSVP lattice created.")
