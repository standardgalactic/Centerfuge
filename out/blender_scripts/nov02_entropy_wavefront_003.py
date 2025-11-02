import bpy, math
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete()
for i in range(12):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.15+i*0.04, location=(0,0,i*0.12))
    s = bpy.context.object
    s.location.x = math.sin(i*0.4)*0.6
    s.location.y = math.cos(i*0.4)*0.6

import bpy, math
# Camera
bpy.ops.object.camera_add(location=(3, -3, 2))
cam = bpy.context.object
cam.rotation_euler = (1.1, 0, 0.8)
bpy.context.scene.camera = cam

# Light
bpy.ops.object.light_add(type='AREA', location=(2, -2, 3))
light = bpy.context.object
light.data.energy = 800
light.data.size = 3.0

# World background
bpy.context.scene.world.use_nodes = True
bg = bpy.context.scene.world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.02, 0.02, 0.025, 1)

bpy.context.scene.render.engine = "BLENDER_EEVEE"
bpy.context.scene.render.resolution_x = 1920
bpy.context.scene.render.resolution_y = 1080
