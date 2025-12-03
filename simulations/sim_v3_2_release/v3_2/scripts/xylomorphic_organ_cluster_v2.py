import bpy
import math
import random
import mathutils

# Clear meshes/curves
for obj in list(bpy.context.scene.objects):
    if obj.type in {'MESH', 'CURVE'}:
        bpy.data.objects.remove(obj, do_unlink=True)

random.seed(123)

def make_trunk(root_loc, height=7.0, radius=0.6):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=(root_loc[0], root_loc[1], height/2))
    trunk = bpy.context.active_object
    trunk.name = "Organ_Trunk"
    mat = bpy.data.materials.new("Mat_Trunk")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.18, 0.35, 0.22, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.8
    trunk.data.materials.append(mat)
    return trunk

def make_branch(start, end):
    curve_data = bpy.data.curves.new("Organ_Branch", 'CURVE')
    curve_data.dimensions = '3D'
    spline = curve_data.splines.new('BEZIER')
    spline.bezier_points.add(2)
    pts = spline.bezier_points
    pts[0].co = start
    pts[1].co = (start + end) / 2 + mathutils.Vector((0,0,1.5))
    pts[2].co = end
    for p in pts:
        p.handle_left_type = p.handle_right_type = 'AUTO'
    curve_data.bevel_depth = 0.08
    obj = bpy.data.objects.new("Organ_Branch", curve_data)
    bpy.context.scene.collection.objects.link(obj)

    mat = bpy.data.materials.new("Mat_Branch")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.3, 0.6, 0.35, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.5
    curve_data.materials.append(mat)
    return obj

def make_hub(loc):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.8, location=loc)
    hub = bpy.context.active_object
    hub.name = "Organ_Hub"
    mat = bpy.data.materials.new("Mat_Hub")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Emission"].default_value = (0.25, 0.9, 0.7, 1.0)
    bsdf.inputs["Emission Strength"].default_value = 6.0
    hub.data.materials.append(mat)
    return hub

# cluster of 3 trunks
trunks = []
roots = [(-4, 0, 0), (4, 0, 0), (0, -5, 0)]
for r in roots:
    trunks.append(make_trunk(r, height=random.uniform(6.0, 9.0)))

hubs = []
for t in trunks:
    top = t.location + mathutils.Vector((0, 0, t.dimensions.z/2))
    for _ in range(3):
        offset = mathutils.Vector((random.uniform(-2,2), random.uniform(-2,2), random.uniform(1,3)))
        h = make_hub(top + offset)
        hubs.append(h)
        make_branch(top, h.location)

# some cross-branches between hubs
for i in range(0, len(hubs), 2):
    if i+1 < len(hubs):
        make_branch(hubs[i].location, hubs[i+1].location)

print("[v3.2] Xylomorphic organ cluster v2 created.")
