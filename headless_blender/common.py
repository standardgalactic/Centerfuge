"""Shared, asset-free helpers for the Centerfuge headless Blender scenes."""

import argparse
import json
import math
import os
import random
import subprocess
import sys
import time
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

# Continuation: PALETTE above is frozen, by reference, as STYLE_PRESETS["original"]
# so that a future stylistic change to PALETTE (or an added alternate preset) does
# not silently change what "original" means for images already rendered and
# committed under that name. What is preserved across such a change is the exact
# color mapping named "original"; what is explicitly NOT preserved is any
# guarantee that the *default* PALETTE global still equals it once a second
# preset is added -- at that point, scenes must select "original" explicitly via
# --style to remain comparable to earlier renders, and this dict is the
# authoritative source of that comparison, not the current PALETTE global.
STYLE_PRESETS = {"original": dict(PALETTE)}


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
    parser.add_argument("--style", choices=tuple(STYLE_PRESETS), default="original")
    parser.add_argument("--no-render", action="store_true")
    return parser.parse_args(argv)


def begin(args):
    random.seed(args.seed)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    # Apply the requested style preset in place, before any scene-building code
    # runs. Every scene script calls begin(args) first and only then reads
    # PALETTE["..."] while constructing materials, so mutating this module's
    # PALETTE dict here (rather than rebinding the name to a new dict) is what
    # makes every later `PALETTE["cyan"]` lookup in the calling script resolve
    # to the selected preset. STYLE_PRESETS["original"] itself is never
    # mutated, so it remains the fixed reference for future comparison.
    PALETTE.clear()
    PALETTE.update(STYLE_PRESETS[args.style])
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


def open_cylindrical_housing(name, outer_radius, inner_radius, height, mat, collection, segments=72,
                              start_deg=-45, sweep_deg=270):
    """Build a thick shell with a real angular gap, not a full solid with a hole implied by camera angle.

    The returned mesh only has faces for `sweep_deg` degrees of the full
    circle (default 270 of 360), so the missing 90 degrees is a structural
    absence -- there is no geometry there for any ray to hit -- rather than a
    closed cylinder that merely happens to face away from the camera. This is
    the housing half of the non-occlusion invariant: pair it with
    tag_role(housing, EXTERIOR_SHELL_ROLE) and pass every object that should
    be visible through the gap to verify_visibility via finish()'s
    interior_objects argument, so the claim is checked, not assumed.
    """
    start = math.radians(start_deg)
    sweep = math.radians(sweep_deg)
    vertices = []
    faces = []
    for index in range(segments + 1):
        angle = start + sweep * index / segments
        c, s = math.cos(angle), math.sin(angle)
        vertices.extend(((outer_radius * c, outer_radius * s, 0),
                         (outer_radius * c, outer_radius * s, height),
                         (inner_radius * c, inner_radius * s, 0),
                         (inner_radius * c, inner_radius * s, height)))
    for index in range(segments):
        a, b = index * 4, (index + 1) * 4
        faces.extend(((a, b, b + 1, a + 1),
                      (a + 3, b + 3, b + 2, a + 2),
                      (a + 1, b + 1, b + 3, a + 3),
                      (a + 2, b + 2, b, a)))
    last = segments * 4
    faces.extend(((0, 1, 3, 2), (last + 2, last + 3, last + 1, last)))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    apply(obj, mat)
    bevel = obj.modifiers.new("Soft housing edges", "BEVEL")
    bevel.width = 0.045
    bevel.segments = 2
    return obj


# --- Non-occlusion invariant --------------------------------------------------
#
# A scene may claim to be a "cutaway", "cross-section", or "interior view" only
# if its interior geometry is actually reachable by light/camera rays through a
# real subtractive or open opening in the enclosing shell -- not because an
# opaque object merely happens not to sit in the way for one camera angle. This
# tags objects by role and then empirically verifies visibility with ray casts
# from the camera, rather than trusting the scene's construction to have been
# done correctly.

INTERIOR_ROLE = "interior"
EXTERIOR_SHELL_ROLE = "exterior_shell"


def tag_role(obj, role):
    """Mark obj as playing `role` ("interior" or "exterior_shell") for verify_visibility."""
    obj["cutaway_role"] = role
    return obj


def verify_visibility(camera, interior_objects, min_fraction=0.6, samples_per_object=24):
    """Ray-cast from the camera to sampled points on each interior object.

    Returns a report dict. Raises RuntimeError if too few interior objects are
    actually reachable by an unobstructed ray from the camera -- this is what
    distinguishes a real cutaway (structurally open) from an opaque occluder
    that merely happens to be out of frame (visually obscured only).
    """
    depsgraph = bpy.context.evaluated_depsgraph_get()
    origin = camera.matrix_world.translation.copy()
    per_object = {}
    for obj in interior_objects:
        mesh_eval = obj.evaluated_get(depsgraph)
        if obj.type == "CURVE":
            # Curve objects (common.curve()) have no .vertices; their actual
            # geometry lives in spline.points, authored in this codebase as
            # already-world-space coordinates with obj.matrix_world left at
            # identity. Falling back to a single object-origin sample here
            # would silently check visibility of an arbitrary (0,0,0) point
            # instead of the duct/spoke/trajectory the curve actually draws --
            # a false pass or fail that this invariant exists to prevent.
            verts = [obj.matrix_world @ Vector(point.co[:3])
                     for spline in mesh_eval.data.splines for point in spline.points]
        else:
            try:
                verts = [obj.matrix_world @ Vector(v.co) for v in mesh_eval.data.vertices]
            except AttributeError:
                verts = [obj.matrix_world @ Vector((0, 0, 0))]
        if not verts:
            continue
        step = max(1, len(verts) // samples_per_object)
        sample_points = verts[::step][:samples_per_object] or verts[:1]
        hits, total = 0, 0
        for point in sample_points:
            direction = (point - origin)
            distance = direction.length
            if distance < 1e-6:
                continue
            direction.normalize()
            success, location, _normal, _index, hit_obj, _matrix = bpy.context.scene.ray_cast(
                depsgraph, origin + direction * 1e-4, direction, distance=distance * 0.999
            )
            total += 1
            # A clear ray (no hit before reaching the target) or a ray that
            # terminates on the target object itself counts as visible.
            if not success or hit_obj == obj:
                hits += 1
        fraction = hits / total if total else 0.0
        per_object[obj.name] = {"hits": hits, "samples": total, "fraction": fraction}

    overall = [r["fraction"] for r in per_object.values()]
    overall_fraction = sum(overall) / len(overall) if overall else 0.0
    report = {
        "min_fraction_required": min_fraction,
        "overall_fraction": overall_fraction,
        "objects": per_object,
    }
    failing = {name: r for name, r in per_object.items() if r["fraction"] < min_fraction}
    if failing or not per_object:
        raise RuntimeError(
            "Non-occlusion invariant failed: interior geometry is not reachable by "
            f"camera rays (report={json.dumps(report)}). A scene claiming a cutaway "
            "must expose interior objects through an actual opening, not merely "
            "position an opaque shell out of the camera's immediate line of sight."
        )
    return report


# --- Fail-loud invariant -------------------------------------------------------
#
# Success is defined at the level of a verified, non-degenerate rendered image
# and a written provenance record -- not merely a zero process exit code. A
# render that silently produces a blank/near-uniform image (wrong camera, dead
# lighting, fully transparent material) must still fail the build.

def verify_image_not_degenerate(image_path, min_stddev=1.5, sample_stride=7):
    """Load the rendered PNG back through Blender's image API and check contrast.

    Raises RuntimeError if the image is missing, unreadable, or has pixel
    variance below `min_stddev` (a near-blank/uniform image), which would
    otherwise let a broken scene report success merely because Blender's
    render operator did not raise an exception.
    """
    image_path = Path(image_path)
    if not image_path.exists() or image_path.stat().st_size == 0:
        raise RuntimeError(f"Fail-loud invariant failed: {image_path} was not written.")
    image = bpy.data.images.load(str(image_path), check_existing=False)
    try:
        pixels = list(image.pixels[:: sample_stride * 4])
        if not pixels:
            raise RuntimeError(f"Fail-loud invariant failed: {image_path} has no readable pixels.")
        mean = sum(pixels) / len(pixels)
        variance = sum((p - mean) ** 2 for p in pixels) / len(pixels)
        stddev = variance ** 0.5 * 255.0
        if stddev < min_stddev:
            raise RuntimeError(
                f"Fail-loud invariant failed: {image_path} is near-uniform "
                f"(stddev={stddev:.3f} < {min_stddev}); rendering likely failed "
                "silently (blank frame, dead lighting, or fully transparent scene)."
            )
        return {"stddev": stddev, "sampled_pixels": len(pixels)}
    finally:
        bpy.data.images.remove(image)


# --- Provenance completeness ---------------------------------------------------
#
# Every generated artifact must be traceable to the exact code state, the
# parameters used to produce it, and whether it passed verification.

def _git_commit():
    """Return the checked-out commit SHA, or None if it cannot be determined.

    This is the "exact code state" half of the provenance record written by
    write_manifest_entry: a manifest entry with git_commit=None is not a
    failure (a shallow checkout or missing git binary is common in CI
    artifacts), but it is a documented gap in provenance, not silently
    equivalent to a resolved commit.
    """
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(Path(__file__).resolve().parent), text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def write_manifest_entry(output_dir, name, args, blend_path, image_path, verification):
    """Record this scene's provenance in <output_dir>/manifest.json.

    This performs Record only, not Admit: it writes what generation
    parameters and verification results occurred for `name`, keyed by scene
    name, without itself deciding whether the scene counts as passing. That
    admission decision belongs to check_manifest.py, which reads this file
    and treats a scene as admitted only if verification["visibility"] (when
    applicable) and verification["image"] are both present and did not raise
    -- i.e. finish() completed without RuntimeError. A scene missing from
    this file, or present with an empty verification dict for a check that
    should have run, is not admitted and must fail check_manifest.py.
    """
    manifest_path = Path(output_dir) / "manifest.json"
    manifest = {"schema_version": 1, "scenes": {}}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    manifest.setdefault("scenes", {})[name] = {
        "generator": f"headless_blender/{name}.py",
        "git_commit": _git_commit(),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "blender_version": ".".join(str(v) for v in bpy.app.version),
        "parameters": {
            "seed": args.seed,
            "resolution": args.resolution,
            "samples": args.samples,
            "engine": bpy.context.scene.render.engine,
            "style": args.style,
            "rendered": not args.no_render,
        },
        "outputs": {
            "blend": str(blend_path),
            "image": str(image_path) if not args.no_render else None,
        },
        "verification": verification,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest_path


def finish(args, interior_objects=None):
    """Save the .blend, render (unless --no-render), verify, and record provenance.

    If `interior_objects` is given, the non-occlusion invariant is checked
    against the scene's active camera before anything is considered to have
    succeeded. Any failed check raises, which -- combined with
    `--python-exit-code 1` in render_all.sh -- makes the whole pipeline fail
    loudly instead of reporting success on a broken scene.
    """
    scene = bpy.context.scene
    output = Path(bpy.path.abspath(args.output)).resolve()
    output.mkdir(parents=True, exist_ok=True)
    blend_path = output / f"{args.name}.blend"
    image_path = output / f"{args.name}.png"
    scene.render.filepath = str(image_path)

    verification = {}
    if interior_objects:
        verification["visibility"] = verify_visibility(scene.camera, interior_objects)

    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    if not args.no_render:
        bpy.ops.render.render(write_still=True)
        verification["image"] = verify_image_not_degenerate(image_path)

    write_manifest_entry(output, args.name, args, blend_path, image_path, verification)

    print(f"CENTERFUGE_BLEND={blend_path}")
    if not args.no_render:
        print(f"CENTERFUGE_RENDER={image_path}")
    print(f"CENTERFUGE_VERIFIED={json.dumps(verification)}")
