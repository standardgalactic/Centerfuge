import bpy
import random
import math
import mathutils

# Xylomorphic City / Organ (static)
# - Ring of trunk towers + canopy spheres.

# Clear previous meshes/curves
for obj in list(bpy.context.scene.objects):
    if obj.type in {'MESH', 'CURVE'}:
        bpy.data.objects.remove(obj, do_unlink=True)

def create_trunk(location, height=8.0, radius=0.8):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=(location[0], location[1], height / 2.0))
    trunk = bpy.context.active_object
    trunk.name = "Xylo_Trunk"
    mat = bpy.data.materials.new("Mat_Xylo_Trunk")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.15, 0.4, 0.2, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.7
    trunk.data.materials.append(mat)
    return trunk

def create_canopy(location, radius=1.4):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=location)
    hub = bpy.context.active_object
    hub.name = "Xylo_Hub"
    mat = bpy.data.materials.new("Mat_Xylo_Hub")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Emission"].default_value = (0.2, 0.9, 0.6, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 7.0
    hub.data.materials.append(mat)
    return hub

random.seed(42)
num_trunks = 6
radius_ring = 10.0

for i in range(num_trunks):
    angle = 2.0 * math.pi * i / num_trunks
    x = radius_ring * math.cos(angle)
    y = radius_ring * math.sin(angle)
    height = random.uniform(7.0, 11.0)
    trunk = create_trunk((x, y), height=height)

    top = trunk.location + mathutils.Vector((0.0, 0.0, height / 2.0))
    for _ in range(3):
        offset = mathutils.Vector((random.uniform(-2, 2),
                                   random.uniform(-2, 2),
                                   random.uniform(0.0, 3.0)))
        create_canopy(top + offset)

print("[v3.1] Xylomorphic city (static) created.")
