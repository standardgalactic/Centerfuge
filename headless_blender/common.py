"""Shared, asset-free helpers for the Centerfuge headless Blender scenes."""

import argparse
import math
import os
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector


PALETTE = {
    "dark": (0.012, 0.018, 0.028, 1.0),
    "shell": (0.13, 0.17, 0.21, 1.0),
    "cyan": (0.03, 0.75, 1.0, 1.0),
    "amber": (1.0, 0.34, 0.04, 1.0),
    "green": (0.14, 0.9, 0.42, 1.0),
    "violet": (0.58, 0.2, 1.0, 1.0),
    "paper": (0.72, 0.76, 0.72, 1.0),
}


def arguments(default_name):
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="output/headless")
    parser.add_argument("--name", default=default_name)
    parser.add_argument("--resolution", default="1280x1280")
    parser.add_argument("--samples", type=int, default=64)
    parser.add_argument("--seed", type=int, default=23)
    parser.add_argument(
        "--engine",
        choices=("AUTO", "BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "CYCLES"),
        default="AUTO",
    )
    parser.add_argument("--no-render", action="store_true")
    return parser.parse_args(argv)


def begin(args):
    random.seed(args.seed)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    width, height = (int(v) for v in args.resolution.lower().split("x", 1))
    engines = {item.identifier for item in scene.render.bl_rna.properties["engine"].enum_items}
    requested_engine = args.engine
    if requested_engine == "AUTO":
        requested_engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
    if requested_engine not in engines:
        raise RuntimeError(f"Render engine {requested_engine} is unavailable; found {sorted(engines)}")
    scene.render.engine = requested_engine
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    if scene.render.engine == "CYCLES":
        scene.cycles.samples = args.samples
        scene.cycles.use_denoising = True
    else:
        scene.render.image_settings.color_mode = "RGBA"
    scene.render.resolution_percentage = 100
    scene.world = bpy.data.worlds.new("Centerfuge World")
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = PALETTE["dark"]
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.18
    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass
    return scene


def material(name, color, metallic=0.0, roughness=0.45, emission=0.0, alpha=1.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    color = (*color[:3], alpha)
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = color
        bsdf.inputs["Emission Strength"].default_value = emission
    else:
        bsdf.inputs["Emission"].default_value = color
        bsdf.inputs["Emission Strength"].default_value = emission
    bsdf.inputs["Alpha"].default_value = alpha
    if alpha < 1.0:
        mat.blend_method = "BLEND"
    return mat


def apply(obj, mat):
    obj.data.materials.append(mat)
    return obj


def collection(name):
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    return coll


def move_to(obj, coll):
    for old in tuple(obj.users_collection):
        old.objects.unlink(obj)
    coll.objects.link(obj)
    return obj


def curve(name, points, mat, radius=0.04, cyclic=False, collection=None):
    data = bpy.data.curves.new(name, "CURVE")
    data.dimensions = "3D"
    data.resolution_u = 2
    data.bevel_depth = radius
    data.bevel_resolution = 3
    spline = data.splines.new("NURBS" if len(points) > 3 else "POLY")
    spline.points.add(len(points) - 1)
    for point, co in zip(spline.points, points):
        point.co = (*co, 1.0)
    if len(points) > 3:
        spline.order_u = min(4, len(points))
        spline.use_endpoint_u = not cyclic
    spline.use_cyclic_u = cyclic
    obj = bpy.data.objects.new(name, data)
    (collection or bpy.context.scene.collection).objects.link(obj)
    data.materials.append(mat)
    return obj


def cylinder(name, radius, depth, location, mat, vertices=64, collection=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    apply(obj, mat)
    if collection:
        move_to(obj, collection)
    return obj


def sphere(name, radius, location, mat, segments=32, collection=None):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=radius, location=location)
    obj = bpy.context.object
    obj.name = name
    apply(obj, mat)
    if collection:
        move_to(obj, collection)
    return obj


def torus(name, major, minor, location, mat, rotation=(0, 0, 0), collection=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=64,
                                    minor_segments=10, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    apply(obj, mat)
    if collection:
        move_to(obj, collection)
    return obj


def add_camera(location, target=(0, 0, 0), lens=52):
    data = bpy.data.cameras.new("Camera")
    obj = bpy.data.objects.new("Camera", data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    data.lens = lens
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = obj
    return obj


def add_lighting(key=(5, -7, 11), energy=1300):
    for name, location, power, size, color in (
        ("Key", key, energy, 5.0, (0.75, 0.88, 1.0)),
        ("Warm rim", (-7, 3, 7), energy * 0.7, 4.0, (1.0, 0.24, 0.06)),
    ):
        data = bpy.data.lights.new(name, "AREA")
        data.energy, data.shape, data.size, data.color = power, "DISK", size, color
        obj = bpy.data.objects.new(name, data)
        bpy.context.scene.collection.objects.link(obj)
        obj.location = location
        obj.rotation_euler = (Vector((0, 0, 2)) - obj.location).to_track_quat("-Z", "Y").to_euler()


def label(text, location, size=0.42, color=None, rotation=(math.pi / 2, 0, 0), align="CENTER"):
    data = bpy.data.curves.new(f"Label {text}", "FONT")
    data.body, data.align_x, data.size, data.extrude = text, align, size, 0.008
    obj = bpy.data.objects.new(f"Label {text}", data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location, obj.rotation_euler = location, rotation
    data.materials.append(color or material(f"Text {text}", PALETTE["paper"], roughness=0.6, emission=0.3))
    return obj


def floor(size=28, z=-0.03):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, z))
    return apply(bpy.context.object, material("Floor", (0.018, 0.026, 0.038, 1), metallic=0.1, roughness=0.32))


def finish(args):
    scene = bpy.context.scene
    output = Path(bpy.path.abspath(args.output)).resolve()
    output.mkdir(parents=True, exist_ok=True)
    blend_path = output / f"{args.name}.blend"
    image_path = output / f"{args.name}.png"
    scene.render.filepath = str(image_path)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    if not args.no_render:
        bpy.ops.render.render(write_still=True)
    print(f"CENTERFUGE_BLEND={blend_path}")
    if not args.no_render:
        print(f"CENTERFUGE_RENDER={image_path}")
