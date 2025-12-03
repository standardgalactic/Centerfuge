import bpy
import math

# Clear previous meshes & curves
for obj in list(bpy.context.scene.objects):
    if obj.type in {"MESH", "CURVE"}:
        bpy.data.objects.remove(obj, do_unlink=True)

# Central field node
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.2, location=(0,0,0))
core = bpy.context.active_object
core.name = "HYDRA_Field_Node"
cmat = bpy.data.materials.new("Mat_HYDRA_Core")
cmat.use_nodes = True
bsdf = cmat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Emission"].default_value = (0.2, 0.9, 0.9, 1.0)
bsdf.inputs["Emission Strength"].default_value = 5.5
core.data.materials.append(cmat)

personas = [
    ("Seer",      (0.4, 0.8, 1.0, 1.0), 0.0),
    ("Engineer",  (0.4, 1.0, 0.4, 1.0), math.pi/2),
    ("Archivist", (1.0, 0.7, 0.3, 1.0), math.pi),
    ("Trickster", (1.0, 0.3, 0.7, 1.0), 3*math.pi/2),
]

radius = 5.0

for name, color, ang in personas:
    x = radius * math.cos(ang)
    y = radius * math.sin(ang)
    z = 0.0

    # glyph as extruded plane
    bpy.ops.mesh.primitive_circle_add(radius=0.9, vertices=6, location=(x,y,z))
    glyph = bpy.context.active_object
    glyph.name = f"Glyph_{name}"
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value": (0,0,0.25)})
    bpy.ops.object.editmode_toggle()

    mat = bpy.data.materials.new(f"Mat_Glyph_{name}")
    mat.use_nodes = True
    gbsdf = mat.node_tree.nodes["Principled BSDF"]
    gbsdf.inputs["Emission"].default_value = color
    gbsdf.inputs["Emission Strength"].default_value = 4.5
    glyph.data.materials.append(mat)

    # thin ribbon connecting glyph to core
    curve_data = bpy.data.curves.new(f"PersonaLink_{name}", 'CURVE')
    curve_data.dimensions = '3D'
    spline = curve_data.splines.new('POLY')
    spline.points.add(1)
    spline.points[0].co = (0.0, 0.0, 0.0, 1.0)
    spline.points[1].co = (x, y, 0.0, 1.0)
    curve_data.bevel_depth = 0.05
    cobj = bpy.data.objects.new(f"PersonaLink_{name}", curve_data)
    bpy.context.scene.collection.objects.link(cobj)

    m = bpy.data.materials.new(f"Mat_PersonaLink_{name}")
    m.use_nodes = True
    lbsdf = m.node_tree.nodes["Principled BSDF"]
    lbsdf.inputs["Emission"].default_value = (0.8, 0.8, 1.0, 1.0)
    lbsdf.inputs["Emission Strength"].default_value = 3.0
    curve_data.materials.append(m)

print("[v3.2] HYDRA persona glyphs created.")
