#!/usr/bin/env python3
"""
rsvp_blender_gen.py
-------------------
Generate Blender Python scripts that visualize RSVP-inspired geometric scenes,
then (optionally) run Blender headless to emit .blend files, still PNGs, and MP4 animations.

Examples:
  # Generate scripts only
  python rsvp_blender_gen.py --outdir out --scenes all

  # Generate and run Blender headless (still images)
  python rsvp_blender_gen.py --outdir out --scenes lattice_plenum,vector_field_glyphs --blender blender --render

  # Generate and run headless with animations to MP4 (for supported scenes)
  python rsvp_blender_gen.py --outdir out --scenes lamphrodyne_vortex,trajectory_ribbons --blender blender --animate --render --fps 30 --duration 120

  # Use Cycles
  python rsvp_blender_gen.py --outdir out --scenes all --blender blender --render --engine CYCLES --samples 64
"""

import argparse
import os
import pathlib
import subprocess
import sys
import json
from textwrap import dedent

SCENE_NAMES = [
    "lattice_plenum",
    "vector_field_glyphs",
    "entropy_sheet",
    "trajectory_ribbons",
    "soliton_wane",
    "torsion_tubes",
    "lamphrodyne_vortex",
    "lattice_vector_overlay",
]

# ----------------------------
# Helpers
# ----------------------------

def ensure_dir(p: pathlib.Path):
    p.mkdir(parents=True, exist_ok=True)

def make_header(blend_path: str, render_path: str, video_path: str, do_render: bool, do_anim: bool, fps: int, duration: int, engine: str, samples: int):
    return dedent(f"""
    import bpy, math, random
    from math import sin, cos, pi, sqrt
    from mathutils import Vector, Euler

    # Reset default scene
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # Basic scene setup
    scene = bpy.context.scene
    scene.render.engine = "{engine}"
    if scene.render.engine == "CYCLES":
        scene.cycles.device = 'CPU'
        scene.cycles.samples = {samples}
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
    BLEND_PATH = r"{blend_path}"
    RENDER_PATH = r"{render_path}"
    VIDEO_PATH  = r"{video_path}"
    DO_RENDER = {str(do_render)}
    DO_ANIM   = {str(do_anim)}
    FPS       = {fps}
    DURATION  = {duration}

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
    """)

def make_footer():
    return dedent("""
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
    """)

# ----------------------------
# Scene templates
# ----------------------------

def scene_lattice_plenum(blend_path, render_path, video_path, do_render, do_anim, fps, duration, engine, samples):
    """Scalar Φ field sampled on a 3D lattice as glowing spheres; S modulates scale."""
    header = make_header(blend_path, render_path, video_path, do_render, do_anim, fps, duration, engine, samples)
    body = dedent("""
    # Parameters
    N = 8            # grid points per axis
    SPACING = 0.6
    SCALE = 0.22

    # Materials
    mat_phi = make_emission("MatPhi", (0.2,0.8,1.0,1.0), strength=2.5)

    # Geometry
    import math
    def Phi(x,y,z):
        r2 = x*x + y*y + z*z
        return math.exp(-0.4*r2) + 0.35*(math.sin(2.1*x)+math.sin(2.1*y)+math.sin(2.1*z))

    def S(x,y,z):
        eps = 0.1
        dpx = (Phi(x+eps,y,z) - Phi(x-eps,y,z))/(2*eps)
        dpy = (Phi(x,y+eps,z) - Phi(x,y-eps,z))/(2*eps)
        dpz = (Phi(x,y,z+eps) - Phi(x,y,z-eps))/(2*eps)
        return (dpx*dpx + dpy*dpy + dpz*dpz) ** 0.5

    offset = (N-1)*SPACING*0.5
    for ix in range(N):
        for iy in range(N):
            for iz in range(N//2):
                x = ix*SPACING - offset
                y = iy*SPACING - offset
                z = iz*SPACING - offset*0.5
                val = max(0.02, Phi(x,y,z))
                ent = S(x,y,z)
                scale = SCALE * (0.4 + 0.6*val)
                bpy.ops.mesh.primitive_uv_sphere_add(radius=scale, location=(x,y,z))
                sph = bpy.context.active_object
                sph.data.materials.append(mat_phi)
                sph.color = (0.4+0.6*min(ent,1.0), 0.7, 1.0, 1.0)

    # Camera & light placement
    cam_obj.location = (4.2, -5.3, 4.0)
    cam_obj.rotation_euler = Euler((1.1, 0.0, 0.8), 'XYZ')
    light_obj.location = (3.0, -2.0, 5.0)
    light_obj.scale = (3,3,3)
    """)
    return header + body + make_footer()

def scene_vector_field_glyphs(blend_path, render_path, video_path, do_render, do_anim, fps, duration, engine, samples):
    """Vector field 𝒗 rendered as arrow glyphs (cylinder + cone)."""
    header = make_header(blend_path, render_path, video_path, do_render, do_anim, fps, duration, engine, samples)
    body = dedent("""
    # Parameters
    NX, NY = 11, 11
    SPACING = 0.6
    ARROW_SCALE = 0.7

    # Materials
    mat_vec = make_principled("MatVec", (0.95,0.95,0.98,1.0), rough=0.2, metallic=0.05)

    import math
    def vfield(x,y,z=0.0):
        r2 = x*x + y*y + 1e-3
        k = 1.0 / (1.0 + 0.3*r2)
        return (-k*y, k*x, 0.3*math.sin(0.8*math.sqrt(r2)))

    def add_arrow(base_loc, direction, scale=1.0):
        import mathutils
        d = mathutils.Vector(direction)
        mag = max(d.length, 1e-6)
        d_n = d / mag

        bpy.ops.mesh.primitive_cylinder_add(radius=0.03*scale, depth=0.6*scale, location=(0,0,0))
        shaft = bpy.context.active_object
        bpy.ops.mesh.primitive_cone_add(radius1=0.07*scale, depth=0.25*scale, location=(0,0,0.4*scale))
        head = bpy.context.active_object
        shaft.select_set(True); head.select_set(True)
        bpy.context.view_layer.objects.active = shaft
        bpy.ops.object.join()
        arrow = shaft
        arrow.data.materials.append(mat_vec)

        up = mathutils.Vector((0,0,1))
        rot_axis = up.cross(d_n)
        angle = up.angle(d_n)
        if rot_axis.length > 1e-6:
            arrow.rotation_mode = 'AXIS_ANGLE'
            arrow.rotation_axis_angle = (angle, rot_axis.x, rot_axis.y, rot_axis.z)
        arrow.location = base_loc
        arrow.scale *= (0.6 + 0.6*mag)*ARROW_SCALE
        return arrow

    ox = (NX-1)*SPACING*0.5
    oy = (NY-1)*SPACING*0.5
    for i in range(NX):
        for j in range(NY):
            x = i*SPACING - ox
            y = j*SPACING - oy
            vx,vy,vz = vfield(x,y,0.0)
            add_arrow((x,y,0.0), (vx,vy,vz), scale=1.0)

    cam_obj.location = (0.0, -7.5, 6.5)
    cam_obj.rotation_euler = Euler((1.1, 0.0, 0.0), 'XYZ')
    light_obj.location = (0.0, -3.0, 8.0)
    light_obj.scale = (4,4,4)
    """)
    return header + body + make_footer()

def scene_entropy_sheet(blend_path, render_path, video_path, do_render, do_anim, fps, duration, engine, samples):
    """Entropy surface S(x,y) as a subdivided, displaced sheet with emissive grid."""
    header = make_header(blend_path, render_path, video_path, do_render, do_anim, fps, duration, engine, samples)
    body = dedent("""
    mat_sheet = make_principled("MatSheet", (0.2,0.22,0.28,1.0), rough=0.6, metallic=0.0)
    mat_grid = make_emission("MatGrid", (0.8,0.9,1.0,1.0), strength=3.0)

    bpy.ops.mesh.primitive_plane_add(size=6.0, location=(0,0,0))
    plane = bpy.context.active_object
    plane.data.materials.append(mat_sheet)

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.subdivide(number_cuts=120)
    bpy.ops.object.mode_set(mode='OBJECT')

    import bmesh, math
    me = plane.data
    bm = bmesh.new()
    bm.from_mesh(me)

    def Sxy(x,y):
        r1 = math.hypot(x-1.0,y+0.5)
        r2 = math.hypot(x+1.0,y-0.8)
        return 0.25*math.sin(2.2*r1) + 0.2*math.cos(2.0*r2)

    for v in bm.verts:
        x,y,z = v.co
        v.co.z = Sxy(x,y)

    bm.to_mesh(me)
    bm.free()

    grid = plane.copy()
    grid.data = plane.data.copy()
    bpy.context.collection.objects.link(grid)
    mod = grid.modifiers.new(name="Wire", type="WIREFRAME")
    mod.thickness = 0.01
    grid.data.materials.clear()
    grid.data.materials.append(mat_grid)

    cam_obj.location = (0.0, -6.2, 4.6)
    cam_obj.rotation_euler = Euler((1.04, 0.0, 0.0), 'XYZ')
    light_obj.location = (0.0, -3.0, 6.0)
    light_obj.scale = (4,4,4)
    """)
    return header + body + make_footer()

def scene_trajectory_ribbons(blend_path, render_path, video_path, do_render, do_anim, fps, duration, engine, samples):
    """Trajectories as beveled curves with color-coded bundles; supports animation to MP4."""
    header = make_header(blend_path, render_path, video_path, do_render, do_anim, fps, duration, engine, samples)
    body = dedent("""
    import math, random, mathutils

    cols = [
        (0.90,0.35,0.35,1.0),
        (0.35,0.90,0.55,1.0),
        (0.35,0.55,0.95,1.0),
        (0.95,0.85,0.35,1.0),
    ]
    mats = []
    for i,c in enumerate(cols):
        m = make_principled(f"Ribbon{{i}}", c, rough=0.35, metallic=0.1)
        mats.append(m)

    bpy.ops.curve.primitive_bezier_circle_add(radius=0.03, location=(0,0,0))
    profile = bpy.context.active_object
    profile.name = "RibbonProfile"

    def param_traj(t, seed=0, phase=0.0):
        random.seed(seed)
        f1 = 1.2 + 0.3*random.random()
        f2 = 0.9 + 0.3*random.random()
        px = 0.5*random.random()
        py = 0.5*random.random()
        x = 2.4*math.sin(f1*(t+phase) + px)
        y = 2.0*math.sin(f2*(t+phase) + py)
        z = 0.8*math.sin(0.7*(t+phase) + 0.2*seed) + 0.02*t
        return (x,y,z)

    def add_curve(points, mat):
        crv = bpy.data.curves.new("Trajectory", type='CURVE')
        crv.dimensions = '3D'
        spline = crv.splines.new('POLY')
        spline.points.add(len(points)-1)
        for i, p in enumerate(points):
            spline.points[i].co = (p[0], p[1], p[2], 1.0)
        crv.bevel_mode = 'OBJECT'
        crv.bevel_object = profile
        obj = bpy.data.objects.new("TrajectoryObj", crv)
        bpy.context.collection.objects.link(obj)
        obj.data.materials.append(mat)
        return obj

    bundle = []
    for b in range(4):
        mat = mats[b]
        for k in range(8):
            seed = b*100 + k
            pts = [param_traj(t, seed=seed) for t in [i*0.08 for i in range(160)]]
            bundle.append(add_curve(pts, mat))

    # Camera & light
    cam_obj.location = (0.0, -8.0, 4.0)
    cam_obj.rotation_euler = Euler((1.15, 0.0, 0.0), 'XYZ')
    light_obj.location = (0.0, -3.0, 6.0)
    light_obj.scale = (5,5,5)

    # Animation: orbit camera around Z and shimmer emission
    if DO_ANIM:
        setup_animation(bpy.context.scene, FPS, DURATION, VIDEO_PATH)
        # Parent camera to an empty for clean rotation
        empty = bpy.data.objects.new("CamOrbit", None)
        bpy.context.collection.objects.link(empty)
        cam_obj.parent = empty
        empty.location = (0.0, 0.0, 0.0)

        for f in [1, DURATION]:
            bpy.context.scene.frame_set(f)
            angle = 0.8 * (f-1)/max(1,DURATION-1) * 2*math.pi
            empty.rotation_euler = Euler((0.0, 0.0, angle), 'XYZ')
            empty.keyframe_insert(data_path="rotation_euler", index=-1)

        # Slight emission shimmer by keyframing material roughness
        for m in mats:
            bsdf = m.node_tree.nodes.get("Principled BSDF")
            for f in [1, DURATION//2, DURATION]:
                bpy.context.scene.frame_set(f)
                val = 0.25 + 0.15*math.sin(2*math.pi*f/max(1,DURATION))
                bsdf.inputs["Roughness"].default_value = val
                bsdf.inputs["Roughness"].keyframe_insert("default_value")
    """)
    return header + body + make_footer()

def scene_soliton_wane(blend_path, render_path, video_path, do_render, do_anim, fps, duration, engine, samples):
    """Localized scalar condensates: multiple gaussian Φ packets as emissive shells."""
    header = make_header(blend_path, render_path, video_path, do_render, do_anim, fps, duration, engine, samples)
    body = dedent("""
    import math, random
    mat_core = make_emission("MatCore", (0.9,0.95,1.0,1.0), strength=3.0)
    mat_shell = make_emission("MatShell", (0.4,0.8,1.0,1.0), strength=1.6)

    random.seed(7)
    centers = [(random.uniform(-1.2,1.2), random.uniform(-1.2,1.2), random.uniform(-0.6,0.6)) for _ in range(5)]

    for cx,cy,cz in centers:
        # Core
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.25, location=(cx,cy,cz))
        core = bpy.context.active_object
        core.data.materials.append(mat_core)
        # Nested fading shells
        for i in range(1,5):
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.25+0.08*i, location=(cx,cy,cz))
            sh = bpy.context.active_object
            sh.data.materials.append(mat_shell)
            sh.display_type = 'WIRE'

    cam_obj.location = (0.0, -5.7, 3.8)
    cam_obj.rotation_euler = Euler((1.1, 0.0, 0.0), 'XYZ')
    light_obj.location = (1.5, -2.0, 5.0)
    light_obj.scale = (4,4,4)

    if DO_ANIM:
        setup_animation(bpy.context.scene, FPS, DURATION, VIDEO_PATH)
        # Gentle pulsing by scaling all cores/shells via an empty parent
        empty = bpy.data.objects.new("Pulse", None)
        bpy.context.collection.objects.link(empty)
        for obj in list(bpy.context.collection.objects):
            if obj.type in {{'MESH'}} and obj.name.startswith(("Sphere")):
                obj.parent = empty
        for f in [1, DURATION]:
            bpy.context.scene.frame_set(f)
            s = 1.0 + 0.08*math.sin(2*math.pi*f/max(1,DURATION))
            empty.scale = (s,s,s)
            empty.keyframe_insert(data_path="scale", index=-1)
    """)
    return header + body + make_footer()

def scene_torsion_tubes(blend_path, render_path, video_path, do_render, do_anim, fps, duration, engine, samples):
    """Twisted tubes along field lines; tilt encodes torsion (curl magnitude proxy)."""
    header = make_header(blend_path, render_path, video_path, do_render, do_anim, fps, duration, engine, samples)
    body = dedent("""
    import math, random, mathutils, bpy

    mat_tube = make_principled("MatTube", (0.85,0.9,0.98,1.0), rough=0.25, metallic=0.1)

    # Field and curl proxy (for illustration)
    def vfield(x,y,z):
        r2 = x*x + y*y + 1e-6
        k = 1.0/(1.0+0.2*r2)
        return (-k*y, k*x, 0.5*math.sin(0.7*z))

    def curl_mag(x,y,z, eps=0.1):
        # Simple finite-difference proxy for |∇×v| magnitude
        def v(p):
            return mathutils.Vector(vfield(*p))
        vx1 = v((x+eps,y,z)); vx2 = v((x-eps,y,z))
        vy1 = v((x,y+eps,z)); vy2 = v((x,y-eps,z))
        vz1 = v((x,y,z+eps)); vz2 = v((x,y,z-eps))
        dvx_dy = (vx1 - vx2)/(2*eps)
        dvy_dx = (vy1 - vy2)/(2*eps)
        # Not a rigorous curl; we just need a smooth scalar driver
        return (dvx_dy - dvy_dx).length

    # Create a bevel profile
    bpy.ops.curve.primitive_bezier_circle_add(radius=0.04, location=(0,0,0))
    profile = bpy.context.active_object
    profile.name = "TubeProfile"

    def add_fieldline(seed, steps=140, h=0.07):
        random.seed(seed)
        p = mathutils.Vector((random.uniform(-2,2), random.uniform(-2,2), random.uniform(-1,1)))
        points = [tuple(p)]
        tilts = [0.0]
        for i in range(steps):
            v = mathutils.Vector(vfield(*p))
            p = p + h*v
            points.append(tuple(p))
            t = 0.3*curl_mag(*p)
            tilts.append(t)

        crv = bpy.data.curves.new("FieldLine", type='CURVE')
        crv.dimensions = '3D'
        spl = crv.splines.new('POLY')
        spl.points.add(len(points)-1)
        for i, q in enumerate(points):
            spl.points[i].co = (q[0], q[1], q[2], 1.0)
            spl.points[i].tilt = tilts[i]  # encode torsion-ish driver
        crv.bevel_mode = 'OBJECT'
        crv.bevel_object = profile
        obj = bpy.data.objects.new("TorsionTube", crv)
        bpy.context.collection.objects.link(obj)
        obj.data.materials.append(mat_tube)
        return obj

    tubes = [add_fieldline(seed=10+k) for k in range(18)]

    cam_obj.location = (0.0, -8.0, 4.5)
    cam_obj.rotation_euler = Euler((1.2, 0.0, 0.0), 'XYZ')
    light_obj.location = (0.0, -3.0, 7.0)
    light_obj.scale = (5,5,5)

    if DO_ANIM:
        setup_animation(bpy.context.scene, FPS, DURATION, VIDEO_PATH)
        # Rotate the whole system slowly around Z
        empty = bpy.data.objects.new("Spin", None)
        bpy.context.collection.objects.link(empty)
        for t in tubes:
            t.parent = empty
        for f in [1, DURATION]:
            bpy.context.scene.frame_set(f)
            angle = 1.0 * (f-1)/max(1,DURATION-1) * 2*math.pi
            empty.rotation_euler = Euler((0.0, 0.0, angle), 'XYZ')
            empty.keyframe_insert(data_path="rotation_euler", index=-1)
    """)
    return header + body + make_footer()

def scene_lamphrodyne_vortex(blend_path, render_path, video_path, do_render, do_anim, fps, duration, engine, samples):
    """Spiral vector plenum with evolving phase; supports MP4 animation and orbiting camera."""
    header = make_header(blend_path, render_path, video_path, do_render, do_anim, fps, duration, engine, samples)
    body = dedent("""
    import math, mathutils, random

    mat_stream = make_emission("MatStream", (0.7,0.9,1.0,1.0), strength=2.6)

    # Spiral field — lamphrodyne-esque
    def vfield(x,y,z):
        r = math.hypot(x,y) + 1e-6
        theta = math.atan2(y,x)
        k = 1.0/(1.0+0.15*r*r)
        return ( -k*math.sin(theta), k*math.cos(theta), 0.15*math.cos(0.7*r) )

    def streamline(seed, steps=200, h=0.06):
        random.seed(seed)
        p = mathutils.Vector((random.uniform(-2,2), random.uniform(-2,2), random.uniform(-0.6,0.6)))
        points = [tuple(p)]
        for i in range(steps):
            v = mathutils.Vector(vfield(*p))
            p = p + h*v
            points.append(tuple(p))
        return points

    def add_curve(points):
        crv = bpy.data.curves.new("Stream", type='CURVE')
        crv.dimensions = '3D'
        spl = crv.splines.new('POLY')
        spl.points.add(len(points)-1)
        for i, q in enumerate(points):
            spl.points[i].co = (q[0], q[1], q[2], 1.0)
        crv.bevel_depth = 0.02
        crv.bevel_resolution = 2
        obj = bpy.data.objects.new("StreamObj", crv)
        bpy.context.collection.objects.link(obj)
        obj.data.materials.append(mat_stream)
        return obj

    streams = [add_curve(streamline(100+i)) for i in range(40)]

    cam_obj.location = (0.0, -9.0, 5.2)
    cam_obj.rotation_euler = Euler((1.2, 0.0, 0.0), 'XYZ')
    light_obj.location = (0.0, -3.0, 7.0)
    light_obj.scale = (6,6,6)

    if DO_ANIM:
        setup_animation(bpy.context.scene, FPS, DURATION, VIDEO_PATH)
        # Orbit camera and pulse emission strength
        empty = bpy.data.objects.new("VortexOrbit", None)
        bpy.context.collection.objects.link(empty)
        cam_obj.parent = empty
        for f in [1, DURATION]:
            bpy.context.scene.frame_set(f)
            angle = 1.0 * (f-1)/max(1,DURATION-1) * 2*math.pi
            empty.rotation_euler = Euler((0.0, 0.0, angle), 'XYZ')
            empty.keyframe_insert(data_path="rotation_euler", index=-1)
        # Emission pulse
        emn = mat_stream.node_tree.nodes.get("Emission")
        for f in [1, DURATION//2, DURATION]:
            bpy.context.scene.frame_set(f)
            emn.inputs["Strength"].default_value = 1.8 + 1.0*math.sin(2*math.pi*f/max(1,DURATION))
            emn.inputs["Strength"].keyframe_insert("default_value")
    """)
    return header + body + make_footer()

def scene_lattice_vector_overlay(blend_path, render_path, video_path, do_render, do_anim, fps, duration, engine, samples):
    """Combined Φ lattice (spheres) + planar 𝒗 arrows."""
    header = make_header(blend_path, render_path, video_path, do_render, do_anim, fps, duration, engine, samples)
    body = dedent("""
    import math, mathutils

    # Scalar lattice
    mat_phi = make_emission("MatPhi2", (0.25,0.85,1.0,1.0), strength=2.2)
    N = 7; SPACING=0.7; SCALE=0.2
    def Phi(x,y,z):
        r2 = x*x + y*y + z*z
        return math.exp(-0.35*r2) + 0.3*(math.sin(1.7*x)+math.sin(1.7*y)+math.sin(1.7*z))
    offset = (N-1)*SPACING*0.5
    for ix in range(N):
        for iy in range(N):
            for iz in range(N//2):
                x = ix*SPACING - offset
                y = iy*SPACING - offset
                z = iz*SPACING - offset*0.5
                val = max(0.02, Phi(x,y,z))
                scale = SCALE * (0.4 + 0.6*val)
                bpy.ops.mesh.primitive_uv_sphere_add(radius=scale, location=(x,y,z))
                sph = bpy.context.active_object
                sph.data.materials.append(mat_phi)

    # Vector arrows on z=0 plane
    mat_vec = make_principled("MatVec2", (0.95,0.95,0.98,1.0), rough=0.25, metallic=0.05)

    def vfield(x,y,z=0.0):
        r2 = x*x + y*y + 1e-3
        k = 1.0/(1.0+0.25*r2)
        return (-k*y, k*x, 0.25*math.sin(0.7*math.sqrt(r2)))

    def add_arrow(base_loc, direction, scale=1.0):
        d = mathutils.Vector(direction)
        mag = max(d.length, 1e-6)
        d_n = d/mag
        bpy.ops.mesh.primitive_cylinder_add(radius=0.025*scale, depth=0.5*scale, location=(0,0,0))
        shaft = bpy.context.active_object
        bpy.ops.mesh.primitive_cone_add(radius1=0.06*scale, depth=0.22*scale, location=(0,0,0.35*scale))
        head = bpy.context.active_object
        shaft.select_set(True); head.select_set(True)
        bpy.context.view_layer.objects.active = shaft
        bpy.ops.object.join()
        arrow = shaft
        arrow.data.materials.append(mat_vec)

        up = mathutils.Vector((0,0,1))
        rot_axis = up.cross(d_n)
        angle = up.angle(d_n)
        if rot_axis.length > 1e-6:
            arrow.rotation_mode = 'AXIS_ANGLE'
            arrow.rotation_axis_angle = (angle, rot_axis.x, rot_axis.y, rot_axis.z)
        arrow.location = base_loc
        arrow.scale *= (0.6 + 0.6*mag)
        return arrow

    NX, NY = 9, 9; SP=0.9
    ox = (NX-1)*SP*0.5; oy = (NY-1)*SP*0.5
    for i in range(NX):
        for j in range(NY):
            x = i*SP - ox
            y = j*SP - oy
            vx,vy,vz = vfield(x,y,0.0)
            add_arrow((x,y,0.0), (vx,vy,vz), 1.0)

    cam_obj.location = (5.2, -7.2, 5.3)
    cam_obj.rotation_euler = Euler((1.15, 0.0, 0.8), 'XYZ')
    light_obj.location = (3.0, -2.0, 6.0)
    light_obj.scale = (5,5,5)
    """)
    return header + body + make_footer()


# ----------------------------
# Advanced RSVP–TARTAN Motifs
# ----------------------------

def scene_negentropic_front(blend_path, render_path, video_path, do_render, do_anim, fps, duration, engine, samples):
    """Expanding negentropic 'cool front' as an emissive ring (torus) that grows over time."""
    header = make_header(blend_path, render_path, video_path, do_render, do_anim, fps, duration, engine, samples)
    body = dedent("""
    import math

    mat_ring = make_emission("MatNegentropicFront", (0.8,0.95,1.0,1.0), strength=3.0)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.2, minor_radius=0.06, location=(0,0,0))
    ring = bpy.context.active_object
    ring.data.materials.append(mat_ring)

    # Ambient sheet for context
    mat_sheet = make_principled("MatCoolSheet", (0.08,0.1,0.14,1.0), rough=0.8, metallic=0.0)
    bpy.ops.mesh.primitive_plane_add(size=10.0, location=(0,0,-0.1))
    plane = bpy.context.active_object
    plane.data.materials.append(mat_sheet)

    cam_obj.location = (0.0, -7.2, 5.0)
    cam_obj.rotation_euler = Euler((1.15, 0.0, 0.0), 'XYZ')
    light_obj.location = (0.0, -3.0, 7.0)
    light_obj.scale = (6,6,6)

    if DO_ANIM:
        setup_animation(bpy.context.scene, FPS, DURATION, VIDEO_PATH)
        # Keyframe ring expansion and emission pulse
        for f in [1, DURATION//2, DURATION]:
            bpy.context.scene.frame_set(f)
            t = (f-1)/max(1,DURATION-1)
            ring.scale = (1.0 + 7.0*t, 1.0 + 7.0*t, 1.0)
            ring.keyframe_insert(data_path="scale", index=-1)
            emn = mat_ring.node_tree.nodes.get("Emission")
            emn.inputs["Strength"].default_value = 2.0 + 2.0*math.sin(2*math.pi*t)
            emn.inputs["Strength"].keyframe_insert("default_value")
    """)
    return header + body + make_footer()

def scene_semantic_tiling(blend_path, render_path, video_path, do_render, do_anim, fps, duration, engine, samples):
    """Recursive-looking tiling via a grid of tiles that animate scale in a staggered pattern."""
    header = make_header(blend_path, render_path, video_path, do_render, do_anim, fps, duration, engine, samples)
    body = dedent("""
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
    """)
    return header + body + make_footer()

def scene_scalar_vector_surface(blend_path, render_path, video_path, do_render, do_anim, fps, duration, engine, samples):
    """Static high-detail surface where height = Φ * |v| (simple Φ–𝒗 coupling)."""
    header = make_header(blend_path, render_path, video_path, do_render, do_anim, fps, duration, engine, samples)
    body = dedent("""
    # Materials
    mat_surf = make_principled("MatCoupling", (0.2,0.22,0.28,1.0), rough=0.55, metallic=0.05)
    mat_grid = make_emission("MatCoupleGrid", (0.9,0.95,1.0,1.0), strength=2.6)

    # Base plane
    bpy.ops.mesh.primitive_plane_add(size=8.0, location=(0,0,0))
    plane = bpy.context.active_object
    plane.data.materials.append(mat_surf)

    # Dense tessellation
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.subdivide(number_cuts=180)
    bpy.ops.object.mode_set(mode='OBJECT')

    import bmesh, math
    me = plane.data
    bm = bmesh.new()
    bm.from_mesh(me)

    def Phi(x,y):
        r2 = x*x + y*y
        return math.exp(-0.25*r2) + 0.35*math.sin(1.5*x)*math.cos(1.3*y)

    def vfield(x,y):
        r2 = x*x + y*y + 1e-6
        k = 1.0/(1.0+0.2*r2)
        return (-k*y, k*x, 0.0)

    for v in bm.verts:
        x,y,z = v.co
        vx,vy,_ = vfield(x,y)
        val = Phi(x,y) * (vx*vx + vy*vy) ** 0.5
        v.co.z = 0.8*val

    bm.to_mesh(me)
    bm.free()

    # Overlay wireframe emissive grid
    grid = plane.copy()
    grid.data = plane.data.copy()
    bpy.context.collection.objects.link(grid)
    mod = grid.modifiers.new(name="Wire", type="WIREFRAME")
    mod.thickness = 0.01
    grid.data.materials.clear()
    grid.data.materials.append(mat_grid)

    cam_obj.location = (0.0, -9.5, 7.2)
    cam_obj.rotation_euler = Euler((1.22, 0.0, 0.0), 'XYZ')
    light_obj.location = (0.0, -4.0, 9.0)
    light_obj.scale = (7,7,7)
    """)
    return header + body + make_footer()

def scene_entropy_coupling_lattice(blend_path, render_path, video_path, do_render, do_anim, fps, duration, engine, samples):
    """3D lattice with Φ/𝒗/S coupling shown via sphere size and color; gentle animated pulse."""
    header = make_header(blend_path, render_path, video_path, do_render, do_anim, fps, duration, engine, samples)
    body = dedent("""
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
    """)
    return header + body + make_footer()


SCENE_BUILDERS = {
    "lattice_plenum": scene_lattice_plenum,
    "vector_field_glyphs": scene_vector_field_glyphs,
    "entropy_sheet": scene_entropy_sheet,
    "trajectory_ribbons": scene_trajectory_ribbons,        # supports animation
    "soliton_wane": scene_soliton_wane,
    "torsion_tubes": scene_torsion_tubes,                  # supports animation
    "lamphrodyne_vortex": scene_lamphrodyne_vortex,        # supports animation
    "lattice_vector_overlay": scene_lattice_vector_overlay,
    "negentropic_front": scene_negentropic_front,
    "semantic_tiling": scene_semantic_tiling,
    "scalar_vector_surface": scene_scalar_vector_surface,
    "entropy_coupling_lattice": scene_entropy_coupling_lattice,
}

ANIM_SUPPORTED = {
    "trajectory_ribbons": True,
    "lamphrodyne_vortex": True,
    "torsion_tubes": True,
    # others False by default
}

# ----------------------------
# CLI
# ----------------------------

def main():
    ap = argparse.ArgumentParser(description="Generate Blender scene scripts and optionally run Blender to produce .blend files, PNG stills, and MP4 animations.")
    ap.add_argument("--outdir", default="out", help="Output directory (default: out)")
    ap.add_argument("--scenes", default="all", help="Comma-separated scene names or 'all'")
    ap.add_argument("--blender", default=None, help="Path to Blender executable; if set, run headless to create outputs")
    ap.add_argument("--render", action="store_true", help="Render a still (PNG) or animation (MP4 if --animate) in addition to saving .blend")
    ap.add_argument("--animate", action="store_true", help="If supported by the scene, render an MP4 animation instead of a single still")
    ap.add_argument("--fps", type=int, default=30, help="Frames per second for animations")
    ap.add_argument("--duration", type=int, default=120, help="Number of frames for animations")
    ap.add_argument("--engine", default="BLENDER_EEVEE", choices=["BLENDER_EEVEE","CYCLES"], help="Render engine for generated scripts")
    ap.add_argument("--samples", type=int, default=32, help="Cycles samples if using CYCLES")
    args = ap.parse_args()

    outdir = pathlib.Path(args.outdir)
    scripts_dir = outdir / "blender_scripts"
    blends_dir = outdir / "blends"
    renders_dir = outdir / "renders"
    videos_dir  = outdir / "videos"
    ensure_dir(scripts_dir); ensure_dir(blends_dir); ensure_dir(renders_dir); ensure_dir(videos_dir)

    if args.scenes.lower() == "all":
        selected = list(SCENE_NAMES)
    else:
        selected = [s.strip() for s in args.scenes.split(",") if s.strip()]
        for s in selected:
            if s not in SCENE_BUILDERS:
                print(f"[WARN] Unknown scene '{s}'. Known: {', '.join(SCENE_NAMES)}", file=sys.stderr)

    # Generate scene scripts
    generated = []
    for name in selected:
        if name not in SCENE_BUILDERS:
            continue
        blend_path = str((blends_dir / f"{name}.blend").resolve())
        render_path = str((renders_dir / f"{name}.png").resolve())
        video_path  = str((videos_dir  / f"{name}.mp4").resolve())
        # Only enable animation when requested and supported
        do_anim = bool(args.animate and ANIM_SUPPORTED.get(name, False))
        code = SCENE_BUILDERS[name](blend_path, render_path, video_path, args.render, do_anim, args.fps, args.duration, args.engine, args.samples)
        script_path = scripts_dir / f"{name}.py"
        script_path.write_text(code, encoding="utf-8")
        generated.append({
            "name": name,
            "script": str(script_path),
            "blend": blend_path,
            "render": render_path,
            "video": video_path if do_anim else None,
            "animated": do_anim
        })

    manifest = {"generated": generated}
    (outdir / "manifest.json").write_text(json.dumps(manifest, indent=2))

    print(f"[OK] Wrote {len(generated)} Blender scripts to {scripts_dir}")
    print(f"[OK] Manifest at {outdir/'manifest.json'}")

    # Optionally run Blender headless
    if args.blender:
        blender = args.blender
        for item in generated:
            print(f"[RUN] {item['name']} via Blender ...")
            cmd = [blender, "-noaudio", "-b", "-P", item["script"]]
            try:
                subprocess.run(cmd, check=True)
                print(f"[OK] .blend -> {item['blend']}")
                if args.render:
                    if item["animated"]:
                        print(f"[OK] animation -> {item['video']}")
                    else:
                        print(f"[OK] render -> {item['render']}")
            except subprocess.CalledProcessError as e:
                print(f"[ERR] Blender failed for {item['name']}: {e}", file=sys.stderr)

if __name__ == "__main__":
    main()
