# Centerfuge Safety and Maintenance Specification

**Specification status:** Foundation draft  
**Evidence status:** M — Modeled  
**Controlling issue:** [#9](https://github.com/standardgalactic/Centerfuge/issues/9)  
**Parent architecture:** [Boundary-Aware Operating Architecture](operating-model.md)

## 1. Purpose and authority

This document defines the safety contract for the complete envisioned domestic Centerfuge. It applies to the shared intake, quarantine chamber, rotating separation core, air and exhaust path, routing and storage, repair and fabrication modules, isolated food-and-clothing domain, hyperbolation equipment, controls, installation, cleaning, and service interfaces.

It is a requirements specification, not a declaration that an apparatus is safe. Requirements use **shall** for mandatory behavior, **should** for a recommended design choice that requires justification if omitted, and **may** for a permitted option. A subsystem may operate only inside an apparatus-specific envelope whose thresholds, provenance, verification, and unresolved limitations are recorded in a validated safety manifest.

The first concrete application is [Fast Solids Lab Experiment 001](../experiments/fast_solids_lab/protocols/experiment-001.md). That experiment may demonstrate protections for its exact apparatus and material batches. It cannot qualify the complete domestic system.

## 2. Non-claims and evidence boundary

This specification does not establish compliance with any jurisdiction's product-safety, electrical, machinery, pressure, fire, food-contact, accessibility, or occupational requirements. Applicable standards depend on the final mechanism, installation, jurisdiction, and intended use. Standards named in the evidence register are constraints and research anchors until their applicable clauses have been mapped and verified.

The system shall preserve separate physical and epistemic records:

\[
L_{\mathrm{phys}} \ne L_{\mathrm{epi}}.
\]

The physical ledger records observations and actions: sensor values, guard and interlock states, commands, trips, motion, pressure, temperature, containment, and destinations. The epistemic ledger records what those observations warrant: interpreted cause, confidence, authorized recovery, prohibited continuation, open uncertainty, and evidence status. A plausible interpretation shall not overwrite an adverse physical event. A successful physical stop shall not establish that its cause is understood.

## 3. Admission and refusal

Every hazardous process shall define a process-relative admission predicate:

\[
\operatorname{Admit}(x,p)
\iff K(x)\land C(x,p)\land H(x,p)\leq H_{\max}(p).
\]

Here, \(K(x)\) means the properties required by process \(p\) are known; \(C(x,p)\) means the known properties are compatible; and \(H(x,p)\) is the estimated hazard under that process. Classification confidence alone is not admission.

The controller shall refuse the affected operation when an applicable manifest value is missing, a required sensor is unavailable or stale, calibration has expired, an interlock is unverified, configuration identity is ambiguous, or the credible uncertainty in an input includes a hard-refusal class. Unknown is a stable result, not an invitation to guess.

Refusal shall stop further admission, preserve containment and identity where practical, record its cause, and expose a bounded recovery route. It shall not destructively process an object merely to make refusal easier.

## 4. Protective hierarchy

The design shall first remove or bound hazards through process and geometry, then use passive containment and guards, then interlocks and protective controls, then procedures and warnings. A warning, password, manual instruction, remote connection, or expectation of expert attention shall not be the sole protection against a credible high-consequence event.

No single sensor, software task, operator action, transparent observation panel, or network connection shall be the sole barrier against rotor or projectile release, hazardous motion, fire, hazardous atmosphere, pressure release, or cross-contamination into the food subsystem. Safety functions that use software shall state their failure assumptions and independent physical fallback.

## 5. Operating states

The minimum state vocabulary is:

| State | Required invariant |
| --- | --- |
| **OFF** | No commanded motion; stored energy may remain and access is not implied. |
| **QUARANTINE** | Input enclosed for observation; destructive processing unavailable. |
| **READY** | Preconditions have passed for one named process and configuration. |
| **RUN** | The admitted process operates inside its commissioned envelope. |
| **CONTROLLED_REFUSAL** | Feed is inhibited and the event-specific safe-stop sequence is active. |
| **COOLDOWN_CLEARING** | Residual motion, pressure, temperature, atmosphere, or material prevents access. |
| **USER_ACCESS** | Only designated low-energy compartments may be opened. |
| **SERVICE_LOCKOUT** | Hazardous energy has been isolated and independently verified for protected access. |
| **FAULT_LATCHED** | Restart is prohibited until recorded recovery and reset conditions are met. |

Every transition shall define its initiating event, guards, actions, completion evidence, timeout, fallback, reset authority, and ledger entry. Power loss, controller restart, sensor loss, disagreement among redundant observations, and communications loss shall have explicit transitions. The system shall not return automatically to RUN after restoration of power or control.

## 6. Safe stopping

A safe state is the lowest-risk reachable state for the observed condition, not necessarily total power loss:

\[
s_{\mathrm{safe}}=
\arg\min_{s\in S_{\mathrm{reachable}}}
\operatorname{Risk}(s\mid\widehat{x},L_{\mathrm{phys}}).
\]

Each trip shall select an evidence-backed combination of feed isolation, drive-torque removal, braking or coast-down, duct and gate isolation, extraction, cooling, suppression, alarm, and fault latching. Normal stop, protective stop, and emergency stop shall remain distinct.

No recovery instruction may require access to a chamber, feeder, duct, collector interface, or rotor path until all applicable residual hazards have reached verified access limits. Loss of the sensor used to demonstrate a safe-access condition shall retain the lock unless a separate verified method establishes that condition.

## 7. Containment and high-energy parts

The rotating assembly shall be characterized by rated speed, maximum permitted speed, maximum credible speed, inertia, stored energy, tip speed, allowable imbalance, fatigue and wear assumptions, retention features, and coast-down behavior. Guards and containment shall be justified against the credible fragments and feedstock projectiles for that envelope. Transparent material shall not be presumed impact containment because it permits observation.

Overspeed protection shall be independent to the degree required by the consequence of primary-control failure. Imbalance monitoring shall use a commissioned baseline and shall account for the \(\omega^2\) growth of imbalance force. A protective trip caused by overspeed, impact, severe imbalance, loosened mass, bearing distress, or containment loss shall require event-specific inspection and recommissioning rather than an ordinary reset.

Feed, product, exhaust, and service openings shall be enumerated. Matter outside a designated opening or capture boundary is containment failure. Collector removal shall be inhibited whenever its absence or incomplete seating could open a path to motion, pressure, dust, fragments, or an incorrect destination.

## 8. Air, dust, pressure, heat, and ignition

Every dry-solids process shall assess whether its admitted materials or wear products can form hazardous dust or aerosols. The assessment shall cover fines production, concentration, electrostatic charging, credible ignition sources, grounding and bonding, filter loading, exhaust destination, housekeeping, and the consequences of continuing or stopping airflow.

Airflow and pressure boundaries shall record normal ranges, trip limits, sensor response, filter differential-pressure limit, relief behavior, and safe vent destination. A blocked filter, duct, or outlet shall produce controlled refusal before structural or containment limits are reached.

Thermal limits shall distinguish bearings, motor, drive electronics, air stream, process material, filters, seals, accessible surfaces, and any isolated food-contact region. A thermal stop shall state whether extraction or cooling must continue after motion and feed cease.

## 9. Material refusal and subsystem isolation

The general processing path shall not destructively accept batteries; lamps; pesticides; solvents; paints; fuels; aerosols; pressurized vessels; ammunition; radioactive or medical waste; unknown electronics; reactive chemicals; unknown powders; active biological contamination; or unknown matter whose credible possibilities include these classes.

Sharp objects, glass, ceramics, textiles, wet residues, food, magnets, conductive fibers, expandable beads, dust-forming solids, and high-mass objects require a named process and apparatus-specific admission. There is no global category of “Centerfuge-safe material.”

The food subsystem shall have separate surfaces, tools, storage, air handling, drainage, cleaning validation, and consumables. Waste-derived material shall not acquire food-contact authorization through washing, optical identification, sorting, or prior food use. The physical architecture shall prevent an unauthorized gate command or single routing fault from connecting general recovery exhaust, drainage, residue, or product paths to the food domain.

## 10. Cleaning and maintenance

Every wetted, dusted, or material-contact surface shall have a documented inspection and cleaning route. The design shall identify dead zones, trapped inventory, carryover paths, abrasion products, filter-change exposure, wet-cleaning incompatibilities, and a method for establishing acceptable cleanliness. Material recovered during cleaning belongs to the originating batch's mass balance.

Maintenance shall be scheduled by the mechanism that best represents degradation: pre-run, per-batch, operating hours, cycles, measured condition, calendar limit, or event trigger. Initial intervals shall be conservative and explicitly provisional. Evidence from vibration, temperature, differential pressure, leakage, fastener retention, abrasion, corrosion, electrical tests, contamination, and cycle history may revise them without erasing the earlier basis.

Maintenance history shall be part of apparatus configuration control. A run record shall identify the exact apparatus revision and current safety-manifest version.

## 11. Service boundary

Every component shall have one service class:

| Class | Boundary |
| --- | --- |
| **USER** | External cleaning, sealed-bin exchange, or approved consumable replacement without exposure to hazardous energy. |
| **TRAINED** | Guarded access after documented isolation, residual-energy verification, and prescribed return-to-service tests. |
| **PROTECTED_REPLACE_ONLY** | High-energy rotor and drive parts, containment-critical parts, safety controls, or equipment whose incorrect repair can defeat a primary protection. |

Service instructions shall define access conditions, authority, tools, protective assumptions, inspection, replacement or retirement criteria, reassembly checks, and the exact test required before READY. Safety-critical filters, bins, seals, ducts, guards, sensors, and fasteners should be keyed, captive, monitored, or otherwise designed so omission, reversal, incomplete seating, and silent bypass do not create an admitted state.

## 12. Domestic accessibility and foreseeable misuse

The design shall document loading and reach assumptions, required force and dexterity, maximum removable-bin mass, spill-resistant transfers, status presentation, and recovery actions usable under stress. Safety-critical status shall be available through more than one appropriate sensory channel where loss of one channel could produce unsafe access.

Normal use shall not require a person to infer whether motion has stopped, pressure has dissipated, a surface is safe to touch, an atmosphere is safe, or a fault permits access. Credible interaction by children, pets, visitors, and people with limited vision, hearing, mobility, strength, literacy, or technical knowledge shall be included in the hazard register.

## 13. Records and verification

The canonical machine-readable sources are:

- [hazard register](../safety/hazards.json), validated against [its schema](../safety/schemas/hazard-register.schema.json);
- apparatus manifests, validated against the [apparatus-manifest schema](../safety/schemas/apparatus-manifest.schema.json).

Every safety requirement and hazard control shall terminate in an inspection, analysis, test, demonstration, applicable authoritative constraint, or explicit open question that blocks the affected capability. Acceptance criteria shall be fixed before a test. Results shall identify apparatus configuration, instruments, calibration, deviations, and evidential scope.

The validator checks structural completeness, unique identifiers, recognized states and evidence classes, traceable controls, manifest provenance, and readiness blockers. It does not certify engineering adequacy or legal compliance. Use:


    python3 scripts/validate-safety.py


To require a manifest to be admitted for operation rather than merely valid as a draft, use:


    python3 scripts/validate-safety.py --require-runnable safety/manifests/experiment-001.json


The checked-in Experiment 001 manifest is intentionally blocked until apparatus-specific values and verification evidence exist. A successful structural validation must not convert those unknowns into permission to run.

For Experiment 001, structural completeness includes the complete, versioned
datum-ID inventory enforced by the validator. Removing a required datum is a
validation failure rather than a way to make an unknown disappear. A datum
with a physical unit requires a recorded tolerance before it can contribute to
RUN readiness. Every required safety sensor shall identify its instrument and
installed location, range, accuracy, sampling rate, calibration interval and
record, plausibility test, and current-availability test. Expired calibration
is a refusal condition. Every required interlock shall identify an independent
fallback so that a software interpretation is not the sole protection against
a high-consequence event.

RUN authorization remains a separate admission act after the evidence record
is complete. It shall identify the authority, timestamp, exact authorized
scope, and evidence record. Setting `approved_for_run` without that record, or
while any datum, sensor, interlock, calibration, fallback, or explicit blocker
remains unresolved, shall fail the runnable validation gate.

## 14. Reference constraints

The following sources establish constraints used by the architecture; their presence does not itself establish conformity:

- OSHA, [Machine Guarding](https://www.osha.gov/machine-guarding), for guarding of moving machine parts.
- OSHA, [Control of Hazardous Energy (Lockout/Tagout)](https://www.osha.gov/control-hazardous-energy), for hazardous-energy isolation concepts.
- OSHA, [Combustible Dust](https://www.osha.gov/combustible-dust), for dust recognition, ignition control, containment, and housekeeping.
- EPA, [Household Hazardous Waste](https://www.epa.gov/hw/household-hazardous-waste-hhw), for refusal and intact diversion of hazardous household materials.
- EPA, [Lithium-Ion Battery Recycling](https://www.epa.gov/hw/lithium-ion-battery-recycling-frequently-asked-questions), for exclusion of batteries from mechanical household processing.
- FDA, [Recycled Plastics in Food Packaging](https://www.fda.gov/food/packaging-food-contact-substances-fcs/recycled-plastics-food-packaging), for the process-specific nature of food-contact suitability.

Final product development shall add the applicable jurisdictional and consensus standards and map individual clauses to stable requirement and evidence identifiers.
