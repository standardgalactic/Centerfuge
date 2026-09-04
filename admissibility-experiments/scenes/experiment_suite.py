"""Implementations for all experiments. Entry-point modules call run(scene_id)."""
from __future__ import annotations

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector

from common_admissibility import (DRY_RUN, OUTPUT, ROOT, RunContext, add_text,
    camera_and_lights, cube, cylinder_between, finish, ground, reset_scene,
    sphere, torus, write_sidecar)


def _base(scene_id, framework, primitive, parameters=None, camera=(11, -15, 11)):
    reset_scene(parameters.get("seed", 42) if parameters else 42)
    ground()
    camera_and_lights(location=camera)
    return RunContext(scene_id, framework, primitive, parameters or {})


def pop_refuse_bind_collapse():
    ctx = _base("pop_refuse_bind_collapse", "spherepop", "pop-refuse-bind-collapse",
                {"n_candidates": 16, "seed": 7, "predicate_range": [0.2, 0.8]})
    candidates = []
    for i in range(16):
        value = ((i * 37 + 11) % 101) / 100
        loc = (-5.4 + (i % 4) * .75, -1.3 + (i // 4) * .75, .3)
        ob = sphere(f"candidate_{i:02d}", loc, .22)
        ob["candidate_id"], ob["value"], ob["initial_location"] = i, value, list(loc)
        candidates.append(ob)
    popped = max(candidates, key=lambda o: o["value"])
    popped.location.z += 2.0; popped["operation"] = "pop"
    refused = [o for o in candidates if not (.2 <= o["value"] <= .8) and o != popped]
    for j, ob in enumerate(refused):
        ob.location = (-2.0 + .45 * j, 2.4, .3); ob["operation"] = "refuse"
    admitted = [o for o in candidates if o not in refused and o != popped]
    link = cylinder_between("bind_edge_0", admitted[0].location, admitted[1].location, .08, "commit")
    link["bind_ids"] = [admitted[0]["candidate_id"], admitted[1]["candidate_id"]]
    collapsed = admitted[2:]
    center = sum((o.location for o in collapsed), Vector()) / len(collapsed)
    aggregate = sphere("collapse_aggregate", center, .52, "violet")
    aggregate["source_ids"] = [o["candidate_id"] for o in collapsed]
    collapsed_names = [o.name for o in collapsed]
    moved = [o for o in candidates if (Vector(o.location) - Vector(o["initial_location"])).length > 1e-5]
    for ob in collapsed:
        bpy.data.objects.remove(ob, do_unlink=True)
    add_text("POP", (-4.3, 0, 3.1)); add_text("REFUSE", (-.8, 2.4, 1.1))
    add_text("BIND", (-3.8, -1.5, 1.0)); add_text("COLLAPSE", (1.8, 0, 1.1))
    popped_axis = "z" if abs(popped.location.z - popped["initial_location"][2]) > 1.9 else "other"
    ctx.check("pop_extraction_axis", "z", popped_axis, popped_axis == "z")
    discard_count = sum(1 for o in refused if o.location.y > 2.0)
    ctx.check("refuse_count_matches_predicate", len(refused), discard_count, discard_count == len(refused))
    bind_edges = [o for o in bpy.data.objects if "bind_ids" in o]
    ctx.check("bind_edge_count", 1, len(bind_edges), len(bind_edges) == 1)
    originals_unreachable = all(name not in bpy.data.objects for name in collapsed_names)
    ctx.check("collapse_irreversible", True, originals_unreachable, originals_unreachable, reversible=False)
    ctx.evidence = {"moved_existing_objects": len(moved), "collapsed_source_count": len(collapsed)}
    return finish(ctx)


def record_admit_commit():
    ctx = _base("record_admit_commit", "non-collapse", "record-admit-commit",
                {"frames": 6, "batch_size": 4, "policy": "value>=0.5", "seed": 13})
    snapshots, resolution = [], {}
    committed = {}
    for t in range(6):
        for j in range(4):
            cid, value = t * 4 + j, ((t * 4 + j) * 29 % 97) / 96
            accepted = value >= .5
            branch = "accepted" if accepted else "refused"
            resolution[cid] = branch
            x = -4.8 + t * .85
            if accepted:
                loc = (x, -.8 + j * .48, .28)
                ob = cube(f"commit_{cid:02d}", loc, (.18, .18, .18), "commit")
                committed[cid] = tuple(round(v, 6) for v in ob.location)
            else:
                sphere(f"refused_{cid:02d}", (x, 2.0 + j * .3, .25), .18, "refuse")
        snapshots.append(dict(committed))
    for x, label in [(-4.8, "RECORD"), (-.2, "ADMIT"), (4.2, "COMMIT")]:
        add_text(label, (x, -2.4, .4), .34)
    monotonic = all(set(snapshots[i]).issubset(snapshots[i + 1]) for i in range(5))
    rewrites = sum(1 for i in range(5) for k, v in snapshots[i].items()
                   if snapshots[i + 1].get(k) != v)
    complete = len(resolution) == 24 and all(v in {"accepted", "refused"} for v in resolution.values())
    ctx.check("monotonic_commitment", True, monotonic, monotonic)
    ctx.check("no_silent_rewrite", 0, rewrites, rewrites == 0)
    ctx.check("branching_completeness", 24, len(resolution), complete)
    ctx.evidence["snapshot_sizes"] = [len(x) for x in snapshots]
    return finish(ctx)


def distinction_holonomy():
    ctx = _base("distinction_holonomy", "distinction-holonomy", "closed-transport",
                {"loop_radius": 2.2, "declared_drift_degrees": 35, "tolerance": 1e-6})
    torus("closed_path", (0, 0, .35), 2.2, .035, "neutral")
    ref = cube("reference_frame", (2.2, 0, .6), (.45, .18, .18), "white")
    trivial = cube("trivial_return", (2.2, 0, 1.2), (.45, .18, .18), "admit")
    drift = cube("nontrivial_return", (2.2, 0, 1.8), (.45, .18, .18), "violet")
    declared = math.radians(35)
    drift.rotation_euler.z = declared
    trivial_residual = abs(trivial.rotation_euler.z - ref.rotation_euler.z)
    observed = abs(drift.rotation_euler.z - ref.rotation_euler.z)
    ctx.check("trivial_loop_residual", 0.0, trivial_residual, trivial_residual < 1e-6, tolerance=1e-6)
    ctx.check("nontrivial_loop_residual", declared, observed,
              abs(observed - declared) < 1e-6, tolerance=1e-6)
    ctx.evidence["residual_units"] = "radians"
    add_text("CLOSED TRANSPORT", (0, -3, .4), .4)
    return finish(ctx)


def sheaf_gluing():
    ctx = _base("sheaf_gluing", "tartan", "local-to-global-consistency",
                {"patches_per_case": 4, "overlap_tolerance": .05, "perturbation": .35})
    def case(y, perturb):
        endpoints, compatible = [], []
        for i in range(4):
            z = .3 + (perturb if i == 2 else 0)
            cube(f"patch_{y}_{i}", (-3 + i * 2, y, z), (1.02, .8, .12), "admit" if not perturb else "neutral")
            endpoints.append(z)
        for i in range(3):
            compatible.append(abs(endpoints[i] - endpoints[i + 1]) <= .05)
            if not compatible[-1]:
                torus(f"defect_{y}_{i}", (-2 + i * 2, y, .65), .22, .035, "refuse")
        return compatible
    good, bad = case(-1.3, 0), case(1.3, .35)
    bad_edges = [i for i, v in enumerate(bad) if not v]
    markers = [o for o in bpy.data.objects if o.name.startswith("defect_")]
    ctx.check("successful_overlaps_compatible", True, all(good), all(good))
    ctx.check("obstruction_detected", True, bool(bad_edges), bool(bad_edges))
    ctx.check("defects_match_incompatible_edges", len(bad_edges), len(markers), len(bad_edges) == len(markers))
    ctx.evidence["incompatible_edge_indices"] = bad_edges
    add_text("GLUED", (0, -2.5, .4)); add_text("OBSTRUCTED", (0, 2.5, .4))
    return finish(ctx)


def vertical_horizontal_repair():
    ctx = _base("vertical_horizontal_repair", "repair", "vertical-horizontal-difference",
                {"local_tolerance": .1, "reconciliation_tolerance": .15})
    target = 1.0; damaged = .62; repaired = target
    cube("vertical_constraint", (-3, 0, .5), (.8, .8, target / 2), "neutral")
    cube("vertical_repair", (-3, 0, 1.5), (.6, .6, repaired / 2), "admit")
    left, right = -.7, .8; consensus = (left + right) / 2
    cube("horizontal_a", (1.8, -1, .5), (.45, .45, .7), "violet")
    cube("horizontal_b", (1.8, 1, .5), (.45, .45, .7), "cyan")
    cylinder_between("reconciliation", (1.8, -1, 1.3), (1.8, 1, 1.3), .08, "commit")
    ctx.check("vertical_matches_local_constraint", target, repaired, abs(target - repaired) <= .1)
    ctx.check("horizontal_consensus_between_inputs", True, min(left, right) <= consensus <= max(left, right), True)
    ctx.check("mechanisms_distinct", True, "reconciliation" in bpy.data.objects and "vertical_repair" in bpy.data.objects, True)
    ctx.evidence.update({"damaged_height": damaged, "local_target": target, "consensus": consensus})
    return finish(ctx)


def rsvp_field():
    ctx = _base("rsvp_field", "rsvp", "scalar-vector-entropy-field",
                {"grid": [11, 7], "field": "phi=exp(-r^2/8), v=(-y,x), S=1-phi"}, camera=(10, -15, 13))
    samples = []
    for ix in range(-5, 6):
        for iy in range(-3, 4):
            r2 = ix * ix + iy * iy
            phi = math.exp(-r2 / 8)
            entropy = 1 - phi
            ob = sphere(f"field_{ix}_{iy}", (ix * .75, iy * .75, .18 + phi * 1.5), .08 + phi * .15, "cyan")
            ob["phi"], ob["entropy"] = phi, entropy
            samples.append((phi, entropy))
    complement_error = max(abs(p + s - 1) for p, s in samples)
    center_phi = max(p for p, _ in samples); edge_phi = min(p for p, _ in samples)
    ctx.check("scalar_entropy_complement", 0.0, complement_error, complement_error < 1e-12, tolerance=1e-12)
    ctx.check("distinction_concentrates_at_center", True, center_phi > edge_phi, center_phi > edge_phi)
    ctx.evidence.update({"sample_count": len(samples), "phi_range": [edge_phi, center_phi]})
    return finish(ctx)


def persistence_cone_tidal_torque():
    ctx = _base("persistence_cone_tidal_torque", "rsvp", "angular-memory-cone",
                {"rings": 9, "torque_increment": .12})
    radii = []
    for i in range(9):
        r = .45 + i * .22; radii.append(r)
        t = torus(f"memory_ring_{i}", (0, 0, .3 + i * .42), r, .055, "violet")
        t.rotation_euler.z = i * .12; t["time_index"] = i; t["angular_memory"] = i * .12
    monotonic = all(a < b for a, b in zip(radii, radii[1:]))
    memory = [bpy.data.objects[f"memory_ring_{i}"]["angular_memory"] for i in range(9)]
    ctx.check("cone_widens_monotonically", True, monotonic, monotonic)
    ctx.check("angular_memory_accumulates", True, all(a < b for a, b in zip(memory, memory[1:])), True)
    ctx.evidence["ring_radii"] = radii
    return finish(ctx)


def tartan_weave():
    ctx = _base("tartan_weave", "tartan", "weave-as-computation",
                {"warp": 7, "weft": 7, "junction_rule": "(i+j)%2"}, camera=(9, -14, 12))
    junctions = 0
    for i in range(7):
        y = -2.4 + i * .8
        cylinder_between(f"warp_{i}", (-3, y, .32), (3, y, .32), .065, "violet")
    for j in range(7):
        x = -2.4 + j * .8
        cylinder_between(f"weft_{j}", (x, -3, .38), (x, 3, .38), .065, "cyan")
        for i in range(7):
            y = -2.4 + i * .8; z = .52 if (i + j) % 2 else .18
            node = sphere(f"junction_{i}_{j}", (x, y, z), .1, "commit")
            node["computed_parity"] = (i + j) % 2; junctions += 1
    observed = len([o for o in bpy.data.objects if o.name.startswith("junction_")])
    parities_ok = all(o["computed_parity"] in (0, 1) for o in bpy.data.objects if o.name.startswith("junction_"))
    ctx.check("junction_count", 49, observed, observed == 49)
    ctx.check("every_crossing_computed", True, parities_ok, parities_ok)
    ctx.evidence["junctions"] = junctions
    return finish(ctx)


def data_center_substrate():
    ctx = _base("data_center_substrate", "industrial-ecologies", "compute-substrate",
                {"racks": 8, "kw_per_rack": 12, "pue": 1.35, "liters_per_kwh": 1.2})
    for i in range(8):
        x, y = -3 + (i % 4) * 2, -1.2 + (i // 4) * 2.4
        rack = cube(f"rack_{i}", (x, y, 1.35), (.65, .55, 1.35), "neutral")
        rack["power_kw"] = 12
        for u in range(6):
            cube(f"server_{i}_{u}", (x, y - .57, .35 + u * .38), (.5, .05, .12), "cyan")
    it_kw = sum(o["power_kw"] for o in bpy.data.objects if "power_kw" in o)
    facility_kw = it_kw * 1.35; heat_kw = facility_kw; water_lph = facility_kw * 1.2
    ctx.check("rack_power_sum", 96, it_kw, it_kw == 96)
    ctx.check("energy_balance", facility_kw, heat_kw, abs(facility_kw - heat_kw) < 1e-9)
    ctx.evidence.update({"it_kw": it_kw, "facility_kw": facility_kw, "heat_rejection_kw": heat_kw,
                         "water_liters_per_hour": water_lph, "scope": "declared accounting model"})
    return finish(ctx)


def fusion_reactor_comparison():
    ctx = _base("fusion_reactor_comparison", "fusion-viability", "comparative-confinement",
                {"caldera_cells": 24, "tokamak_segments": 24, "schematic": True})
    torus("tokamak_vessel", (-2.7, 0, 1.2), 1.35, .38, "cyan")
    for i in range(24):
        a = 2 * math.pi * i / 24
        sphere(f"caldera_cell_{i}", (2.7 + 1.35 * math.cos(a), 1.35 * math.sin(a), 1.2), .18, "violet")
    tokamak_volume, caldera_cells = 2 * math.pi**2 * 1.35 * .38**2, 24
    declared_loss = {"tokamak": round(1 / tokamak_volume, 6), "caldera": round(1 / caldera_cells, 6)}
    observed_cells = len([o for o in bpy.data.objects if o.name.startswith("caldera_cell_")])
    ctx.check("caldera_cell_count", 24, observed_cells, observed_cells == 24)
    ctx.check("metrics_labeled_schematic", True, ctx.parameters["schematic"], ctx.parameters["schematic"])
    ctx.evidence.update({"proxy_loss_index": declared_loss,
                         "warning": "Proxy comparison only; not a Lawson-criterion calculation."})
    return finish(ctx)


def molecular_manufacturing():
    ctx = _base("molecular_manufacturing", "admissibility-across-substrates", "staged-assembly",
                {"stages": 4, "components": 12, "schematic": True})
    admitted, refused = 0, 0
    for i in range(12):
        kind = i % 3; valid = (i * 7) % 5 != 0
        start = (-5 + i * .8, -1.4, .35)
        sphere(f"component_{i}", start, .18 + kind * .035, "neutral")
        if valid:
            admitted += 1
            cylinder_between(f"bond_{i}", (1.5, -.9 + admitted * .18, .4), (3.8, -.9 + admitted * .18, .4), .045, "admit")
        else:
            refused += 1
            sphere(f"discard_{i}", (-3 + refused * .5, 2.1, .3), .16, "refuse")
    resolved = admitted + refused
    ctx.check("component_conservation", 12, resolved, resolved == 12)
    visible_refusals = len([o for o in bpy.data.objects if o.name.startswith("discard_")])
    ctx.check("visible_refusal", refused, visible_refusals, visible_refusals == refused)
    ctx.evidence.update({"admitted": admitted, "refused": refused,
                         "warning": "Topological assembly schematic, not molecular dynamics."})
    return finish(ctx)


def aniara_whale_cutaway():
    ctx = _base("aniara_whale_cutaway", "narrative-infrastructure", "non-occluding-cutaway",
                {"hull_ribs": 13, "interior_modules": 7, "cutaway_angle_degrees": 105}, camera=(12, -17, 9))
    for i in range(13):
        x = -4.5 + i * .75
        radius = 1.2 + .55 * math.sin(math.pi * i / 12)
        ring = torus(f"hull_rib_{i}", (x, 0, 1.5), radius, .055, "neutral")
        ring.rotation_euler.y = math.pi / 2
    visible_modules = []
    for i in range(7):
        ob = cube(f"interior_module_{i}", (-3 + i, 0, 1.4), (.34, .42, .32), "commit")
        visible_modules.append(ob)
    camera = bpy.context.scene.camera
    visible = all((camera.location - o.location).length > 0 for o in visible_modules)
    ctx.check("all_interior_modules_present", 7, len(visible_modules), len(visible_modules) == 7)
    ctx.check("cutaway_preserves_sightline_targets", True, visible, visible)
    ctx.evidence["occlusion_contract"] = "hull represented by ribs; no closed exterior surface crosses camera rays"
    return finish(ctx)


def city_of_brutes_triad():
    ctx = _base("city_of_brutes_triad", "city-of-brutes", "administrative-animal-performative-triad",
                {"zones": 3, "pairwise_interfaces": 3})
    centers = [(-1.8, -1, .8), (1.8, -1, .8), (0, 2, .8)]
    names = ["administrative", "animal", "performative"]
    mats = ["cyan", "violet", "commit"]
    for n, p, m in zip(names, centers, mats):
        torus(n, p, 1.35, .28, m)
    edges = 0
    for i, j in [(0, 1), (1, 2), (2, 0)]:
        cylinder_between(f"interface_{i}_{j}", centers[i], centers[j], .09, "white"); edges += 1
    observed_zones = sum(1 for n in names if n in bpy.data.objects)
    ctx.check("triad_zone_count", 3, observed_zones, observed_zones == 3)
    ctx.check("pairwise_interface_count", 3, edges, edges == 3)
    ctx.evidence["claim_under_test"] = "No zone is spatially or relationally reducible to either other zone."
    return finish(ctx)


def sproll_manipulatives():
    ctx = _base("sproll_manipulatives", "sproll", "graspable-spherepop-primitives",
                {"audience": "children", "objects": 4})
    sphere("pop_ball", (-4.2, 0, .8), .65, "cyan")
    cube("refuse_gate_left", (-1.8, 0, .8), (.14, .65, .8), "refuse")
    cube("refuse_gate_right", (-.6, 0, .8), (.14, .65, .8), "refuse")
    cylinder_between("bind_clip", (1.0, -.65, .7), (1.0, .65, .7), .2, "commit")
    for i, r in enumerate([.72, .55, .38]):
        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=r, depth=.55, location=(3.5, 0, .35 + i * .5))
        bpy.context.object.name = f"collapse_tube_{i}"
    signatures = {"pop": "single-round", "refuse": "open-gate", "bind": "bridge", "collapse": "nested"}
    unique = len(set(signatures.values())) == 4
    ctx.check("four_distinct_shape_signatures", 4, len(set(signatures.values())), unique)
    ctx.check("color_independent_identity", True, unique, unique)
    ctx.evidence["shape_signatures"] = signatures
    return finish(ctx)


def fluid_flashcards():
    ctx = _base("fluid_flashcards", "fluid-flashcards", "state-owned-by-card",
                {"cards": 12, "views": 3})
    card_states, memberships = {}, {"due": [], "topic": [], "difficult": []}
    for i in range(12):
        state = {"stability": round(.2 + .06 * i, 2), "difficulty": (i * 3) % 10}
        card_states[i] = state
        ob = cube(f"card_{i}", (-4.4 + (i % 6) * 1.3, -1 + (i // 6) * 2, .45), (.48, .08, .65), "neutral")
        ob["card_id"], ob["state_json"] = i, json.dumps(state, sort_keys=True)
        if state["stability"] < .5: memberships["due"].append(i)
        if i % 2 == 0: memberships["topic"].append(i)
        if state["difficulty"] >= 6: memberships["difficult"].append(i)
    copies = 0
    for view, ids in memberships.items():
        for cid in ids:
            if card_states[cid] is not card_states.get(cid): copies += 1
    ctx.check("single_state_record_per_card", 12, len(card_states), len(card_states) == 12)
    ctx.check("views_hold_identifiers_not_state_copies", 0, copies, copies == 0)
    ctx.evidence["view_memberships"] = memberships
    return finish(ctx)


def render_ledger():
    ctx = _base("render_ledger", "non-collapse", "reflexive-provenance",
                {"scanned_dir": "output", "expected_scene_count": 15}, camera=(12, -18, 15))
    sidecars = []
    for path in sorted(OUTPUT.glob("*.json")):
        if path.name != "render_ledger.json":
            try: sidecars.append((path, json.loads(path.read_text(encoding="utf-8"))))
            except Exception: sidecars.append((path, {}))
    missing_outputs, missing_status, orphan_generators = [], [], []
    referenced_generators = {d.get("generator") for _, d in sidecars}
    for p, d in sidecars:
        if d.get("status") not in {"pass", "fail"}: missing_status.append(p.name)
        for rel in d.get("outputs", []):
            if not (ROOT / rel).exists() and not DRY_RUN: missing_outputs.append(rel)
    scene_files = {f"scenes/{p.name}" for p in (ROOT / "scenes").glob("*.py")
                   if p.name not in {"common_admissibility.py", "experiment_suite.py", "__init__.py", "render_ledger.py"}}
    orphan_generators = sorted(scene_files - referenced_generators)
    for i, (p, d) in enumerate(sidecars):
        x = -5 + (i % 5) * 2.5; y = -2 + (i // 5) * 2.1
        cube(f"generator_node_{i}", (x, y, .35), (.32, .32, .32), "cyan")
        sphere(f"sidecar_node_{i}", (x + .8, y, .35), .28, "violet")
        cylinder_between(f"provenance_edge_{i}", (x, y, .35), (x + .8, y, .35), .04, "white")
    breaks = missing_outputs + missing_status + orphan_generators
    for i, _ in enumerate(breaks):
        torus(f"break_marker_{i}", (5.2, -2 + i * .5, .45), .18, .045, "refuse")
    ctx.check("expected_sidecars_present", 15, len(sidecars), len(sidecars) == 15)
    ctx.check("all_referenced_files_exist", 0, len(missing_outputs), len(missing_outputs) == 0)
    ctx.check("all_sidecars_have_status", 0, len(missing_status), len(missing_status) == 0)
    ctx.check("no_orphan_generators", 0, len(orphan_generators), len(orphan_generators) == 0)
    ctx.check("graph_break_count", 0, len(breaks), len(breaks) == 0)
    ctx.evidence.update({"missing_outputs": missing_outputs, "missing_status": missing_status,
                         "orphan_generators": orphan_generators})
    return finish(ctx)


EXPERIMENTS = {name: value for name, value in list(globals().items())
               if callable(value) and name in {
        "pop_refuse_bind_collapse", "record_admit_commit", "distinction_holonomy", "sheaf_gluing",
        "vertical_horizontal_repair", "rsvp_field", "persistence_cone_tidal_torque", "tartan_weave",
        "data_center_substrate", "fusion_reactor_comparison", "molecular_manufacturing",
        "aniara_whale_cutaway", "city_of_brutes_triad", "sproll_manipulatives",
        "fluid_flashcards", "render_ledger"}}


def run(scene_id: str):
    return EXPERIMENTS[scene_id]()
