
import bpy, math, random
from mathutils import Euler

# Reset
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
if scene.render.engine == "CYCLES":
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 32
    scene.cycles.use_adaptive_sampling = True
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 70

world = bpy.data.worlds.new("RSVPWorld")
scene.world = world
world.color = (0.02, 0.02, 0.02, 1.0)

# Camera
cam_data = bpy.data.cameras.new("Camera")
cam_obj = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

# Light
light_data = bpy.data.lights.new(name="Key", type='AREA')
light_data.energy = 2000
light_obj = bpy.data.objects.new("Key", light_data)
scene.collection.objects.link(light_obj)

BLEND_PATH = r"/mnt/c/Users/Mechachleopteryx/OneDrive/Documents/GitHub/Centerfuge/out/blends/lamphrodyne_shell.blend"
RENDER_PATH = r"/mnt/c/Users/Mechachleopteryx/OneDrive/Documents/GitHub/Centerfuge/out/renders/lamphrodyne_shell.png"
VIDEO_PATH  = r"/mnt/c/Users/Mechachleopteryx/OneDrive/Documents/GitHub/Centerfuge/out/renders/lamphrodyne_shell.mp4"
DO_RENDER = True
DO_ANIM   = False
FPS       = 30
DURATION  = 120

def make_emission(name, color=(0.6,0.9,1.0,1.0), strength=2.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = color
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return m

def make_principled(name, color=(0.8,0.8,0.85,1.0), rough=0.3, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    return m

mat_shell = make_emission("MatShell", (0.25,0.85,1.0,1.0), strength=2.2)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=1)
obj = bpy.context.object
obj.data.materials.append(mat_shell)

# Wireframe copy
grid = obj.copy()
grid.data = obj.data.copy()
bpy.context.collection.objects.link(grid)
mod = grid.modifiers.new(name="Wire", type="WIREFRAME")
mod.thickness = 0.04
grid.data.materials.clear()
grid.data.materials.append(make_principled("MatWire", (0.8,0.9,1.0,1.0), rough=0.3))

cam_obj.location = (0.0, -4.5, 3.2)
cam_obj.rotation_euler = Euler((1.2, 0.0, 0.0), 'XYZ')
light_obj.location = (1.8, -2.0, 4.5)
light_obj.scale = (4,4,4)

import os
os.makedirs(os.path.dirname(BLEND_PATH), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)

if DO_RENDER and not DO_ANIM:
    os.makedirs(os.path.dirname(RENDER_PATH), exist_ok=True)
    bpy.context.scene.render.image_settings.file_format = 'PNG'
    bpy.context.scene.render.filepath = RENDER_PATH
    bpy.ops.render.render(write_still=True)
