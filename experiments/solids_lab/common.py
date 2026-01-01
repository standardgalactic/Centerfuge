import bpy
import math
from mathutils import Vector
from pathlib import Path

def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 64
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080

def ensure_collection(name):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col

def camera_default():
    cam_data = bpy.data.cameras.new("Camera")
    cam = bpy.data.objects.new("Camera", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = (6, -6, 4)
    cam.rotation_euler = (math.radians(60), 0, math.radians(45))
    bpy.context.scene.camera = cam

def lights_basic():
    def light(name, loc, power):
        l = bpy.data.lights.new(name, 'AREA')
        l.energy = power
        o = bpy.data.objects.new(name, l)
        bpy.context.scene.collection.objects.link(o)
        o.location = loc

    light("Key", (4,-4,6), 2000)
    light("Fill", (-5,-3,3), 800)
    light("Rim", (0,6,4), 1200)

def material_basic(name, color=(0.6,0.6,0.6,1), rough=0.4, emit=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n = m.node_tree.nodes
    n.clear()
    out = n.new("ShaderNodeOutputMaterial")
    bsdf = n.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Emission Strength"].default_value = emit
    m.node_tree.links.new(bsdf.outputs[0], out.inputs[0])
    return m

def save_and_render(outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(outdir / "scene.blend"))
    bpy.context.scene.render.filepath = str(outdir / "render.png")
    bpy.ops.render.render(write_still=True)

def parse_args():
    import sys
    if "--" in sys.argv:
        a = sys.argv[sys.argv.index("--")+1:]
    else:
        a = []
    opts = {"outdir": "out/run"}
    for i,x in enumerate(a):
        if x == "--outdir":
            opts["outdir"] = a[i+1]
    return opts
