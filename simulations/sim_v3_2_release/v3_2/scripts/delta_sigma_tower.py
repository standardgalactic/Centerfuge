import bpy
import math

# Clear meshes/curves
for obj in list(bpy.context.scene.objects):
    if obj.type in {'MESH', 'CURVE'}:
        bpy.data.objects.remove(obj, do_unlink=True)

NUM_RINGS = 6
base_radius = 2.5
height_step = 0.8

for i in range(NUM_RINGS):
    z = i * height_step
    r = base_radius - 0.15*i
    thickness = 0.25 + 0.05*i

    bpy.ops.mesh.primitive_torus_add(
        major_radius=r,
        minor_radius=thickness,
        location=(0.0, 0.0, z)
    )
    ring = bpy.context.active_object
    ring.name = f"DS_Ring_{i}"

    mat = bpy.data.materials.new(f"Mat_DS_Ring_{i}")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]

    # map "bit density" ~ sin(i) pattern into color + emission
    bit_intensity = 0.5 + 0.5*math.sin(i * 1.2)
    color = (0.2 + 0.6*bit_intensity, 0.2, 0.5 + 0.4*bit_intensity, 1.0)

    bsdf.inputs["Emission"].default_value = color
    bsdf.inputs["Emission Strength"].default_value = 4.0 + 4.0*bit_intensity
    bsdf.inputs["Base Color"].default_value = color
    ring.data.materials.append(mat)

# base platform
bpy.ops.mesh.primitive_cylinder_add(radius=3.0, depth=0.4, location=(0.0,0.0,-0.2))
base = bpy.context.active_object
base.name = "DS_Base"
bmat = bpy.data.materials.new("Mat_DS_Base")
bmat.use_nodes = True
bbsdf = bmat.node_tree.nodes["Principled BSDF"]
bbsdf.inputs["Base Color"].default_value = (0.05, 0.05, 0.08, 1.0)
bbsdf.inputs["Roughness"].default_value = 0.9
base.data.materials.append(bmat)

print("[v3.2] Delta-sigma tower created.")
