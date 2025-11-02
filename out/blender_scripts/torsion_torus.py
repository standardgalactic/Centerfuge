import bpy, math
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
bpy.ops.mesh.primitive_torus_add(major_radius=1.2, minor_radius=0.4)
obj = bpy.context.active_object
obj.name = "TorsionTorus"
obj.modifiers.new(name="Wave", type='WAVE')
obj.modifiers["Wave"].height = 0.3
obj.modifiers["Wave"].width = 0.4
bpy.context.scene.render.engine = "BLENDER_EEVEE"
bpy.context.scene.world.color = (0.02, 0.02, 0.02)
