import bpy
import math
import mathutils
import random

"""Xylomorphic City / Organ Generator
--------------------------------------
Generates a forest-like / organ-like city:
  - trunk towers (macro organs)
  - branch streets
  - canopy nodes (hubs)
Intended to visualize xylomorphic architecture and RSVP-style entropy flows.
"""

random.seed(42)

CITY_COLL_NAME = "XyloCity_v3"


def clear_collection(name):
    if name in bpy.data.collections:
        coll = bpy.data.collections[name]
        for obj in list(coll.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(coll)


def ensure_collection(name):
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    return coll


def create_trunk(location, height, radius, coll):
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=height, location=location)
    obj = bpy.context.active_object
    obj.location.z = height * 0.5
    obj["xylo_role"] = "trunk"
    obj["entropy_sink"] = random.uniform(0.3, 1.0)

    mat = bpy.data.materials.new("Xylo_Trunk_Mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.15, 0.4, 0.2, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.7
    obj.data.materials.append(mat)

    for c in obj.users_collection:
        c.objects.unlink(obj)
    coll.objects.link(obj)

    return obj


def create_branch(start, end, coll):
    curve_data = bpy.data.curves.new("Xylo_Branch", type='CURVE')
    curve_data.dimensions = '3D'
    spline = curve_data.splines.new('POLY')
    spline.points.add(1)
    spline.points[0].co = (*start, 1.0)
    spline.points[1].co = (*end, 1.0)
    curve_data.bevel_depth = 0.06
    curve_obj = bpy.data.objects.new("Branch", curve_data)
    curve_obj["xylo_role"] = "branch"
    for c in curve_obj.users_collection:
        c.objects.unlink(curve_obj)
    coll.objects.link(curve_obj)
    return curve_obj


def create_canopy_node(location, coll):
    bpy.ops.mesh.primitive_ico_sphere_add(radius=0.4, location=location)
    hub = bpy.context.active_object
    hub["xylo_role"] = "canopy_hub"
    hub["metabolic_rate"] = random.uniform(0.2, 1.2)

    mat = bpy.data.materials.new("Xylo_Hub_Mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Emission"].default_value = (0.2, 0.9, 0.6, 1.0)
    bsdf.inputs["Emission Strength"].default_value = 5.0 * hub["metabolic_rate"]
    hub.data.materials.append(mat)

    for c in hub.users_collection:
        c.objects.unlink(hub)
    coll.objects.link(hub)
    return hub


def generate_city():
    clear_collection(CITY_COLL_NAME)
    coll = ensure_collection(CITY_COLL_NAME)

    num_trunks = 7
    trunks = []
    for i in range(num_trunks):
        angle = (2 * math.pi * i) / num_trunks
        r = 8.0
        x = r * math.cos(angle)
        y = r * math.sin(angle)
        height = random.uniform(5.0, 11.0)
        trunk = create_trunk((x, y, 0.0), height, radius=0.6, coll=coll)
        trunks.append(trunk)

    # central trunk / brainstem
    center_trunk = create_trunk((0.0, 0.0, 0.0), height=14.0, radius=1.2, coll=coll)
    trunks.append(center_trunk)

    hubs = []
    for trunk in trunks:
        top_loc = trunk.location + mathutils.Vector((0.0, 0.0, trunk.dimensions.z * 0.5))
        for k in range(random.randint(2, 4)):
            offset = mathutils.Vector((random.uniform(-2, 2), random.uniform(-2, 2), random.uniform(1.0, 3.0)))
            hub = create_canopy_node(top_loc + offset, coll)
            hubs.append(hub)
            create_branch(top_loc, hub.location, coll)

    print("[XyloCity] Generated trunks, branches, and canopy hubs.")
    return coll


if __name__ == "__main__":
    generate_city()
