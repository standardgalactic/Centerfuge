import bpy

# Semantic Merge Operators (static)
# - Three spheres: Module A, Module B, Merge M in the center.

# Clear meshes only
for obj in list(bpy.context.scene.objects):
    if obj.type == 'MESH':
        bpy.data.objects.remove(obj, do_unlink=True)

def make_blob(name, loc, color):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.3, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    mat = bpy.data.materials.new(f"Mat_{name}")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Emission"].default_value = color
        bsdf.inputs["Emission Strength"].default_value = 6.0
        bsdf.inputs["Base Color"].default_value = color
    obj.data.materials.append(mat)
    return obj

make_blob("Module_A", (-3.0, 0.0, 1.3), (0.3, 0.7, 1.0, 1.0))
make_blob("Module_B", ( 3.0, 0.0, 1.3), (1.0, 0.5, 0.2, 1.0))
make_blob("Merge_M",  ( 0.0, 0.0, 1.3), (0.95, 0.95, 0.95, 1.0))

print("[v3.1] Semantic merge blobs created.")
