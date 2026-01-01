
# common.py - shared bpy helpers for repeatable experiments

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
    scene.view_settings.view_transform = 'Filmic'

def ensure_collection(name="Experiment"):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col

def make_camera(location=(6,-6,4), look_at=(0,0,0), lens=50):
    cam_data = bpy.data.cameras.new("Camera")
    cam = bpy.data.objects.new("Camera", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = Vector(location)
    cam_data.lens = lens
    direction = Vector(look_at) - cam.location
    cam.rotation_euler = direction.to_track_quat('-Z','Y').to_euler()
    bpy.context.scene.camera = cam
    return cam

def make_three_point_lights():
    def add(name, loc, energy):
        ldata = bpy.data.lights.new(name, 'AREA')
        ldata.energy = energy
        obj = bpy.data.objects.new(name, ldata)
        bpy.context.scene.collection.objects.link(obj)
        obj.location = Vector(loc)
        obj.rotation_euler = (Vector((0,0,0)) - obj.location).to_track_quat('-Z','Y').to_euler()
    add("Key", (4,-4,6), 2000)
    add("Fill", (-6,-2,3), 800)
    add("Rim", (0,6,4), 1200)

def simple_material(name, color=(0.8,0.8,0.8,1), emission=(0,0,0,1), e=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Emission Color"].default_value = emission
    bsdf.inputs["Emission Strength"].default_value = e
    mat.node_tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def parse_args_after_double_dash():
    import sys
    argv = sys.argv
    args = argv[argv.index("--")+1:] if "--" in argv else []
    opts = {"outdir":"out/run"}
    for i,a in enumerate(args):
        if a == "--outdir":
            opts["outdir"] = args[i+1]
    return opts
