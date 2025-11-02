
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
BLEND_PATH = r"/mnt/c/Users/Mechachleopteryx/OneDrive/Documents/GitHub/Centerfuge/out/blends/entropy_coupling_lattice.blend"
RENDER_PATH = r"/mnt/c/Users/Mechachleopteryx/OneDrive/Documents/GitHub/Centerfuge/out/renders/entropy_coupling_lattice.png"
VIDEO_PATH  = r"/mnt/c/Users/Mechachleopteryx/OneDrive/Documents/GitHub/Centerfuge/out/videos/entropy_coupling_lattice.mp4"
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

import math

N = 7; SP=0.8; BASE=0.16
mat_node = make_emission("MatNode", (0.25,0.85,1.0,1.0), strength=2.2)

def Phi(x,y,z):
    r2 = x*x + y*y + z*z
    return math.exp(-0.35*r2) + 0.25*(math.sin(1.7*x)+math.cos(1.4*y)+0.5*math.sin(1.1*z))

def vfield(x,y,z):
    r2 = x*x + y*y + 1e-6
    k = 1.0/(1.0+0.2*r2)
    return (-k*y, k*x, 0.2*math.sin(0.8*z))

def Sproxy(x,y,z):
    eps = 0.12
    def P(a,b,c): return Phi(a,b,c)
    dpx = (P(x+eps,y,z)-P(x-eps,y,z))/(2*eps)
    dpy = (P(x,y+eps,z)-P(x,y-eps,z))/(2*eps)
    dpz = (P(x,y,z+eps)-P(x,y,z-eps))/(2*eps)
    return (dpx*dpx+dpy*dpy+dpz*dpz)**0.5

offset = (N-1)*SP*0.5
nodes = []
for ix in range(N):
    for iy in range(N):
        for iz in range(N//2):
            x = ix*SP - offset
            y = iy*SP - offset
            z = iz*SP - offset*0.5
            ph = Phi(x,y,z)
            vx,vy,vz = vfield(x,y,z)
            sp = Sproxy(x,y,z)
            size = BASE*(0.5 + 0.8*max(0.02,ph))
            bpy.ops.mesh.primitive_uv_sphere_add(radius=size, location=(x,y,z))
            s = bpy.context.active_object
            s.data.materials.append(mat_node)
            # tint hue by |v| and brightness by 1/(1+S)
            vmag = (vx*vx+vy*vy+vz*vz)**0.5
            tint = min(1.0, 0.4 + 0.6*vmag)
            s.color = (tint, 0.7, 1.0/(1.0+0.5*sp), 1.0)
            nodes.append(s)

cam_obj.location = (5.2, -7.2, 5.3)
cam_obj.rotation_euler = Euler((1.15, 0.0, 0.8), 'XYZ')
light_obj.location = (3.0, -2.0, 6.0)
light_obj.scale = (5,5,5)

if DO_ANIM:
    setup_animation(bpy.context.scene, FPS, DURATION, VIDEO_PATH)
    empty = bpy.data.objects.new("PulseCoupling", None)
    bpy.context.collection.objects.link(empty)
    for n in nodes: n.parent = empty
    for f in [1, DURATION//2, DURATION]:
        bpy.context.scene.frame_set(f)
        t = (f-1)/max(1,DURATION-1)
        s = 1.0 + 0.12*math.sin(2*math.pi*t)
        empty.scale = (s,s,s)
        empty.keyframe_insert(data_path="scale", index=-1)

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
