import bpy, math
from pathlib import Path

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene

    # Renderer: FAST + headless-safe
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 1280

    # ---- WORLD (HEADLESS SAFE) ----
    if scene.world is None:
        world = bpy.data.worlds.new("World")
        scene.world = world
    else:
        world = scene.world

    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()

    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = (0.02, 0.02, 0.02, 1.0)
    bg.inputs["Strength"].default_value = 1.5

    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])

def camera():
    scene = bpy.context.scene

    # Camera
    bpy.ops.object.camera_add(
        location=(5.5, -5.5, 4.0),
        rotation=(1.15, 0.0, 0.85)
    )
    scene.camera = bpy.context.object

    # Key light
    bpy.ops.object.light_add(type='AREA', location=(4, -4, 6))
    key = bpy.context.object
    key.data.energy = 3000
    key.data.size = 3.0

    # Fill light
    bpy.ops.object.light_add(type='AREA', location=(-5, -3, 2.5))
    fill = bpy.context.object
    fill.data.energy = 1200
    fill.data.size = 4.0

    # Rim / back light
    bpy.ops.object.light_add(type='AREA', location=(0, 6, 3))
    rim = bpy.context.object
    rim.data.energy = 2000
    rim.data.size = 2.5

def material(name, color):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = 0.4

    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def finish(outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(outdir / "scene.blend"))
    bpy.context.scene.render.filepath = str(outdir / "render.png")
    bpy.ops.render.render(write_still=True)
