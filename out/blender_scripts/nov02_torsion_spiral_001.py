import bpy, math
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
bpy.ops.curve.primitive_bezier_circle_add(radius=1)
curve = bpy.context.object
bpy.ops.object.modifier_add(type='SCREW')
curve.modifiers["Screw"].angle = math.radians(720)
curve.modifiers["Screw"].screw_offset = 1.5
curve.modifiers["Screw"].steps = 64
bpy.context.scene.render.engine = "BLENDER_EEVEE"

# Add camera
bpy.ops.object.camera_add(location=(3, -3, 2))
cam = bpy.context.object
cam.rotation_euler = (1.1, 0, 0.8)
bpy.context.scene.camera = cam

# Add light
bpy.ops.object.light_add(type='AREA', location=(2, -2, 3))
light = bpy.context.object
light.data.energy = 800
light.data.size = 3.0

# Background
bpy.context.scene.world.use_nodes = True
bg = bpy.context.scene.world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.02, 0.02, 0.025, 1)
