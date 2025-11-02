
import bpy, math, random
from math import sin, cos, pi, sqrt
from mathutils import Vector, Euler

# Reset default scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# Basic scene setup
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
if scene.render.engine == "CYCLES":
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 32
    scene.cycles.max_bounces = 6
    scene.cycles.use_adaptive_sampling = True
# Set output resolution
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 50

# World
world = bpy.data.worlds.new("RSVPWorld")
scene.world = world
if scene.render.engine == "BLENDER_EEVEE":
    world.color = (0.02, 0.02, 0.022)
else:
    world.color = (0.0, 0.0, 0.0)

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

# Save/render paths (filled by generator)
BLEND_PATH = r"/mnt/c/Users/Mechachleopteryx/OneDrive/Documents/GitHub/Centerfuge/out/blends/semantic_tiling.blend"
RENDER_PATH = r"/mnt/c/Users/Mechachleopteryx/OneDrive/Documents/GitHub/Centerfuge/out/renders/semantic_tiling.png"
VIDEO_PATH  = r"/mnt/c/Users/Mechachleopteryx/OneDrive/Documents/GitHub/Centerfuge/out/videos/semantic_tiling.mp4"
DO_RENDER = True
DO_ANIM   = False
FPS       = 30
DURATION  = 120

# Simple material helpers
def make_emission(name, color=(0.6,0.9,1.0,1.0), strength=2.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    # clear
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = color
    em.inputs["Strength"].default_value = strength
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return mat

def make_principled(name, color=(0.8,0.8,0.85,1.0), rough=0.3, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metallic
    return mat

def setup_ffmpeg(scene, video_path, fps):
    scene.render.image_settings.file_format = 'FFMPEG'
    scene.render.ffmpeg.format = 'MPEG4'
    scene.render.ffmpeg.codec = 'H264'
    scene.render.ffmpeg.constant_rate_factor = 'HIGH'
    scene.render.ffmpeg.ffmpeg_preset = 'GOOD'
    scene.render.fps = fps
    scene.render.filepath = video_path

def setup_animation(scene, fps, duration, video_path):
    scene.frame_start = 1
    scene.frame_end   = max(1, duration)
    setup_ffmpeg(scene, video_path, fps)

import math, random

NX, NY = 8, 8
SP = 1.1
mat_tile = make_principled("MatTile", (0.22,0.26,0.32,1.0), rough=0.5, metallic=0.05)
mat_glow = make_emission("MatTileGlow", (0.85,0.95,1.0,1.0), strength=2.2)

tiles = []
ox = (NX-1)*SP*0.5; oy = (NY-1)*SP*0.5
for i in range(NX):
    for j in range(NY):
        bpy.ops.mesh.primitive_plane_add(size=0.9, location=(i*SP-ox, j*SP-oy, 0.0))
        tile = bpy.context.active_object
        tile.data.materials.append(mat_tile if (i+j)%2==0 else mat_glow)
        tiles.append((tile,i,j))

cam_obj.location = (0.0, -10.0, 8.0)
cam_obj.rotation_euler = Euler((1.2, 0.0, 0.0), 'XYZ')
light_obj.location = (0.0, -4.0, 9.0)
light_obj.scale = (7,7,7)

if DO_ANIM:
    setup_animation(bpy.context.scene, FPS, DURATION, VIDEO_PATH)
    # Staggered wave of subdivision-like growth via scale keyframes
    for tile,i,j in tiles:
        phase = (i + j) / float(NX + NY)
        for f in [1, DURATION//2, DURATION]:
            bpy.context.scene.frame_set(f)
            t = (f-1)/max(1,DURATION-1)
            s = 0.2 + 0.8*abs(math.sin(2*math.pi*(t+phase)))
            tile.scale = (s,s,1.0)
            tile.keyframe_insert(data_path="scale", index=-1)

# Save and render outputs
import os
os.makedirs(os.path.dirname(BLEND_PATH), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)

if DO_RENDER and not DO_ANIM:
    # Still image
    os.makedirs(os.path.dirname(RENDER_PATH), exist_ok=True)
    bpy.context.scene.render.image_settings.file_format = 'PNG'
    bpy.context.scene.render.filepath = RENDER_PATH
    bpy.ops.render.render(write_still=True)

if DO_RENDER and DO_ANIM:
    # MP4 animation
    os.makedirs(os.path.dirname(VIDEO_PATH), exist_ok=True)
    setup_animation(bpy.context.scene, FPS, DURATION, VIDEO_PATH)
    bpy.ops.render.render(animation=True)
