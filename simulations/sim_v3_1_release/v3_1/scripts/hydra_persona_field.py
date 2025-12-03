import bpy
import random

# HYDRA Persona Field (static version)
# - Keeps camera/lights from helper
# - Clears only existing meshes
# - Creates a 7x7 lattice of cubes and 4 glowing persona spheres.

# Remove existing meshes, keep camera/lights/etc.
for obj in list(bpy.context.scene.objects):
    if obj.type == 'MESH':
        bpy.data.objects.remove(obj, do_unlink=True)

# Create simple lattice
nodes = []
for i in range(-3, 4):
    for j in range(-3, 4):
        x = i * 1.2
        y = j * 1.2
        z = random.uniform(-0.3, 0.3)
        bpy.ops.mesh.primitive_cube_add(size=0.6, location=(x, y, z))
        cube = bpy.context.active_object
        nodes.append(cube)

# HYDRA personas as colored spheres
personas = [
    ("Seer",      (0.4, 0.8, 1.0, 1.0)),
    ("Engineer",  (0.4, 1.0, 0.4, 1.0)),
    ("Archivist", (1.0, 0.7, 0.3, 1.0)),
    ("Trickster", (1.0, 0.3, 0.7, 1.0)),
]

x0 = -6.0
dx = 4.0

for idx, (name, color) in enumerate(personas):
    x = x0 + idx * dx
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.9, location=(x, 0.0, 1.5))
    sphere = bpy.context.active_object
    sphere.name = f"HYDRA_{name}"
    mat = bpy.data.materials.new(f"Mat_HYDRA_{name}")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Emission"].default_value = color
        bsdf.inputs["Emission Strength"].default_value = 5.0
        bsdf.inputs["Base Color"].default_value = color
    sphere.data.materials.append(mat)

print("[v3.1] HYDRA static lattice + personas created.")
