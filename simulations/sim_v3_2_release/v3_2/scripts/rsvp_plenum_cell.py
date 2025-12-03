import bpy
import math
import random
import mathutils

# Clear meshes & curves, keep lights/camera
for obj in list(bpy.context.scene.objects):
    if obj.type in {"MESH", "CURVE"}:
        bpy.data.objects.remove(obj, do_unlink=True)

PHI_COLOR = (0.3, 0.8, 1.0, 1.0)
VEC_COLOR = (1.0, 0.6, 0.2, 1.0)
ENTROPY_SPARK_COLOR = (1.0, 0.2, 0.4, 1.0)

NUM_SPARKS = 60
NUM_FLOW_RIBBONS = 5

# Φ core
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.1, location=(0, 0, 0))
phi = bpy.context.active_object
phi.name = "RSVP_Phi_Core"

phi_mat = bpy.data.materials.new("Phi_Mat")
phi_mat.use_nodes = True
bsdf = phi_mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Emission"].default_value = PHI_COLOR
bsdf.inputs["Emission Strength"].default_value = 6.0
phi.data.materials.append(phi_mat)

# Vector ellipsoid
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.5, location=(0, 0, 0))
vec = bpy.context.active_object
vec.name = "RSVP_Vector_Field"

axis = mathutils.Vector((random.random(), random.random(), random.random()))
axis.normalize()
vec.scale = (1.2 + 0.4*axis.x, 1.2 + 0.4*axis.y, 1.2 + 0.4*axis.z)

vec_mat = bpy.data.materials.new("Vector_Mat")
vec_mat.use_nodes = True
vbsdf = vec_mat.node_tree.nodes["Principled BSDF"]
vbsdf.inputs["Base Color"].default_value = (VEC_COLOR[0], VEC_COLOR[1], VEC_COLOR[2], 1.0)
vbsdf.inputs["Roughness"].default_value = 0.3
vec.data.materials.append(vec_mat)

# Entropy sparks
for i in range(NUM_SPARKS):
    theta = random.random() * math.pi
    phi_ang = random.random() * 2 * math.pi
    r = 2.3 + random.uniform(-0.05, 0.2)

    x = r * math.sin(theta) * math.cos(phi_ang)
    y = r * math.sin(theta) * math.sin(phi_ang)
    z = r * math.cos(theta)

    bpy.ops.mesh.primitive_ico_sphere_add(radius=0.12, location=(x, y, z))
    spark = bpy.context.active_object
    spark.name = f"Entropy_Spark_{i}"

    mat = bpy.data.materials.new(f"EntropyMat_{i}")
    mat.use_nodes = True
    sbsdf = mat.node_tree.nodes["Principled BSDF"]
    sbsdf.inputs["Emission"].default_value = ENTROPY_SPARK_COLOR
    sbsdf.inputs["Emission Strength"].default_value = 8.0
    spark.data.materials.append(mat)

# Lamphrodynamic flow ribbons
for j in range(NUM_FLOW_RIBBONS):
    theta0 = random.random() * math.pi
    phi0 = random.random() * 2*math.pi
    radius = 2.0
    pts = []
    steps = 32
    for k in range(steps):
        theta = theta0 + 0.8 * math.sin(k / steps * math.pi)
        phi_ang = phi0 + 2.0 * (k / steps)
        r = radius + 0.1 * math.sin(4 * phi_ang)

        x = r * math.sin(theta) * math.cos(phi_ang)
        y = r * math.sin(theta) * math.sin(phi_ang)
        z = r * math.cos(theta)
        pts.append((x, y, z))

    curve_data = bpy.data.curves.new(f"FlowRibbon_{j}", 'CURVE')
    curve_data.dimensions = '3D'
    spline = curve_data.splines.new('POLY')
    spline.points.add(len(pts)-1)
    for idx, p in enumerate(pts):
        spline.points[idx].co = (p[0], p[1], p[2], 1.0)
    curve_data.bevel_depth = 0.07

    curve_obj = bpy.data.objects.new(f"FlowRibbon_{j}", curve_data)
    bpy.context.scene.collection.objects.link(curve_obj)

    cm = bpy.data.materials.new(f"FlowMat_{j}")
    cm.use_nodes = True
    node = cm.node_tree.nodes["Principled BSDF"]
    node.inputs["Emission"].default_value = (0.5, 0.9, 1.0, 1.0)
    node.inputs["Emission Strength"].default_value = 6.0
    curve_data.materials.append(cm)

print("[v3.2] RSVP Plenum Cell created.")
