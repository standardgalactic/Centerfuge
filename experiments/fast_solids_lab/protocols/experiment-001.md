# Centerfuge Fast Solids Lab: Experiment 001

## Air-Assisted Classification of Polystyrene, Salt, and Steel

**Protocol status:** Proposed  
**Evidence status:** M — Modeled  
**Related issues:** [#8](https://github.com/standardgalactic/Centerfuge/issues/8), [#9](https://github.com/standardgalactic/Centerfuge/issues/9)  
**Parent architecture:** [Boundary-Aware Operating Architecture](../../../docs/operating-model.md)

## 1. Experimental question

Can a contained air-assisted rotating vortex separate a dry, known mixture of polystyrene pellets, coarse salt, and steel BBs into reproducible collection fractions more effectively than gravity, screening, or airflow alone?

The bounded claim under test is:

> Under a recorded combination of chamber geometry, airflow, angular velocity, feed rate, and residence time, the Centerfuge classifier produces outlet fractions whose purity and recovery exceed specified baselines.

The experiment does not test household waste processing, material identification, fabrication, food safety, or autonomous admission. All three materials are known before entry, and their identities remain known during evaluation.

## 2. Classification hypothesis

The materials differ in density, size, shape, aerodynamic response, restitution, and surface behavior. Separation cannot therefore be attributed to density alone.

Steel BBs should generally exhibit the greatest radial inertia and the lowest acceleration by airflow relative to their mass. Polystyrene pellets should respond most strongly to the air field. Coarse salt should occupy an intermediate but broad response regime because its grains are irregular and vary in size.

The provisional ordering is

\[
\Psi_{\mathrm{PS}} < \Psi_{\mathrm{salt}} < \Psi_{\mathrm{steel}},
\]

where \(\Psi_i\) is an effective inertial-to-drag response parameter. This ordering is a hypothesis rather than a classification rule assumed in advance.

For approximately spherical particles, a useful response quantity is

\[
\Psi_i =
\frac{m_i\omega^2r}
{\frac12 C_{D,i}\rho_a A_i v_{\mathrm{rel},i}^{2}},
\]

where \(m_i\) is particle mass, \(A_i\) is projected area, \(C_{D,i}\) is drag coefficient, \(\rho_a\) is air density, and \(v_{\mathrm{rel},i}\) is relative air speed.

A large \(\Psi_i\) predicts stronger radial migration relative to aerodynamic entrainment. It does not predict the final outlet by itself because wall collisions, salt fragmentation, pellet charging, turbulence, and outlet geometry also affect trajectories.

## 3. Material specification

Materials are characterized as batches rather than treated as ideal substances.

| Property | Polystyrene pellets | Coarse salt | Steel BBs |
| --- | --- | --- | --- |
| Batch identifier | Recorded | Recorded | Recorded |
| Total input mass | Measured | Measured | Measured |
| Individual mass distribution | Sampled | Sampled | Sampled |
| Equivalent diameter | Measured | Sieved and measured | Measured |
| Bulk density | Measured | Measured | Measured |
| Particle density | Supplier value plus verification where practical | Reference value plus uncertainty | Supplier value |
| Shape | Pellet geometry | Irregular crystal | Approximately spherical |
| Moisture | Conditioned and recorded | Conditioned and recorded | Surface dryness recorded |
| Surface condition | Clean and untreated | Clean and dry | Clean and corrosion-free |
| Breakage susceptibility | Low to moderate | Moderate | Low |
| Special confounder | Electrostatic charging | Fragmentation and humidity | Impact energy and magnetism |

The polystyrene feedstock must be identified as expanded foam, expandable beads, or solid resin granules because these have substantially different effective densities and aerodynamic responses.

Coarse salt is sieved into a stated interval. The unsieved remainder is retained but excluded from the principal trial. Steel BB diameter is chosen so that BBs cannot pass through gaps, perforations, or seals not intended as outlets.

### 3.1 Size strategy

The commissioning mixture may use available materials as received. Its purpose is to verify containment, collection, recognition, and mass accounting.

The principal mixture should use overlapping equivalent-diameter ranges as closely as practical. If all three materials occupy visibly distinct size ranges, apparent success may merely reproduce screening.

A later negative control should deliberately make two materials dynamically similar. That is not required for the first commissioning run, but is required before claiming a generalizable separation regime.

## 4. Apparatus boundary

The experimental system begins at the weighed feed container and ends at the sealed collection vessels, exhaust collector, and post-run chamber inventory.

The minimum apparatus comprises a closable feed interface, a contained vortex chamber, independently measured airflow, independently measured rotor or swirl-generator speed, at least three collection bands or outlets, filtered exhaust, emergency stop, vibration measurement, temperature measurement, electrical power measurement, and transparent or instrumented observation where containment permits.

Every opening belongs to one of four classes:

\[
O =
\{O_{\mathrm{feed}}, O_{\mathrm{product}}, O_{\mathrm{exhaust}},
O_{\mathrm{service}}\}.
\]

A particle appearing anywhere else constitutes containment failure.

Radial collection bands are called **inner**, **middle**, and **outer** rather than polystyrene, salt, and steel. Naming outlets after expected materials would allow the intended interpretation to replace the measured result.

## 5. Experimental factors

The first campaign uses staged parameter sweeps rather than a full factorial combination of every possible variable.

| Factor | Symbol | Initial treatment |
| --- | --- | --- |
| Rotor or imposed swirl speed | \(\omega\) | Three levels: low, medium, high |
| Airflow | \(Q_a\) | Three levels: low, medium, high |
| Feed rate | \(\dot m_f\) | Held constant during the first sweep |
| Residence time | \(t_r\) | Fixed by one collection schedule |
| Material ratio | \(\phi_i\) | Equal mass initially |
| Particle-size range | \(d_i\) | Fixed principal batch |
| Chamber geometry | \(G\) | Fixed |
| Outlet geometry | \(O\) | Fixed |
| Relative humidity | \(RH\) | Measured, not deliberately swept initially |
| Electrostatic condition | \(E_s\) | Observed and controlled where practical |

Low, medium, and high must be replaced with measured values. Until apparatus limits are established, levels are defined relative to a safely commissioned maximum:

\[
\omega^* = \frac{\omega}{\omega_{\mathrm{safe}}},
\qquad
Q_a^* = \frac{Q_a}{Q_{a,\mathrm{safe}}}.
\]

The initial screen contains all nine airflow-speed pairs:

| Run family | Rotor speed | Airflow |
| --- | --- | --- |
| A1–A3 | Low | Low, medium, high |
| B1–B3 | Medium | Low, medium, high |
| C1–C3 | High | Low, medium, high |

Each condition is repeated at least three times using newly recombined material. Run order is randomized after commissioning so progressive salt fragmentation, chamber wear, warming, or static buildup is not confused with parameter effects. This produces twenty-seven principal mixed-material runs. Blanks, single-material tests, and baselines are additional.

## 6. Controls

An **empty run** establishes background vibration, power, airflow stability, and material already present in the apparatus.

Three **single-material runs** establish where each material travels without interparticle collisions or contamination by the other two.

An **airflow-only run** sets \(\omega=0\) while preserving the feed and airflow procedure. It measures classification caused by the air path without mechanical rotation.

A **rotation-only run** sets \(Q_a=0\), or the minimum ventilation required for safe operation, while preserving rotation. A larger rotation-only campaign belongs to Experiment 002, but one conservative baseline condition belongs here.

A **gravity control** passes the mixture through the same collection interval with neither active swirl nor classification airflow.

A **screen baseline** separates the same input with available sieves. It measures how much apparent Centerfuge success can be reproduced geometrically.

A **magnetic baseline** extracts steel with a magnet. It may outperform the vortex for steel recovery, and that is useful. Centerfuge is compared with the simplest mechanism appropriate to each material, not only with deliberately weak alternatives.

## 7. Run procedure

Before each run, the chamber and collectors are inspected, cleaned, dried, and assigned a cleanliness status. The rotor, collection bands, filters, seals, and instrumentation are checked. Empty collection vessels are weighed.

Each material batch is separately weighed. Representative particles are measured before mixing. The mixture is prepared by a fixed tumbling procedure that avoids crushing salt or unnecessarily charging polystyrene.

The apparatus is brought to target airflow and rotational state before feeding unless a start-from-rest trial is explicitly designated. Feed begins at the recorded time and proceeds at a controlled rate. The system runs through the defined classification and clearing interval. Power, speed, airflow, vibration, temperature, pressure, and anomalies are recorded continuously or at a fixed sampling interval.

After controlled shutdown, every collector is sealed before removal. Material remaining on walls, in ducts, in filters, and in the feed system is recovered and recorded separately. Residue is not silently added to the nearest expected fraction.

The apparatus is cleaned according to a recorded procedure. Cleaning recovery belongs to the mass balance of the run in which the material was deposited.

## 8. Post-collection assay

The materials permit a strong mass-based assay without advanced spectroscopy.

Steel is isolated magnetically and confirmed visually. Polystyrene is hand-separated or isolated through a validated density method that does not dissolve or alter salt. Salt is identified from the remaining crystalline fraction, with dissolution used only if the analytical method accounts for recovered solute and water.

The assay procedure must itself be validated with known blind mixtures. Otherwise, apparent classifier error may be measurement error.

For each input material \(i\) and collector \(j\), record

\[
m_{ij} =
\text{mass of material }i\text{ recovered from collector }j.
\]

Also record chamber residue \(m_{iR}\), exhaust-filter capture \(m_{iE}\), and unrecovered mass.

## 9. Primary metrics

Purity of collector \(j\) for material \(i\) is

\[
P_{ij} =
\frac{m_{ij}}{\sum_k m_{kj}}.
\]

Recovery of material \(i\) into its assigned collector \(j^*\) is

\[
R_i =
\frac{m_{ij^*}}{m_{i,\mathrm{in}}}.
\]

Choosing \(j^*\) after every run would inflate performance. Outlet assignments are learned from commissioning or training runs and frozen before confirmatory trials.

Macro-averaged recovery is

\[
R_{\mathrm{macro}} =
\frac13 \sum_i R_i,
\]

but individual material results remain visible. A high average must not conceal complete failure for one material.

Mass closure is

\[
C_m =
\frac{
\sum_{i,j}m_{ij}+\sum_i m_{iR}+\sum_i m_{iE}
}{
\sum_i m_{i,\mathrm{in}}
}.
\]

Specific energy is

\[
e_s =
\frac{\int_{t_0}^{t_1}P(t)\,dt}
{\sum_i m_{i,\mathrm{in}}}.
\]

Experimental throughput is

\[
\dot m =
\frac{\sum_i m_{i,\mathrm{in}}}
{t_{\mathrm{feed}}+t_{\mathrm{classification}}+t_{\mathrm{clear}}}.
\]

Operational throughput includes cleaning and recovery time:

\[
\dot m_{\mathrm{operational}} =
\frac{m_{\mathrm{in}}}
{t_{\mathrm{setup}}+t_{\mathrm{run}}+
t_{\mathrm{recovery}}+t_{\mathrm{clean}}}.
\]

Breakage is measured through pre- and post-run size distributions. Contamination includes material in the wrong collector, previous-run carryover, and apparatus-derived matter in any fraction.

## 10. Success and falsification

Visible banding is not a success criterion. A candidate condition is experimentally promising only if confirmatory trials meet every provisional gate below.

| Criterion | Provisional threshold |
| --- | --- |
| Mass closure | \(0.98 \leq C_m \leq 1.02\) |
| Purity for every assigned fraction | At least 90% |
| Recovery for every material | At least 80% |
| Repeatability | No recovery standard deviation above 10 percentage points |
| Active improvement | Meaningful gain over gravity and airflow-only controls |
| Containment | No escape outside designated collectors and exhaust capture |
| Safety stops | None triggered during valid confirmatory runs |
| Reporting | Complete physical and epistemic records |

These are proposed experimental gates, not claims that the present apparatus can meet them.

The tested configuration is ineffective if no safe condition improves meaningfully upon controls; if apparent purity depends primarily on non-overlapping sizes; if one material accumulates unrecoverably in the chamber; if the result cannot be reproduced; or if energy and cleaning costs overwhelm the separation benefit.

Failure falsifies the bounded configuration, not every possible Centerfuge.

## 11. Safety and refusal boundary

Steel BBs introduce impact and imbalance hazards. The chamber must retain a BB at the maximum credible tip speed and must not depend on transparent material unless that barrier has an appropriate impact margin.

Polystyrene may charge electrostatically and produce fine fragments. Salt dust can irritate, abrade, contaminate bearings, and change electrical or surface conditions. The experiment introduces no ignition source into a potentially dusty air stream.

A run enters controlled refusal when vibration exceeds the commissioned limit, rotational speed leaves its allowed range, temperature rises beyond a material or bearing limit, airflow or pressure indicates blockage, containment is breached, a collector fails, feed jams, or instrumentation required for safe interpretation becomes unavailable.

Numerical stop thresholds cannot be assigned until the chamber, rotor, bearings, drive, sensors, and structural ratings are known. They belong in an apparatus-specific safety manifest. A missing threshold prevents the corresponding run from being admitted.

A safe stop may require controlled braking, continued extraction, or continued cooling. It is not necessarily an immediate loss of all power.

## 12. Machine-readable record

Every run produces a JSON record containing the protocol and apparatus versions, material batches and properties, target and observed parameters, timestamps, collector masses, assay results, mass closure, energy, vibration, temperature, anomalies, stop events, cleaning recovery, and evidence status.

The physical result remains distinct from its epistemic interpretation:

\`\`\`json
{
  "protocol": "centerfuge-fast-solids-001",
  "protocol_version": "0.1.0",
  "physical_result": {
    "run_completed": true,
    "containment_intact": true,
    "mass_closure": 0.991
  },
  "epistemic_result": {
    "claim": "bounded separation demonstrated",
    "scope": "specified batches and operating condition only",
    "status": "D",
    "unresolved": [
      "humidity sensitivity",
      "scale dependence",
      "particle wear"
    ]
  }
}
\`\`\`

A completed physical run may validly produce an epistemic result of inconclusive.

## 13. Experimental progression

The immediate progression is commissioning with individual materials, followed by the nine-condition airflow-and-speed screen, replication of promising conditions, confirmatory trials with frozen outlet assignments, and comparisons against gravity, screening, magnetic extraction, airflow-only operation, and rotation-only operation.

Only afterward should experiments vary feed rate, residence time, outlet geometry, particle-size distribution, mixture ratio, and humidity. Changing all of them initially would make successful results difficult to explain and failed results difficult to repair.

The experiment's strongest contribution would not be proof that a vortex can move three visibly different materials. It would be a complete record of where classification comes from, where it stops working, and which continuations the evidence admits.
