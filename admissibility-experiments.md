# Admissibility Experiments — First Suite Specification

**Related suite:** [Centerfuge headless Blender models](headless_blender/README.md) — the fail-loud, non-occlusion, and provenance-manifest conventions this document's shared harness extends (`common.py`'s `verify_image_not_degenerate`, `verify_visibility`, and `write_manifest_entry`) are already implemented there for the Centerfuge scenes; `common_admissibility.py` should reuse or mirror them rather than re-deriving the same checks independently.

**Scope.** Five scenes: Pop/Refuse/Bind/Collapse, Record/Admit/Commit, Distinction Holonomy, Sheaf Gluing, Render Ledger (self-inspection). This suite establishes the visual operator vocabulary; Industrial Ecologies and future application suites are built atop it, not alongside it. Each scene's script must generate its own check data from the same geometry/measurement it renders — no manually entered pass/fail.

**Shared conventions across all five scenes:**
- Each scene lives at `scenes/<scene_id>.py`, importable and runnable standalone via `blender --background --python scenes/<scene_id>.py`.
- Each scene writes exactly one sidecar JSON to `output/<scene_id>.json` and one or more PNGs to `output/<scene_id>_*.png`.
- Each scene's `checks` array entries are computed from measured scene state, not asserted. A scene module should expose a `measure()` function separable from `build()` and `render()`, so checks can in principle be re-run against a saved `.blend` without re-rendering.
- `status` is `"pass"` only if every entry in `checks` has `passed: true`; otherwise `"fail"`, and the failing render is retained (never deleted or overwritten) as a diagnostic artifact.
- A failing run must still exit 0 at the process level (per your earlier fail-loud fix, the *runner* fails loudly by checking `status`, not by the scene process crashing) — this keeps the distinction between "the scene ran and detected an inadmissible result" and "the scene itself broke."

---

## 1. Pop / Refuse / Bind / Collapse

**Goal.** Four geometrically distinct operations over the same candidate population, recognizable by shape/motion alone.

**Script structure**
- `build_population(n, seed)`: generate `n` candidate primitives (e.g. small icospheres) at randomized positions within a bounding volume, each tagged with a custom property `candidate_id` and an admissibility predicate (e.g. a scalar "charge" value computed at creation time, not attached arbitrarily).
- `op_pop(population)`: select the single candidate whose scalar value is extremal (max or min) among an otherwise-underdetermined set, and *extract* it — move it out of the population volume along a distinct axis, scale it up slightly, leave the rest untouched. Visual signature: one object detaches and grows; nothing else moves.
- `op_refuse(population)`: identify candidates failing a stated predicate (e.g. scalar value outside `[lo, hi]`), and visibly eject them — apply an outward radial velocity/keyframe sending them off-frame or into a "discard" zone geometry (e.g. a red-tinted bin mesh), rather than deleting them silently. Visual signature: rejected objects move to a distinct discard region; admitted ones stay put.
- `op_bind(population)`: select two admitted candidates and create an explicit joining structure (a constraint or a generated connector mesh — e.g. a cylinder or curve) between them, then optionally parent them so they move as a unit under a subsequent transform. Visual signature: a new connecting geometry appears between exactly two objects; no other pairs gain one.
- `op_collapse(population)`: take the remaining possibility space (unresolved candidates) and irreversibly reduce it — e.g. merge all remaining unbound candidates into a single mesh via boolean union or a particle-to-mesh convert, deleting the originals. This step must be logged in the sidecar as irreversible (a `reversible: false` flag on this check), distinct from refuse (which is reversible in principle — refused candidates still exist off-frame).
- Each operation renders its own frame/sub-image (`_pop.png`, `_refuse.png`, `_bind.png`, `_collapse.png`) plus a combined 4-panel comparison image.

**Admissibility check.** Since the stated goal is recognizability *without labels or color*, the check cannot be "does it look right" — it must be structural:
- `pop_check`: exactly one object's transform differs from its pre-op transform beyond a small epsilon, and it differs along the axis reserved for extraction (not a random axis).
- `refuse_check`: the count of objects in the discard region equals the count of candidates failing the predicate, computed from the same predicate function used to build the population (not re-declared).
- `bind_check`: exactly one new edge/constraint exists in the scene graph between exactly two candidate objects, and no other pair has one.
- `collapse_check`: the number of distinct mesh-data blocks after the operation is strictly less than before, and the deleted originals are unreachable (not just hidden) in the resulting `.blend`.

**Sidecar schema (extends shared shape)**
```json
{
  "scene_id": "pop-refuse-bind-collapse",
  "generator": "scenes/pop_refuse_bind_collapse.py",
  "framework": "spherepop",
  "primitive": "all-four",
  "parameters": {"n_candidates": 24, "seed": 7, "predicate_range": [0.2, 0.8]},
  "checks": [
    {"name": "pop_extraction_axis", "expected": "z", "observed": "z", "passed": true},
    {"name": "refuse_count_matches_predicate", "expected": 6, "observed": 6, "passed": true},
    {"name": "bind_edge_count", "expected": 1, "observed": 1, "passed": true},
    {"name": "collapse_irreversible", "expected": true, "observed": true, "passed": true, "reversible": false}
  ],
  "outputs": ["output/pop.png", "output/refuse.png", "output/bind.png", "output/collapse.png", "output/combined.png"],
  "status": "pass"
}
```

---

## 2. Record / Admit / Commit

**Goal.** Temporal asymmetry: recorded candidates stay revisable, admission branches visibly, committed structure grows monotonically.

**Script structure**
- Animate across `T` frames. At each frame `t`, a new batch of candidates is *recorded* — added to a "pending" geometry group, rendered in a neutral/translucent material to signal revisability.
- A checkpoint gate function `admit(candidate, policy)` evaluates each pending candidate against a stated policy (e.g. scalar threshold, or a spatial containment test) and moves it to one of two destination groups: `accepted` or `refused`, each with a distinct, fixed material (not just per-frame color drift).
- Accepted candidates are then folded into a `committed` structure — e.g. appended as new vertices/instances to a single growing mesh (an accumulating point cloud or lattice) that is *only ever added to*, never rebuilt from scratch each frame.
- Critically: the script must snapshot the committed structure's vertex/object list at every frame and store it, so the monotonicity check can compare frame `t` to `t+1` directly from stored state rather than from visual inspection.

**Admissibility check.** Stated explicitly as monotonicity:
- For every frame `t` from 0 to `T-1`: the set of committed elements at `t` must be a subset of the committed elements at `t+1`, and every element present at `t` must be positionally and structurally unchanged at `t+1` (no silent rewrite of earlier members).
- A second check confirms branching completeness: every recorded candidate at each frame ends up in exactly one of `accepted` or `refused` — none remain permanently "pending" past a stated grace period, and none appear in both.

**Sidecar schema**
```json
{
  "scene_id": "record-admit-commit",
  "generator": "scenes/record_admit_commit.py",
  "framework": "non-collapse",
  "primitive": "record-admit-commit",
  "parameters": {"frames": 30, "batch_size": 5, "policy": "scalar_threshold>=0.5"},
  "checks": [
    {"name": "monotonicity_frame_0_to_29", "expected": "committed(t) subset committed(t+1) for all t", "observed": true, "passed": true},
    {"name": "no_silent_rewrite", "expected": 0, "observed": 0, "passed": true},
    {"name": "branching_completeness", "expected": "every recorded candidate resolves to exactly one branch", "observed": true, "passed": true}
  ],
  "outputs": ["output/record_admit_commit.mp4", "output/committed_final.png"],
  "status": "pass"
}
```
Note: this scene is the one most naturally rendered as an animation (`.mp4` or frame sequence) rather than a single PNG, since the property under test is inherently temporal.

---

## 3. Distinction Holonomy

**Goal.** An oriented test object transported around a closed path, compared against a preserved reference copy at the origin, producing a quantitative residual.

**Script structure**
- Place a reference copy of an oriented, asymmetric test object (e.g. an object with distinguishable "up," "front," and a non-uniform color/texture so residual is visually legible, though the check itself must not depend on that) fixed at the origin — never moved, used only for comparison.
- Define a closed path (a curve object) and a "connection" — a rule for how the transported object's orientation/scale/material updates as it moves along the path (this is where you inject either a trivial connection, which should return the object unchanged, or a genuinely nontrivial one, e.g. a rotation that doesn't compose to identity over the loop, analogous to parallel transport around a curved surface).
- Animate the test object's transport along the path back to its starting position (same location as the reference copy, for direct comparison).
- At the final frame, compute the residual: positional difference (should be ~0 if the path is truly closed in space), plus rotational, chromatic (if material properties are transported), and morphological (if mesh shape is deformed by the connection) differences against the reference copy.
- Render two variants: `trivial_loop` (connection = identity) and `nontrivial_loop` (connection ≠ identity), so the scene demonstrates both a pass and a declared-nonzero-drift case from the same generator.

**Admissibility check.** Quantitative, per your spec:
- `trivial_residual < tolerance` (e.g. tolerance = 1e-4 in normalized units) → passes.
- `nontrivial_residual > 0` and specifically **declared** (i.e. the sidecar states the expected nonzero value computed analytically or numerically from the connection definition, and the observed rendered/measured residual must match that declared value within tolerance) — this is important: a nonzero residual isn't automatically a "pass," it's a pass only if it matches what the connection *predicts*. An unexplained nonzero residual is itself a failure (it would mean the geometry doesn't implement the stated connection correctly).

**Sidecar schema** (this is the one you already drafted — extending it slightly to cover both variants):
```json
{
  "scene_id": "distinction-holonomy-loop",
  "generator": "scenes/distinction_holonomy.py",
  "framework": "distinction-holonomy",
  "primitive": "closed_transport",
  "parameters": {"path": "closed_curve_a", "connection": "rotation_5deg_per_unit_arc"},
  "render": {
    "blender_version": "4.2",
    "engine": "BLENDER_EEVEE_NEXT",
    "resolution": [1920, 1080],
    "samples": 64,
    "seed": 42,
    "camera": {},
    "lighting": {}
  },
  "checks": [
    {"name": "trivial_loop_residual", "expected": 0.0, "observed": 0.00003, "tolerance": 0.0001, "passed": true},
    {"name": "nontrivial_loop_residual", "expected": 0.0873, "observed": 0.0869, "tolerance": 0.001, "passed": true}
  ],
  "outputs": ["output/holonomy_trivial.png", "output/holonomy_nontrivial.png"],
  "status": "pass"
}
```

---

## 4. Sheaf Gluing

**Goal.** Both a successful and an obstructed gluing case from the same patch system, with global assembly gated by the same compatibility data used to build the geometry.

**Script structure**
- Define `k` local patches (mesh regions), each generated independently with an explicit overlap region against its neighbors (shared boundary vertices or a defined overlap zone with parametrized data — e.g. a scalar field sampled on the overlap).
- Compute pairwise compatibility on each overlap: do the two patches agree on the overlap data (within tolerance)? This produces a compatibility graph (patches as nodes, overlaps as edges, each edge labeled compatible/incompatible).
- **Successful case**: construct all patches so every overlap is compatible by construction (shared generator function for overlap regions), then perform the actual gluing (boolean union / vertex merge at shared boundaries) and render the resulting single coherent object.
- **Obstructed case**: deliberately perturb one patch's overlap data (e.g. offset one patch's boundary values by a fixed amount) so at least one edge in the compatibility graph is incompatible, then attempt the same gluing operation — the script should render the resulting *visible seam/gap/discontinuity* rather than forcing a merge, i.e. the geometry itself should fail to close, not just report failure in text.
- Both cases must derive their rendered outcome and their sidecar `passed` value from the *same* compatibility computation — the script should have exactly one function, `check_compatibility(patch_a, patch_b)`, called both when deciding whether to actually perform the boolean merge and when writing the check result. This is the mechanism that prevents "depicts success while sidecar reports failure."

**Admissibility check.**
- `all_overlaps_compatible` (successful case): every edge in the compatibility graph is compatible, and the resulting mesh has zero non-manifold edges at former patch boundaries (a direct geometric proxy for "actually glued," not just visually adjacent).
- `has_incompatible_overlap` (obstructed case): at least one edge is incompatible, and correspondingly the resulting mesh *does* have a non-manifold edge / gap at that boundary — i.e. the geometric defect's location matches the compatibility graph's flagged edge location.

**Sidecar schema**
```json
{
  "scene_id": "sheaf-gluing",
  "generator": "scenes/sheaf_gluing.py",
  "framework": "structural-semantics",
  "primitive": "local-to-global-consistency",
  "parameters": {"n_patches": 4, "overlap_width": 0.1, "perturbation": {"case": "obstructed", "patch": 2, "offset": 0.3}},
  "checks": [
    {
      "case": "successful",
      "name": "all_overlaps_compatible_and_manifold",
      "expected": true,
      "observed": true,
      "passed": true
    },
    {
      "case": "obstructed",
      "name": "incompatible_overlap_produces_matching_defect",
      "expected_defect_location": "patch_1_patch_2_boundary",
      "observed_defect_location": "patch_1_patch_2_boundary",
      "passed": true
    }
  ],
  "outputs": ["output/gluing_successful.png", "output/gluing_obstructed.png"],
  "status": "pass"
}
```

---

## 5. Render Ledger (self-inspection)

**Goal.** The suite renders its own provenance graph, derived from real manifest entries; missing artifacts appear as visible breaks.

**Script structure**
- Rather than authoring geometry from imagined data, this scene's `build()` function scans `output/*.json` (the sidecar files from scenes 1–4, plus itself once run once) and constructs a directed graph: nodes are {generator script, parameter set, sidecar JSON, rendered output, verification status}, edges are the provenance relations (generator → parameters, parameters → output, output → sidecar, sidecar → status).
- Each node is rendered as a distinct geometric object (e.g. cubes for generators, spheres for parameter sets, cones for outputs, torus for sidecars), positioned by a graph layout (can be a simple force-directed layout computed once in Python before Blender object creation, or a deterministic layered layout by node type — deterministic layout is preferable here since reproducibility is part of what's being tested).
- Edges are rendered as curves/cylinders connecting nodes. **Critically**: an edge is only drawn if the target actually resolves — e.g. if a sidecar references an output PNG that doesn't exist on disk, that edge is *not* drawn, leaving a visible gap in the graph, rather than drawing a dangling edge or a placeholder node.
- Missing/broken relations (a generator with no sidecar, a sidecar with no verification result, a referenced output file absent) should render as an explicit "break" marker — e.g. a small red flag object at the point where the edge would have continued — so the failure is visually locatable, not just absent.

**Admissibility check.** Reflexive: the scene passes only when every visualized provenance relation resolves to a real artifact.
- `all_referenced_files_exist`: for every sidecar scanned, every path in its `outputs` array exists on disk.
- `all_sidecars_have_status`: every sidecar has a `status` field with value `pass` or `fail` (not missing/null).
- `no_orphan_generators`: every `.py` file in `scenes/` has at least one corresponding sidecar referencing it as `generator`.
- `graph_break_count`: count of visible break markers in the rendered graph; the scene's own status is `pass` only if this count is 0 — i.e. **the render ledger scene is the one scene whose "pass" condition is that the rest of the suite has no gaps**, making it a genuine integration check rather than an independent unit test.

**Sidecar schema**
```json
{
  "scene_id": "render-ledger",
  "generator": "scenes/render_ledger.py",
  "framework": "non-collapse",
  "primitive": "reflexive-provenance",
  "parameters": {"scanned_dir": "output/", "scanned_scenes": ["pop-refuse-bind-collapse", "record-admit-commit", "distinction-holonomy-loop", "sheaf-gluing"]},
  "checks": [
    {"name": "all_referenced_files_exist", "expected": true, "observed": true, "passed": true},
    {"name": "all_sidecars_have_status", "expected": true, "observed": true, "passed": true},
    {"name": "no_orphan_generators", "expected": true, "observed": true, "passed": true},
    {"name": "graph_break_count", "expected": 0, "observed": 0, "passed": true}
  ],
  "outputs": ["output/render_ledger_graph.png"],
  "status": "pass"
}
```

---

## Sequencing and shared harness notes

- These five scenes should share a `common_admissibility.py` module (distinct from Centerfuge's existing `common.py`, or an extension of it) providing: sidecar-writing helpers, the `checks` accumulation pattern, deterministic seeding, and the fail-loud status convention.
- Scene 5 has a hard dependency on scenes 1–4 having already run at least once (it scans their output). The suite's `render_all.sh` should therefore run scenes 1–4 first, then scene 5 last, and scene 5's own failure should be treated as suite-level signal, not scene-level noise — a failing render-ledger scene means the suite as a whole is inadmissible even if scenes 1–4 individually reported `pass`.
- Naming this tranche "Admissibility Experiments" as you suggested gives a clean top-level directory (`admissibility-experiments/`) sitting alongside (not inside) `industrial-ecologies/`, with the latter's own scenes eventually able to declare a dependency on specific Admissibility Experiments checks passing before they're considered meaningful — e.g. an Industrial Ecologies conservation check could formally cite the sheaf-gluing scene's compatibility check as the general mechanism it's a specific instance of.
