import bpy

# Clear meshes/curves
for obj in list(bpy.context.scene.objects):
    if obj.type in {'MESH', 'CURVE'}:
        bpy.data.objects.remove(obj, do_unlink=True)

def make_object_block(name, loc, color):
    bpy.ops.mesh.primitive_cube_add(size=1.8, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    mat = bpy.data.materials.new(f"Mat_{name}")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = 0.35
    bsdf.inputs["Emission"].default_value = (color[0]*0.7, color[1]*0.7, color[2]*0.7, 1.0)
    bsdf.inputs["Emission Strength"].default_value = 2.0
    obj.data.materials.append(mat)
    return obj

def make_arrow(start, end, name):
    # simple cylinder + cone arrow along line from start to end
    import mathutils, math
    start_v = mathutils.Vector(start)
    end_v = mathutils.Vector(end)
    direction = end_v - start_v
    length = direction.length
    direction.normalize()

    # cylinder
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=length*0.7, location=(0,0,0))
    cyl = bpy.context.active_object
    cyl.name = f"{name}_shaft"

    # cone
    bpy.ops.mesh.primitive_cone_add(radius1=0.2, depth=length*0.3, location=(0,0,0))
    cone = bpy.context.active_object
    cone.name = f"{name}_head"

    # combine into collection-like grouping by parenting
    cone.parent = cyl

    # orient along direction
    up = mathutils.Vector((0,0,1))
    rot_quat = up.rotation_difference(direction)
    cyl.rotation_mode = 'QUATERNION'
    cyl.rotation_quaternion = rot_quat
    cone.rotation_mode = 'QUATERNION'
    cone.rotation_quaternion = rot_quat

    mid = (start_v + end_v) / 2
    cyl.location = mid
    cone.location = end_v

    for obj in (cyl, cone):
        mat = bpy.data.materials.new(f"Mat_{name}")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        bsdf.inputs["Emission"].default_value = (0.9, 0.9, 1.0, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 5.0
        obj.data.materials.append(mat)

# Objects A, B, and Merge M
A = make_object_block("Obj_A", (-3.0, 0.0, 0.9), (0.3, 0.7, 1.0, 1.0))
B = make_object_block("Obj_B", ( 3.0, 0.0, 0.9), (1.0, 0.5, 0.2, 1.0))
M = make_object_block("Obj_M", ( 0.0, 2.5, 0.9), (0.95, 0.95, 0.95, 1.0))

# Arrows A <- M -> B
make_arrow((0.0, 2.5, 0.9), (-3.0, 0.0, 0.9), "Arrow_M_to_A")
make_arrow((0.0, 2.5, 0.9), ( 3.0, 0.0, 0.9), "Arrow_M_to_B")

# Optional "colimit cone" arrow from below
make_arrow((0.0, -3.0, 0.3), (0.0, 2.5, 0.9), "Arrow_Colimit")

print("[v3.2] Higher-category semantic merge diagram created.")
