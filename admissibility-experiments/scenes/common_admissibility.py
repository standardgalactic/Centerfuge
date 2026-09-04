"""Shared deterministic scene construction, measurement, rendering, and sidecars."""
from __future__ import annotations

import json
import math
import os
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import bpy
from mathutils import Vector

ROOT = Path(os.environ.get("ADMISSIBILITY_ROOT", Path(__file__).resolve().parents[1]))
OUTPUT = Path(os.environ.get("ADMISSIBILITY_OUTPUT", ROOT / "output"))
WIDTH = int(os.environ.get("WIDTH", "960"))
HEIGHT = int(os.environ.get("HEIGHT", "540"))
SAMPLES = int(os.environ.get("SAMPLES", "32"))
DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"


@dataclass
class RunContext:
    scene_id: str
    framework: str
    primitive: str
    parameters: dict[str, Any]
    checks: list[dict[str, Any]] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)

    def check(self, name: str, expected: Any, observed: Any, passed: bool,
              tolerance: float | None = None, **extra: Any) -> None:
        item = {"name": name, "expected": expected, "observed": observed,
                "passed": bool(passed)}
        if tolerance is not None:
            item["tolerance"] = tolerance
        item.update(extra)
        self.checks.append(item)


def reset_scene(seed: int = 42) -> None:
    random.seed(seed)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials,
                       bpy.data.cameras, bpy.data.lights):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)
    scene = bpy.context.scene
    scene.frame_start, scene.frame_end = 1, 120
    # Blender renamed the Eevee engine identifier in 4.2.  Capability probing
    # keeps the suite runnable on 4.0/4.1 as well as current releases.
    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = WIDTH, HEIGHT
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.world.color = (0.012, 0.018, 0.03)
    scene["deterministic_seed"] = seed


def material(name: str, color: tuple[float, float, float, float], metallic=0.0,
             roughness=0.4, emission: tuple[float, float, float, float] | None = None):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = color
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission:
        bsdf.inputs["Emission Color"].default_value = emission
        bsdf.inputs["Emission Strength"].default_value = 2.0
    return mat


PALETTE = {
    "neutral": (0.34, 0.48, 0.62, 1), "admit": (0.12, 0.72, 0.46, 1),
    "refuse": (0.88, 0.16, 0.12, 1), "commit": (0.94, 0.62, 0.12, 1),
    "violet": (0.48, 0.22, 0.86, 1), "cyan": (0.08, 0.72, 0.88, 1),
    "white": (0.86, 0.9, 0.94, 1), "dark": (0.04, 0.06, 0.09, 1),
}


def apply_mat(obj, key: str):
    obj.data.materials.append(material("M_" + key, PALETTE[key], metallic=0.15))
    return obj


def cube(name, loc, scale=(1, 1, 1), mat="neutral"):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return apply_mat(obj, mat)


def sphere(name, loc, radius=0.3, mat="neutral"):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=radius, location=loc)
    obj = bpy.context.object
    obj.name = name
    return apply_mat(obj, mat)


def cylinder_between(name, a, b, radius=0.06, mat="white"):
    a, b = Vector(a), Vector(b)
    d = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=radius, depth=d.length,
                                        location=(a + b) / 2)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = d.to_track_quat("Z", "Y")
    return apply_mat(obj, mat)


def torus(name, loc, major=1.0, minor=0.08, mat="neutral"):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
                                    major_segments=48, minor_segments=10, location=loc)
    obj = bpy.context.object
    obj.name = name
    return apply_mat(obj, mat)


def add_text(text: str, loc, size=0.38, align="CENTER"):
    bpy.ops.object.text_add(location=loc, rotation=(math.pi / 2, 0, 0))
    obj = bpy.context.object
    obj.data.body = text
    obj.data.align_x = align
    obj.data.size = size
    obj.data.extrude = 0.012
    apply_mat(obj, "white")
    return obj


def ground(width=14, depth=9):
    return cube("ground", (0, 0, -0.18), (width / 2, depth / 2, 0.15), "dark")


def camera_and_lights(target=(0, 0, 0), location=(11, -15, 11)):
    bpy.ops.object.camera_add(location=location)
    cam = bpy.context.object
    cam.data.lens = 52
    cam.rotation_euler = (Vector(target) - cam.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    for loc, energy, size in [((-7, -7, 12), 1500, 6), ((8, -2, 7), 1000, 5)]:
        bpy.ops.object.light_add(type="AREA", location=loc)
        light = bpy.context.object
        light.data.energy, light.data.shape, light.data.size = energy, "DISK", size
        light.rotation_euler = (Vector(target) - light.location).to_track_quat("-Z", "Y").to_euler()
    bpy.ops.object.light_add(type="AREA", location=(0, 7, 4))
    bpy.context.object.data.energy = 700
    bpy.context.object.data.color = (0.2, 0.4, 1.0)


def render_png(ctx: RunContext, suffix="main") -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    path = OUTPUT / f"{ctx.scene_id}_{suffix}.png"
    ctx.outputs.append(str(path.relative_to(ROOT)))
    if not DRY_RUN:
        bpy.context.scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)


def write_sidecar(ctx: RunContext) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    payload = {
        "scene_id": ctx.scene_id,
        "generator": f"scenes/{ctx.scene_id}.py",
        "framework": ctx.framework,
        "primitive": ctx.primitive,
        "parameters": ctx.parameters,
        "render": {
            "blender_version": bpy.app.version_string,
            "engine": scene.render.engine,
            "resolution": [scene.render.resolution_x, scene.render.resolution_y],
            "samples": SAMPLES,
            "seed": scene.get("deterministic_seed", 42),
            "camera": dict(location=list(scene.camera.location), lens=scene.camera.data.lens),
        },
        "checks": ctx.checks,
        "evidence": ctx.evidence,
        "outputs": ctx.outputs,
        "status": "pass" if ctx.checks and all(c["passed"] for c in ctx.checks) else "fail",
    }
    (OUTPUT / f"{ctx.scene_id}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def finish(ctx: RunContext, suffix="main") -> RunContext:
    render_png(ctx, suffix)
    write_sidecar(ctx)
    return ctx


def run_scene(build: Callable[[], RunContext], measure: Callable[[RunContext], None],
              render: Callable[[RunContext], None] | None = None) -> RunContext:
    ctx = build()
    measure(ctx)
    if render:
        render(ctx)
    else:
        finish(ctx)
    return ctx
