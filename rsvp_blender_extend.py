#!/usr/bin/env python3
"""
RSVP Blender Generator (extended)
---------------------------------
Generate Blender Python scripts visualizing RSVP-inspired geometries
and optionally render them headlessly to .blend and .png files.

Usage:
  python rsvp_blender_gen.py --outdir out --scenes all
  python rsvp_blender_gen.py --outdir out --scenes torsion_spiral,entropy_wavefront,lamphrodyne_shell --blender blender --render
"""

import argparse, pathlib, subprocess, sys, json
from textwrap import dedent

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
def ensure_dir(p: pathlib.Path):
    p.mkdir(parents=True, exist_ok=True)

def make_header(blend_path, render_path, video_path, do_render, do_anim, fps, duration, engine, samples):
    return dedent(f"""
    import bpy, math, random
    from mathutils import Euler

    # Reset
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "{engine}"
    if scene.render.engine == "CYCLES":
        scene.cycles.device = 'CPU'
        scene.cycles.samples = {samples}
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

    BLEND_PATH = r"{blend_path}"
    RENDER_PATH = r"{render_path}"
    VIDEO_PATH  = r"{video_path}"
    DO_RENDER = {str(do_render)}
    DO_ANIM   = {str(do_anim)}
    FPS       = {fps}
    DURATION  = {duration}

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
    """)

def make_footer():
    return dedent("""
    import os
    os.makedirs(os.path.dirname(BLEND_PATH), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)

    if DO_RENDER and not DO_ANIM:
        os.makedirs(os.path.dirname(RENDER_PATH), exist_ok=True)
        bpy.context.scene.render.image_settings.file_format = 'PNG'
        bpy.context.scene.render.filepath = RENDER_PATH
        bpy.ops.render.render(write_still=True)
    """)

# -------------------------------------------------------------------
# Scene templates
# -------------------------------------------------------------------

def scene_torsion_spiral(blend_path, render_path, video_path, do_render, do_anim, fps, duration, engine, samples):
    """Helical torsion spiral created via screw modifier."""
    header = make_header(blend_path, render_path, video_path, do_render, do_anim, fps, duration, engine, samples)
    body = dedent("""
    import math
    mat_spiral = make_emission("MatSpiral", (0.4,0.9,1.0,1.0), strength=3.0)

    bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=0.4)
    cyl = bpy.context.active_object
    cyl.data.materials.append(mat_spiral)
    bpy.ops.object.modifier_add(type='SCREW')
    cyl.modifiers["Screw"].angle = math.radians(720)
    cyl.modifiers["Screw"].screw_offset = 2.0
    cyl.modifiers["Screw"].steps = 64

    cam_obj.location = (3.5, -4.2, 3.0)
    cam_obj.rotation_euler = Euler((1.1, 0.0, 0.8), 'XYZ')
    light_obj.location = (2.0, -2.0, 3.5)
    light_obj.scale = (3,3,3)
    """)
    return header + body + make_footer()

def scene_entropy_wavefront(blend_path, render_path, video_path, do_render, do_anim, fps, duration, engine, samples):
    """Wavefront spheres illustrating entropy gradients."""
    header = make_header(blend_path, render_path, video_path, do_render, do_anim, fps, duration, engine, samples)
    body = dedent("""
    import math
    mat_core = make_emission("MatEntropy", (0.3,0.8,1.0,1.0), strength=2.5)

    for i in range(12):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2+i*0.05, location=(0,0,i*0.2))
        s = bpy.context.object
        s.location.x = math.sin(i*0.4)*0.6
        s.location.y = math.cos(i*0.4)*0.6
        s.data.materials.append(mat_core)

    cam_obj.location = (4.2, -5.3, 4.0)
    cam_obj.rotation_euler = Euler((1.1, 0.0, 0.8), 'XYZ')
    light_obj.location = (3.0, -2.0, 5.0)
    light_obj.scale = (3,3,3)
    """)
    return header + body + make_footer()

def scene_lamphrodyne_shell(blend_path, render_path, video_path, do_render, do_anim, fps, duration, engine, samples):
    """Lamphrodyne shell: a glowing icosphere with wireframe overlay."""
    header = make_header(blend_path, render_path, video_path, do_render, do_anim, fps, duration, engine, samples)
    body = dedent("""
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
    """)
    return header + body + make_footer()

SCENE_BUILDERS = {
    "torsion_spiral": scene_torsion_spiral,
    "entropy_wavefront": scene_entropy_wavefront,
    "lamphrodyne_shell": scene_lamphrodyne_shell,
}

# -------------------------------------------------------------------
# CLI
# -------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Generate Blender scene scripts and optionally render them.")
    ap.add_argument("--outdir", default="out")
    ap.add_argument("--scenes", default="all")
    ap.add_argument("--blender", default=None)
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--engine", default="BLENDER_EEVEE", choices=["BLENDER_EEVEE", "CYCLES"])
    ap.add_argument("--samples", type=int, default=32)
    args = ap.parse_args()

    outdir = pathlib.Path(args.outdir)
    scripts_dir = outdir / "blender_scripts"
    blends_dir  = outdir / "blends"
    renders_dir = outdir / "renders"
    for d in [scripts_dir, blends_dir, renders_dir]: ensure_dir(d)

    if args.scenes.lower() == "all":
        selected = list(SCENE_BUILDERS.keys())
    else:
        selected = [s.strip() for s in args.scenes.split(",") if s.strip()]

    generated = []
    for name in selected:
        if name not in SCENE_BUILDERS:
            print(f"[WARN] Unknown scene '{name}'", file=sys.stderr)
            continue
        blend_path = str((blends_dir / f"{name}.blend").resolve())
        render_path = str((renders_dir / f"{name}.png").resolve())
        video_path  = str((renders_dir / f"{name}.mp4").resolve())
        code = SCENE_BUILDERS[name](blend_path, render_path, video_path,
                                    args.render, False, 30, 120,
                                    args.engine, args.samples)
        script_path = scripts_dir / f"{name}.py"
        script_path.write_text(code, encoding="utf-8")
        generated.append({
            "name": name,
            "script": str(script_path),
            "blend": blend_path,
            "render": render_path
        })

    manifest = {"generated": generated}
    (outdir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"[OK] Wrote {len(generated)} scripts → {scripts_dir}")

    if args.blender:
        for item in generated:
            print(f"[RUN] {item['name']} via Blender …")
            cmd = [args.blender, "-noaudio", "-b", "-P", item["script"]]
            try:
                subprocess.run(cmd, check=True)
                print(f"[OK] → {item['render']}")
            except subprocess.CalledProcessError as e:
                print(f"[ERR] Blender failed for {item['name']}: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
