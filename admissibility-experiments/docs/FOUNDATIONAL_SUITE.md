# Full Experiment Specifications

These specifications define what each render diagnoses. They are normative: a visually attractive image does not compensate for a check that is disconnected from construction data.

## 1. Pop / Refuse / Bind / Collapse

**Claim under test.** The four Spherepop primitives denote distinguishable operations rather than four names for selection. The population consists of sixteen candidate icospheres with deterministic scalar values. Pop extracts the unique extremal candidate along a reserved axis. Refuse relocates every predicate failure to a persistent discard region without deleting it. Bind creates exactly one explicit edge between two admitted candidates. Collapse replaces the remaining unresolved candidates with one aggregate and unlinks the sources.

**Measurements.** The Pop check compares initial and final transforms and verifies extraction on the reserved Z axis. The Refuse count is computed from the same scalar predicate used during construction. Bind edges are discovered through their `bind_ids` properties. Collapse verifies that every source object is unreachable from `bpy.data.objects`; hiding does not qualify.

**Diagnostic failure.** A failure identifies semantic aliasing: an extraction that behaves like arbitrary displacement, a refusal that silently erases, a bind without a relation, or a collapse that preserves hidden originals.

## 2. Record / Admit / Commit

**Claim under test.** Recording remains revisable, admission exhaustively branches, and commitment is temporally monotone. Six deterministic batches enter a threshold policy. Accepted candidates become committed blocks; refused candidates remain visible in a separate region. A snapshot records committed identifiers and transforms after every batch.

**Measurements.** Every committed identifier set must be a subset of its successor. Previously committed transforms must be byte-for-byte stable at the chosen rounding precision. Every recorded identifier must resolve to exactly one branch.

**Diagnostic failure.** A missing candidate exposes loss between stages. A candidate in both branches exposes incoherent admission. A changed committed transform exposes revision disguised as accumulation.

## 3. Distinction Holonomy

**Claim under test.** Closed spatial return need not imply identity return, but any residual must be predicted by the declared connection. A preserved asymmetric reference frame is compared with trivial and nontrivial transported returns on the same closed path.

**Measurements.** The trivial angular residual must fall below tolerance. The nontrivial residual must equal the declared 35-degree connection residual within tolerance. An unexplained drift fails even though it looks like holonomy.

**Diagnostic failure.** A nonzero trivial residual indicates numerical or construction leakage. A mismatched nontrivial residual means the render does not implement the connection it claims to depict.

## 4. Sheaf Gluing

**Claim under test.** Local pieces form a global object only when overlap data agree. Two four-patch rows share the same construction. The successful row uses identical boundary heights. The obstructed row perturbs one patch. The compatibility computation both governs defect-marker construction and supplies the sidecar observation.

**Measurements.** Every successful overlap must be within tolerance. The obstructed case must contain at least one incompatible edge. The number of visible defect markers must equal the number of incompatible edges.

**Diagnostic failure.** A marker without an incompatible edge is decorative failure theater. An incompatible edge without a marker hides the obstruction. A forced seamless merge falsifies the local data.

## 5. Vertical and Horizontal Repair

**Claim under test.** Vertical repair restores an object against its own retained constraint, whereas horizontal repair reconciles divergent structures through an interface. The diptych gives each mechanism distinct topology rather than merely different colors.

**Measurements.** The vertical result must meet the stored target within tolerance. The horizontal consensus must lie between the two inputs. The scene graph must contain both a restored object and an explicit reconciliation relation.

**Diagnostic failure.** If both halves reduce to replacement by a third value, the prose distinction has not survived geometric implementation.

## 6. RSVP Field

**Claim under test.** A proposed scalar/vector/entropy mapping can be rendered without conflating its components. A deterministic lattice samples `phi = exp(-r²/8)` and `S = 1 - phi`; height and radius encode scalar concentration while the sample metadata retains both quantities.

**Measurements.** Scalar and entropy values must sum to one within numerical tolerance. Maximum scalar concentration must occur nearer the center than the minimum sample.

**Diagnostic failure.** Failure indicates an internally inconsistent visualization, not a disproof of RSVP. Passing likewise establishes only that the mapping implements its declared equations.

## 7. Persistence Cone / Tidal Torque

**Claim under test.** Accumulated angular memory can be distinguished from a static spinning body. Nine rings increase in radius and angular-memory property with time index, forming a widening persistence cone.

**Measurements.** Radius and stored angular memory must both increase strictly with index.

**Diagnostic failure.** A nonmonotone ring sequence exposes a visualization that suggests accumulation while encoding oscillation or erasure.

## 8. TARTAN Weave as Computation

**Claim under test.** Crossings are computed junctions, not a fabric texture. Seven warp and seven weft lines create forty-nine explicit nodes. Junction height is determined by parity, making over/under structure an evaluated rule.

**Measurements.** Exactly forty-nine junction objects must exist and each must carry a valid computed parity.

**Diagnostic failure.** Missing crossings indicate that the weave metaphor outruns its structural realization. Decorative lines without junction state do not count as computation.

## 9. Render Ledger

**Claim under test.** Provenance can inspect itself. The scene scans real sidecars and generator paths, creates nodes only for resolved artifacts, and places break markers for missing relations.

**Measurements.** Fifteen predecessor sidecars must exist. Every referenced output must exist unless running in declared dry-run mode. Every sidecar must have a valid status. Every experiment entry point must be referenced by a sidecar. Break count must be zero.

**Diagnostic failure.** Ledger failure is suite-level inadmissibility. It does not erase otherwise useful renders; it shows that the archive cannot yet support its reproducibility claim.

## 10. Data Center / Compute Substrate

**Claim under test.** Compute can be represented as material infrastructure rather than disembodied capacity. Eight racks expose server units, declared IT load, facility overhead, heat rejection, and water-use accounting.

**Measurements.** Rack power must sum from object properties. Facility power is derived from IT load and PUE. In the simplified steady-state boundary, facility power and heat rejection must balance. Water is derived from the declared intensity.

**Diagnostic failure.** A mismatch exposes inconsistent bookkeeping. A pass validates the accounting graph only; it does not certify empirical PUE or water-intensity values.

## 11. Fusion Reactor Comparison

**Claim under test.** Two confinement topologies can be compared without presenting a speculative proxy as plasma physics. A toroidal vessel and a twenty-four-cell Caldera ring are rendered side by side.

**Measurements.** The declared cell count must match geometry. The sidecar must retain `schematic: true` and explicitly label its loss indices as proxies rather than Lawson calculations.

**Diagnostic failure.** A missing disclaimer is an epistemic failure even if the geometry is correct, because it would admit an illustration as physical evidence.

## 12. Molecular Manufacturing Assembler

**Claim under test.** Staged component admission can remain materially accountable at a schematic molecular scale. Twelve components are evaluated by one deterministic rule; accepted components receive visible bonds and refused ones persist in a discard region.

**Measurements.** Accepted plus refused counts must equal the input count. Every refusal must have visible retained geometry.

**Diagnostic failure.** Lost components violate conservation of candidates. Silent deletion collapses refusal into disappearance. No physical-accuracy claim is made.

## 13. Aniara Whale-Hull Cutaway

**Claim under test.** A cutaway can reveal internal topology without solving occlusion by deleting the interior. Thirteen transverse ribs define the organism-ship hull while seven modules remain in the open viewing wedge.

**Measurements.** All declared modules must be present. The camera-target contract verifies that no closed exterior shell has been introduced between the camera and the interior targets.

**Diagnostic failure.** Missing modules mean the cutaway has simplified away the structure it was meant to inspect. A later ray-cast implementation may strengthen the current sightline proxy.

## 14. City of Brutes Triad

**Claim under test.** Administrative, Animal, and Performative orders remain distinct while every pair shares an interface. Three spatial rings and three explicit connectors encode the triad.

**Measurements.** The scene must contain exactly three named zones and three pairwise interfaces.

**Diagnostic failure.** A missing interface reduces the structure to hierarchy or opposition. A merged zone erases the screenplay's three-part claim.

## 15. Sproll Primitive Manipulatives

**Claim under test.** Spherepop primitives can become graspable, child-legible forms without depending on labels or color. Pop is a single ball, Refuse an open gate, Bind a bridge-like clip, and Collapse a nested telescoping tube.

**Measurements.** All four semantic objects must have unique shape signatures. The identity check uses topology labels rather than material values.

**Diagnostic failure.** If two objects require color or prose to be distinguished, the manipulative vocabulary is not yet pedagogically adequate.

## 16. Fluid Flashcards State Visualization

**Claim under test.** Cards own state while collections remain views over identifiers. Twelve card objects each carry one serialized state record. Due, topic, and difficulty views contain card IDs and may overlap without copying state.

**Measurements.** There must be one state record per card and zero view-owned state copies. Membership lists are retained as evidence.

**Diagnostic failure.** Duplicated state indicates that changing collections could fork a card's identity. Overlapping memberships are permitted and expected.

## Shared execution semantics

Every scene process distinguishes an engine crash from an inadmissible result. A completed scene writes its sidecar and exits normally even when a computed check fails. The suite verifier interprets sidecars and fails loudly. This preserves failed renders as evidence while still supporting continuous integration. Seeds, Blender version, camera, engine, resolution, samples, parameters, checks, evidence, outputs, and final status are serialized. The ledger runs last because its input is the material history produced by the other experiments.

