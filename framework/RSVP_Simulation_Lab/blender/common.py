
import bpy
from mathutils import Vector

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 64

def camera():
    cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Cam"))
    bpy.context.scene.collection.objects.link(cam)
    cam.location = (6,-6,4)
    cam.rotation_euler = (1.1, 0, 0.8)
    bpy.context.scene.camera = cam

def lights():
    light = bpy.data.lights.new("Key", type='AREA')
    light.energy = 2000
    obj = bpy.data.objects.new("Key", light)
    obj.location = (4,-4,6)
    bpy.context.scene.collection.objects.link(obj)
