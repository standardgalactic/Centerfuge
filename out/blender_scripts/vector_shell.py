import bpy, math
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
bpy.ops.mesh.primitive_ico_sphere_add(radius=1.0, subdivisions=3)
obj = bpy.context.active_object
obj.modifiers.new(name="Wireframe", type='WIREFRAME')
obj.modifiers["Wireframe"].thickness = 0.04
bpy.context.scene.world.color = (0.03, 0.03, 0.035)
