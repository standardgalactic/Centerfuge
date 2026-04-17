#!/usr/bin/env python3
"""
render_still.py — universal still renderer for any rsvp-generated .blend.

Applies consistent auto-framing camera and minimal 3-point lighting, then
renders to PNG. Works with any .blend regardless of generator origin.

Usage:
    blender --background scene.blend --python render_still.py -- \
        --output /tmp/scene.png \
        --resolution 1024 \
        --samples 64
"""

from __future__ import annotations
import sys
import argparse
import math
import mathutils
import bpy


def parse_args() -> argparse.Namespace:
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    p = argparse.ArgumentParser(description="Universal rsvp still renderer")
    p.add_argument("--output", required=True, help="Output PNG path")
    p.add_argument("--resolution", type=int, default=1024)
    p.add_argument("--samples", type=int, default=64)
    p.add_argument("--lens", type=float, default=35.0, help="Camera focal length mm")
    p.add_argument("--distance-factor", type=float, default=2.5,
                   help="Camera distance relative to scene width")
    p.add_argument("--elevation", type=float, default=0.25,
                   help="Camera elevation fraction (0=side, 1=top)")
    p.add_argument("--look-at-fraction", type=float, default=0.35,
                   help="Fraction up scene height to aim camera (0=base, 1=top)")
    return p.parse_args(argv)


args = parse_args()


def scene_bounds():
    """Return min, max, center, width, height of all mesh/curve objects."""
    min_v = mathutils.Vector((1e9, 1e9, 1e9))
    max_v = mathutils.Vector((-1e9, -1e9, -1e9))
    found = False

    for obj in bpy.context.scene.objects:
        if obj.type not in ("MESH", "CURVE"):
            continue
        for corner in obj.bound_box:
            v = obj.matrix_world @ mathutils.Vector(corner)
            min_v.x = min(min_v.x, v.x)
            min_v.y = min(min_v.y, v.y)
            min_v.z = min(min_v.z, v.z)
            max_v.x = max(max_v.x, v.x)
            max_v.y = max(max_v.y, v.y)
            max_v.z = max(max_v.z, v.z)
            found = True

    if not found:
        min_v = mathutils.Vector((-2, -2, 0))
        max_v = mathutils.Vector((2, 2, 4))

    center = (min_v + max_v) / 2.0
    width  = max(max_v.x - min_v.x, max_v.y - min_v.y, 0.5)
    height = max(max_v.z - min_v.z, 0.5)

    # Look-at point: controllable fraction up the height from base
    look_at = mathutils.Vector((
        center.x,
        center.y,
        min_v.z + height * args.look_at_fraction,
    ))

    return look_at, width, height, min_v


def remove_existing_cameras_and_lights() -> None:
    for obj in list(bpy.context.scene.objects):
        if obj.type in ("CAMERA", "LIGHT"):
            bpy.data.objects.remove(obj, do_unlink=True)


def setup_camera(look_at: mathutils.Vector, width: float, height: float) -> None:
    # Distance based on the larger of width and height so the whole object fits
    span = max(width, height)
    dist = span * args.distance_factor

    az = math.pi / 4
    el = math.pi * args.elevation * 0.5

    cx = look_at.x + dist * math.cos(el) * math.cos(az)
    cy = look_at.y + dist * math.cos(el) * math.sin(az)
    cz = look_at.z + dist * math.sin(el)

    cam_data = bpy.data.cameras.new("StillCamera")
    cam_data.lens = args.lens
    cam_obj = bpy.data.objects.new("StillCamera", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)

    cam_obj.location = (cx, cy, cz)
    direction = look_at - mathutils.Vector((cx, cy, cz))
    cam_obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

    bpy.context.scene.camera = cam_obj
    print(f"[render_still] camera at ({cx:.2f}, {cy:.2f}, {cz:.2f})  "
          f"looking at ({look_at.x:.2f}, {look_at.y:.2f}, {look_at.z:.2f})")


def setup_lighting(look_at: mathutils.Vector, span: float) -> None:
    sun_data = bpy.data.lights.new("Key", type="SUN")
    sun_data.energy = 4.0
    sun_data.angle = 0.05
    sun_obj = bpy.data.objects.new("Key", sun_data)
    bpy.context.scene.collection.objects.link(sun_obj)
    sun_obj.rotation_euler = (0.6, 0.0, -0.9)

    fill_data = bpy.data.lights.new("Fill", type="AREA")
    fill_data.energy = 60.0 * max(span / 4.0, 1.0)
    fill_data.size = span * 1.2
    fill_obj = bpy.data.objects.new("Fill", fill_data)
    bpy.context.scene.collection.objects.link(fill_obj)
    fill_obj.location = (look_at.x, look_at.y, look_at.z + span * 1.5)

    rim_data = bpy.data.lights.new("Rim", type="SUN")
    rim_data.energy = 1.2
    rim_obj = bpy.data.objects.new("Rim", rim_data)
    bpy.context.scene.collection.objects.link(rim_obj)
    rim_obj.rotation_euler = (0.4, 0.0, 2.3)

    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.15, 0.15, 0.18, 1.0)
        bg.inputs["Strength"].default_value = 1.0


def setup_render() -> None:
    scene = bpy.context.scene
    # Use EEVEE for reliable preview renders on any hardware/version
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = max(args.samples, 16)
    scene.render.resolution_x = args.resolution
    scene.render.resolution_y = args.resolution
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = args.output


# Execute
look_at, width, height, min_v = scene_bounds()
span = max(width, height)
print(f"[render_still] width={width:.2f}  height={height:.2f}  "
      f"span={span:.2f}  look_at_z={look_at.z:.2f}")

remove_existing_cameras_and_lights()
setup_camera(look_at, width, height)
setup_lighting(look_at, span)
setup_render()

bpy.ops.render.render(write_still=True)
print(f"[render_still] → {args.output}")