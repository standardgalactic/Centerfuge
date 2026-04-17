#!/usr/bin/env python3
"""
compose_generator.py — build new headless generators by symbolically composing
rsvp field operators. Each generated script is self-contained and reproducible.

Usage:
    python compose_generator.py [--count N] [--seed S] [--output-dir DIR] [--dry-run]

The composer samples the space of admissible field compositions rather than
constructing individual generators by hand. It is the first step toward
self-directed exploration of the RSVP operator algebra.
"""

from __future__ import annotations
import argparse
import json
import random
import textwrap
from pathlib import Path
from dataclasses import dataclass, field, asdict


# ---------------------------------------------------------------------------
# Symbolic field expression builders
# ---------------------------------------------------------------------------

@dataclass
class FieldExpr:
    """A symbolic description of a composed field, serialisable to JSON."""
    kind: str                          # "scalar" | "vector"
    op: str                            # the rsvp call that produces it
    components: list[FieldExpr] = field(default_factory=list)
    params: dict = field(default_factory=dict)

    def to_code(self) -> str:
        if self.components:
            inner = ", ".join(c.to_code() for c in self.components)
            return f"{self.op}({inner})"
        if self.params:
            kw = ", ".join(f"{k}={v!r}" for k, v in self.params.items())
            return f"{self.op}({kw})"
        return f"{self.op}()"


def sample_basin(rng: random.Random) -> FieldExpr:
    return FieldExpr(
        kind="scalar", op="rsvp.Basin().scalar",
        params={
            "center": (rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5), rng.uniform(-0.3, 0.3)),
            "amplitude": round(rng.uniform(0.6, 1.8), 3),
            "radius": round(rng.uniform(0.5, 2.0), 3),
        }
    )


def sample_harmonic(rng: random.Random) -> FieldExpr:
    return FieldExpr(
        kind="scalar", op="rsvp.HarmonicField().scalar",
        params={
            "weights": tuple(round(rng.uniform(0.1, 1.0), 3) for _ in range(3)),
            "frequencies": tuple(round(rng.uniform(0.5, 5.0), 3) for _ in range(3)),
            "phase": tuple(round(rng.uniform(0, 6.28), 3) for _ in range(3)),
            "amplitude": round(rng.uniform(0.1, 0.5), 3),
        }
    )


def sample_directional(rng: random.Random) -> FieldExpr:
    dx, dy, dz = rng.gauss(0, 0.3), rng.gauss(0, 0.3), rng.uniform(0.5, 1.5)
    return FieldExpr(
        kind="vector", op="rsvp.DirectionalBias().vector",
        params={
            "direction": (round(dx, 3), round(dy, 3), round(dz, 3)),
            "strength": round(rng.uniform(0.5, 1.5), 3),
            "curl": round(rng.uniform(0.0, 0.6), 3),
        }
    )


def sample_entropy_cap(rng: random.Random) -> FieldExpr:
    return FieldExpr(
        kind="cap", op="rsvp.EntropyCap",
        params={
            "threshold": round(rng.uniform(0.6, 2.0), 3),
            "softness": round(rng.uniform(3.0, 12.0), 3),
        }
    )


def compose_scalar(rng: random.Random, depth: int = 0) -> FieldExpr:
    """Recursively compose a scalar field expression."""
    max_depth = 2
    primitives = [sample_basin, sample_harmonic]

    if depth >= max_depth or rng.random() < 0.5:
        return rng.choice(primitives)(rng)

    n = rng.randint(2, 3)
    children = [compose_scalar(rng, depth + 1) for _ in range(n)]
    op = rng.choice(["rsvp.add_scalar_fields", "rsvp.mul_scalar_fields"])
    return FieldExpr(kind="scalar", op=op, components=children)


# ---------------------------------------------------------------------------
# Code generation
# ---------------------------------------------------------------------------

SCRIPT_TEMPLATE = '''\
#!/usr/bin/env python3
"""
generate_{name}.py
Auto-composed by compose_generator.py
Composition seed: {composition_seed}
Field expression: {phi_summary}
"""

from __future__ import annotations
import sys
import argparse
import random

def parse_args():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True)
    p.add_argument("--seed", type=int, default=0)
    return p.parse_args(argv)

args = parse_args()

import bpy
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rsvp

rng = random.Random(args.seed)

# --- composed scalar field ---
phi = {phi_expr}

# --- composed vector field ---
v_field = {v_expr}

# --- entropy cap ---
cap = {cap_expr}

# --- closure ---
closure = rsvp.capped_field(rsvp.closure_field(phi, v_field), cap)

print(f"[{name}] phi@origin={{phi(0,0,0):.4f}}  closure@origin={{closure(0,0,0):.4f}}")

# --- scene ---
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()

# --- growth path from field ---
path = rsvp.trace_growth_path(
    start=(0.0, 0.0, 0.0),
    direction_field=v_field,
    scalar_field=phi,
    step_size={step_size},
    steps={steps},
    attraction={attraction},
)

branches = rsvp.branch_paths(
    root_path=path,
    direction_field=v_field,
    branch_probability={branch_prob},
    max_branches={max_branches},
    lateral_strength={lateral_strength},
    rng=rng,
)

print(f"[{name}] trunk={{len(path)}} pts  branches={{len(branches)}}")

def path_to_curve(pts, name, bevel, col):
    cd = bpy.data.curves.new(name, "CURVE")
    cd.dimensions = "3D"
    cd.bevel_depth = bevel
    cd.bevel_resolution = 3
    cd.use_fill_caps = True
    sp = cd.splines.new("NURBS")
    sp.points.add(len(pts) - 1)
    for i, (x, y, z) in enumerate(pts):
        sp.points[i].co = (x, y, z, 1.0)
    sp.use_endpoint_u = True
    obj = bpy.data.objects.new(name, cd)
    col.objects.link(obj)
    return obj

col = bpy.data.collections.new("{name}")
bpy.context.scene.collection.children.link(col)

path_to_curve(path, "trunk", {trunk_bevel}, col)
for i, b in enumerate(branches):
    path_to_curve(b, f"branch_{{i:03d}}", {branch_bevel}, col)

cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
bpy.context.scene.collection.objects.link(cam)
cam.location = (4.0, -4.0, 3.0)
cam.rotation_euler = (1.1, 0.0, 0.785)
bpy.context.scene.camera = cam

bpy.ops.wm.save_as_mainfile(filepath=args.output)
print(f"[{name}] saved to {{args.output}}")
'''


@dataclass
class CompositionSpec:
    name: str
    composition_seed: int
    phi_expr: str
    phi_expr_tree: dict
    v_expr: str
    v_expr_tree: dict
    cap_expr: str
    step_size: float
    steps: int
    attraction: float
    branch_prob: float
    max_branches: int
    lateral_strength: float
    trunk_bevel: float
    branch_bevel: float


def compose_spec(name: str, composition_seed: int) -> CompositionSpec:
    rng = random.Random(composition_seed)

    phi_tree = compose_scalar(rng)
    v_tree = sample_directional(rng)
    cap_tree = sample_entropy_cap(rng)

    # Build callable code strings from symbolic expressions
    def basin_call(p):
        return (
            f"rsvp.Basin("
            f"center={p['center']}, "
            f"amplitude={p['amplitude']}, "
            f"radius={p['radius']}"
            f").scalar()"
        )

    def harmonic_call(p):
        return (
            f"rsvp.HarmonicField("
            f"weights={p['weights']}, "
            f"frequencies={p['frequencies']}, "
            f"phase={p['phase']}, "
            f"amplitude={p['amplitude']}"
            f").scalar()"
        )

    def directional_call(p):
        return (
            f"rsvp.DirectionalBias("
            f"direction={p['direction']}, "
            f"strength={p['strength']}, "
            f"curl={p['curl']}"
            f").vector()"
        )

    def cap_call(p):
        return (
            f"rsvp.EntropyCap("
            f"threshold={p['threshold']}, "
            f"softness={p['softness']}"
            f")"
        )

    def render_scalar(expr: FieldExpr) -> str:
        if expr.op in ("rsvp.add_scalar_fields", "rsvp.mul_scalar_fields"):
            inner = ", ".join(render_scalar(c) for c in expr.components)
            return f"{expr.op}({inner})"
        if "Basin" in expr.op:
            return basin_call(expr.params)
        if "Harmonic" in expr.op:
            return harmonic_call(expr.params)
        return f"{expr.op}()"

    phi_code = render_scalar(phi_tree)
    v_code = directional_call(v_tree.params)
    cap_code = cap_call(cap_tree.params)

    return CompositionSpec(
        name=name,
        composition_seed=composition_seed,
        phi_expr=phi_code,
        phi_expr_tree=asdict(phi_tree),
        v_expr=v_code,
        v_expr_tree=asdict(v_tree),
        cap_expr=cap_code,
        step_size=round(rng.uniform(0.03, 0.08), 3),
        steps=rng.randint(40, 120),
        attraction=round(rng.uniform(0.1, 0.5), 3),
        branch_prob=round(rng.uniform(0.05, 0.20), 3),
        max_branches=rng.randint(4, 16),
        lateral_strength=round(rng.uniform(0.4, 0.9), 3),
        trunk_bevel=round(rng.uniform(0.04, 0.12), 3),
        branch_bevel=round(rng.uniform(0.01, 0.05), 3),
    )


def emit_script(spec: CompositionSpec, out_dir: Path) -> Path:
    code = SCRIPT_TEMPLATE.format(
        name=spec.name,
        composition_seed=spec.composition_seed,
        phi_summary=spec.phi_expr[:60] + "...",
        phi_expr=spec.phi_expr,
        v_expr=spec.v_expr,
        cap_expr=spec.cap_expr,
        step_size=spec.step_size,
        steps=spec.steps,
        attraction=spec.attraction,
        branch_prob=spec.branch_prob,
        max_branches=spec.max_branches,
        lateral_strength=spec.lateral_strength,
        trunk_bevel=spec.trunk_bevel,
        branch_bevel=spec.branch_bevel,
    )
    path = out_dir / f"generate_{spec.name}.py"
    path.write_text(code, encoding="utf-8")
    path.chmod(0o755)

    # Sidecar JSON — full composition record, re-runnable
    sidecar = {
        "schema": "rsvp-composition-v1",
        "name": spec.name,
        "composition_seed": spec.composition_seed,
        "phi_expr": spec.phi_expr,
        "phi_expr_tree": spec.phi_expr_tree,
        "v_expr": spec.v_expr,
        "cap_expr": spec.cap_expr,
        "growth_params": {
            "step_size": spec.step_size,
            "steps": spec.steps,
            "attraction": spec.attraction,
            "branch_prob": spec.branch_prob,
            "max_branches": spec.max_branches,
            "lateral_strength": spec.lateral_strength,
        },
    }
    sidecar_path = out_dir / f"generate_{spec.name}.composition.json"
    sidecar_path.write_text(json.dumps(sidecar, indent=2) + "\n", encoding="utf-8")

    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Compose new rsvp generator scripts")
    parser.add_argument("--count", type=int, default=5, help="Number of generators to emit")
    parser.add_argument("--seed", type=int, default=0, help="Master seed for composition RNG")
    parser.add_argument("--output-dir", default=".", help="Directory for emitted scripts")
    parser.add_argument("--dry-run", action="store_true", help="Print composition specs without writing")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    master_rng = random.Random(args.seed)

    for i in range(args.count):
        composition_seed = master_rng.randint(0, 2**31)
        name = f"auto_{i:03d}"
        spec = compose_spec(name, composition_seed)

        if args.dry_run:
            print(f"[compose] {name}  seed={composition_seed}")
            print(f"  phi:    {spec.phi_expr[:80]}")
            print(f"  v:      {spec.v_expr[:80]}")
            print(f"  steps:  {spec.steps}  attraction: {spec.attraction}")
        else:
            path = emit_script(spec, out_dir)
            print(f"[compose] {path}")


if __name__ == "__main__":
    main()
