# Centerfuge: Boundary-Aware Operating Architecture

**Safety contract:** [Safety and Maintenance Specification](safety-maintenance-spec.md)

## 1. Architectural claim

The Centerfuge is not one universal machine that accepts undifferentiated household matter and converts it directly into useful goods. It is a federation of physically and epistemically isolated subsystems organized around a shared intake, characterization, separation, and routing core.

Its governing operation is not simply

\[
\text{waste} \longrightarrow \text{resource},
\]

but

\[
x \xrightarrow{\text{observe}} \widehat{x}
\xrightarrow{\text{admit/refuse}} c
\xrightarrow{\text{transform}} y
\xrightarrow{\text{verify}} \widehat{y}
\xrightarrow{\text{route}} d.
\]

Here \(x\) is the received material, \(\widehat{x}\) is the machine's fallible description of it, \(c\) is an admitted processing class, \(y\) is the transformed output, \(\widehat{y}\) is the verified output description, and \(d\) is an authorized destination.

Material can pass successfully through a separator without becoming safe, pure, food-compatible, structurally reliable, or suitable for fabrication. Physical displacement is not epistemic certification.

The Centerfuge vision includes construction, repair, clothing, food, and hyperbolation. This architecture preserves that scope while preventing those functions from collapsing into an unqualified claim of universal recycling.

## 2. The primary boundary

Let the complete system be

\[
\mathcal{C} =
(B,I,G,S,R,F,H,W,L_{\mathrm{phys}},L_{\mathrm{epi}}),
\]

where \(B\) is physical containment, \(I\) is intake and characterization, \(G\) is the rotating separation core, \(S\) is routing and storage, \(R\) is repair and fabrication, \(F\) is the isolated food-and-clothing domain, \(H\) is hyperbolation, \(W\) is refusal and residue handling, and the final two terms are the physical and epistemic ledgers.

The appliance boundary includes its loading chamber, sensors, interlocks, separators, ducts, bins, cleaning systems, local fabrication tools, hyperbolation equipment, control system, and containment structure. It does not include municipal waste systems, hazardous-material treatment, mining and primary refining, industrial polymer reclamation, biological composting infrastructure, or the household objects into which certified outputs are later incorporated.

Those external processes remain environmental dependencies. The Centerfuge may prepare or package material for them, but it must not represent transfer to an external processor as completed recovery.

## 3. Two ledgers

Every batch \(b\) produces two related but non-identical records. The physical ledger records what happened:

\[
L_{\mathrm{phys}}(b)=
\{m_{\mathrm{in}},m_{\mathrm{out}},E_{\mathrm{in}},\omega(t),T(t),
p(t),t_{\mathrm{res}},\text{valve states},\text{measured destinations}\}.
\]

The epistemic ledger records what the observations warrant:

\[
L_{\mathrm{epi}}(b)=
\{\text{claimed identity},\text{confidence},\text{tests performed},
\text{unresolved ambiguity},\text{authorized uses},\text{prohibited uses},
\text{evidence status}\}.
\]

A batch may have the physical record "entered polymer bin 3" while retaining the epistemic record "mixed or unidentified thermoplastic; non-food use only." The first describes location. The second controls what may happen next.

Neither ledger may silently repair the other. A high-confidence classification does not prove that routing physically succeeded, while a successful routing event does not prove that the classification was correct.

## 4. Material states and admission

Material moves through explicit custody states:

\[
\text{Presented}\rightarrow\text{Quarantined}\rightarrow
\text{Characterized}\rightarrow\text{Admitted}\rightarrow
\text{Processed}\rightarrow\text{Verified}\rightarrow\text{Released}.
\]

Refusal is possible from every state before release. Unknown is not a temporary inconvenience that the controller is expected to guess away. It is a stable and valid terminal classification.

A process-relative admission relation is

\[
\operatorname{Admit}(x,p)
\iff K(x)\land C(x,p)\land H(x,p)\leq H_{\max}(p),
\]

where \(K(x)\) means that the required properties of \(x\) are known, \(C(x,p)\) means those properties are compatible with process \(p\), and \(H(x,p)\) is estimated process hazard.

Classification confidence alone does not determine admission. A high-confidence identification can still be inadmissible if the remaining uncertainty includes batteries, solvents, pressurized vessels, biological contamination, or incompatible polymers.

## 5. Admissible inputs

Admission is process-relative. There is no single category called "Centerfuge-safe material."

| Input class | Default disposition | Conditions for admission |
| --- | --- | --- |
| Clean, dry, known rigid objects | Mechanical characterization | Size, mass, and geometry within chamber limits |
| Known metals | Sorting or fabrication feedstock | Alloy uncertainty compatible with intended output |
| Known single-polymer articles | Non-food material recovery | Resin identity and contamination limits verified |
| Clean textiles | Fiber sorting or textile processing | Fiber composition, coatings, and biological condition known |
| Unpackaged food | Food subsystem only | Kept outside reclaimed-material circulation |
| Food packaging | General characterization | Never presumed food-safe merely from prior use |
| Mixed or wet household residues | Quarantine or limited preprocessing | Moisture, biological load, and reactive components assessed |
| Glass and ceramics | Controlled geometric processing | Breakage and fragment containment available |
| Electronics | External disassembly route by default | Batteries and hazardous components removed under a validated procedure |
| Batteries, lamps, pesticides, solvents, paint, and aerosols | Refuse to main process | Transfer intact to an appropriate external waste stream |
| Pressurized, reactive, radioactive, medical, or compositionally unknown material | Hard refusal | No autonomous destructive processing |

EPA identifies paints, cleaners, oils, batteries, and pesticides as household hazardous waste because they may be toxic, corrosive, ignitable, reactive, or explosive. Lithium batteries should be diverted to collection or hazardous-waste facilities rather than mechanically processed in the household machine. See the EPA guidance on [household hazardous waste](https://www.epa.gov/hw/household-hazardous-waste-hhw) and [lithium-ion battery recycling](https://www.epa.gov/hw/lithium-ion-battery-recycling-frequently-asked-questions).

## 6. Operating sequence

### 6.1 Presentation and quarantine

Material first enters a stationary, closable presentation chamber. No object reaches the rotating core directly from the room.

The chamber establishes mass, approximate dimensions, visual condition, temperature, moisture, volatile-compound indications, magnetic response, electrical activity, and evidence of pressure or stored energy. Imaging and spectroscopy may propose identities, but each sensor produces evidence rather than truth.

The chamber returns one of four decisions:

\[
D(x)\in\{\mathrm{ADMIT}(p),\mathrm{DIVERT}(q),\mathrm{AUDIT},\mathrm{REFUSE}\}.
\]

ADMIT authorizes one named process. DIVERT sends the intact object to a protected collection route. AUDIT requests additional observation or human identification. REFUSE returns or isolates it without destructive action.

### 6.2 Preparation

Preparation may include controlled opening, coarse disassembly, size reduction, drying, cleaning, or removal of known fasteners. Each is an independent transformation with its own admission predicate.

Size reduction is especially consequential. Before comminution, a mistaken object may remain recoverable. After shredding, its identity, contamination, and stored hazards may be distributed throughout the machine. Shredding therefore follows, rather than precedes, the strongest practical hazard screen.

### 6.3 Rotational entrainment

Admitted material enters a contained rotating chamber. Depending on the selected regime, this may use a rotating wall, internal rotor, controlled air vortex, liquid carrier, perforated basket, or a combination.

For a particle at radius \(r\) rotating with angular speed \(\omega\), the idealized outward inertial acceleration in the rotating frame is

\[
a_c=\omega^2r,
\]

and the corresponding radial force is

\[
F_c=m_p\omega^2r.
\]

This does not establish that a particle will separate. Separation also depends on particle size, shape, carrier density and viscosity, collisions, wall interaction, turbulence, adhesion, moisture, and residence time.

### 6.4 Separation

The rotating core is a configurable sequence of separation operations rather than one universal vortex. A candidate sequence is geometric screening, ballistic or inertial separation, aerodynamic classification, magnetic extraction, optical identification, and collection by gated radial or axial outlets.

| Mechanism | Principal discriminator | Main limitation |
| --- | --- | --- |
| Screen or aperture | Size and geometry | Flexible objects deform; apertures clog |
| Inertial or ballistic | Mass-to-drag response | Shape and collisions complicate trajectories |
| Aerodynamic | Terminal response and projected area | Density cannot be inferred independently of shape |
| Magnetic | Magnetic susceptibility | Nonmagnetic alloys and composites remain |
| Eddy-current | Electrical conductivity | Geometry and rotor conditions affect response |
| Optical or spectroscopic | Surface composition or appearance | Coatings, dirt, and hidden layers confound classification |
| Electrostatic | Charge response and conductivity | Humidity and surface condition matter |
| Chemical | Solubility or reaction | Creates contamination and reagent-management burdens |

Density-based sorting is not shorthand for rotational sorting. A centrifuge separates according to differential motion in a carrier, not density in isolation.

For a small spherical particle in a viscous carrier under a Stokes-regime approximation,

\[
v_r=\frac{d_p^2(\rho_p-\rho_f)\omega^2r}{18\mu},
\]

where \(d_p\) is particle diameter, \(\rho_p\) and \(\rho_f\) are particle and carrier-fluid densities, and \(\mu\) is dynamic viscosity. This applies only when

\[
\operatorname{Re}_p=\frac{\rho_f|v_r|d_p}{\mu}\ll 1.
\]

Outside that regime, drag is expressed through a drag coefficient:

\[
F_D=\frac12 C_D\rho_fA_pv_{\mathrm{rel}}^2.
\]

Two objects of identical material but different geometry can follow different paths, while objects of different density can overlap dynamically. Every claimed separation requires a measured operating envelope.

### 6.5 Routing

A separator does not produce useful material until the correct fraction is captured without cross-contamination. Routing consists of verified gates, ducts, buffers, and bins whose states are recorded in \(L_{\mathrm{phys}}\).

Each fraction receives a provisional identity:

\[
f_i=(\widehat{c_i},q_i,\sigma_i,U_i),
\]

where \(\widehat{c_i}\) is its proposed class, \(q_i\) is estimated purity, \(\sigma_i\) is uncertainty, and \(U_i\) is the set of authorized downstream uses.

No fraction proceeds merely because its intended bin is full. It proceeds because the batch is re-observed after collection and the downstream subsystem accepts its material contract.

## 7. Bounded downstream subsystems

### 7.1 Fabrication

Fabrication converts certified feedstocks into non-food components. Its boundary begins only after a fraction has an adequate composition, contamination profile, particle-size distribution, moisture level, and thermal history.

Possible transformations include remelting and extrusion of known thermoplastics, compression molding, casting of known low-temperature alloys, fiber pressing, additive manufacture, subtractive finishing, and assembly from recovered standard parts.

Geometric completion is distinct from functional certification. A printed bracket that matches intended dimensions has not thereby demonstrated load capacity, creep resistance, fire behavior, fatigue life, or long-term compatibility.

An output \(y\) may be released for use \(u\) only if

\[
\operatorname{Release}(y,u)=
\operatorname{MaterialAdmissible}(y,u)\land
\operatorname{GeometryVerified}(y)\land
\operatorname{FunctionTested}(y,u).
\]

Safety-critical structural, electrical, pressure-bearing, fire-containment, and potable-water parts remain outside autonomous fabrication until process-specific qualification exists.

### 7.2 Repair

Repair is a custody-preserving transformation of an existing object whose prior identity and intended function matter. A repair transaction records

\[
r=(o,f,a,\Delta,t),
\]

where \(o\) is the object, \(f\) the diagnosed failure, \(a\) the authorized intervention, \(\Delta\) the actual material or geometric change, and \(t\) the post-repair test.

The machine preserves three separate claims:

\[
\text{repair proposed}\neq\text{repair executed}\neq\text{repair verified}.
\]

A repair remains open until its functional test passes. If verification is impossible, the output may be returned as modified but uncertified; it must not be labeled repaired.

### 7.3 Clothing and textiles

The clothing subsystem accepts identified fibers, intact reusable cloth, known thread, and verified accessories. It may clean, unravel, card, blend, spin, weave, knit, cut, patch, or assemble.

Blended fibers, coatings, dyes, elastic elements, fasteners, biological contamination, and flame retardants may be hidden. Appearance cannot establish fiber composition or safe processing temperature.

The subsystem should initially support repair and recomposition of known textiles before attempting chemical recovery of mixed fibers. Outputs retain composition and processing histories rather than being represented as equivalent to virgin material.

### 7.4 Food

The food subsystem is physically isolated from waste-derived material processing. It has separate air handling, surfaces, tools, storage, drainage, cleaning validation, and consumables.

Food production from unknown post-consumer matter is inadmissible. The full vision includes food preparation, portioning, preservation, inventory management, and packaging, but ingredients enter through a food-only custody path.

Recovered polymer does not regain food-contact status merely because it was washed, spectroscopically identified, or previously served as food packaging. FDA guidance treats recycled-plastic purity and food-contact suitability as process-specific questions. See the FDA material on [recycled plastics in food packaging](https://www.fda.gov/food/packaging-food-contact-substances-fcs/recycled-plastics-food-packaging) and [food-contact substances](https://www.fda.gov/food/food-packaging-other-substances-come-contact-food-information-consumers/understanding-how-fda-regulates-substances-come-contact-food).

The governing separation is

\[
\mathcal{M}_{\mathrm{recovered}}\cap\mathcal{M}_{\mathrm{food}}=\varnothing
\]

unless a particular recovery process independently establishes food-contact suitability.

### 7.5 Hyperbolation

Hyperbolation is a terminal custody protocol rather than an additional separation mechanism. Given a parcel \(p\), it constructs

\[
H(p)=(p,E_1,\ldots,E_n,\lambda,\pi,\tau),
\]

where \(E_i\) are protective or functional envelope layers, \(\lambda\) is a machine- and human-readable label, \(\pi\) is provenance, and \(\tau\) is a set of permitted future transitions.

The resulting gnotobiotic hyperball or cognet does not certify purity by wrapping it. It preserves the parcel's known state, limits contamination, exposes uncertainty, and controls future access.

A hyperball label records its source batch, measured composition, confidence, contamination status, mass, creation time, permitted environments, prohibited uses, reopening instructions, and destination. Unknown or hazardous material may be hyperbolated for containment and transfer, but remains "contained unknown" or "contained hazard," never "recovered resource."

Hyperbolation is a monotonic custody operation:

\[
K_{t+1}=K_t+\text{new observations},
\]

without deleting prior uncertainty or provenance. Later evidence may refine status but may not retroactively erase uncertainty.

## 8. Conservation balances

For a batch over interval \([t_0,t_1]\),

\[
m_{\mathrm{in}}+m_{\mathrm{consumables}}
=m_{\mathrm{products}}+m_{\mathrm{residues}}+
m_{\mathrm{emissions}}+\Delta m_{\mathrm{inventory}}.
\]

The residual

\[
\epsilon_m=m_{\mathrm{in}}+m_{\mathrm{consumables}}-
m_{\mathrm{products}}-m_{\mathrm{residues}}-
m_{\mathrm{emissions}}-\Delta m_{\mathrm{inventory}}
\]

must remain within a stated tolerance. Unaccounted mass may indicate dust deposition, liquid retention, leaks, sensor error, or trapped material; it is not automatically process loss.

The energy balance is

\[
E_{\mathrm{elec}}+E_{\mathrm{thermal,in}}+E_{\mathrm{chemical,in}}
=\Delta U+\Delta K_{\mathrm{rot}}+W_{\mathrm{useful}}+
Q_{\mathrm{loss}}+E_{\mathrm{exhaust}}.
\]

For a rotating assembly,

\[
E_{\mathrm{rot}}=\frac12J\omega^2,\qquad
L=J\omega,\qquad
\tau_{\mathrm{drive}}=\frac{dL}{dt}+\tau_{\mathrm{loss}}.
\]

Imbalance is tracked through vibration and estimated eccentric mass moment:

\[
F_{\mathrm{imbalance}}\approx m_e e\omega^2.
\]

Because force rises with \(\omega^2\), overspeed and imbalance are coupled hazards.

Residence time for fraction \(i\) is

\[
t_{\mathrm{res},i}=t_{\mathrm{exit},i}-t_{\mathrm{entry},i}.
\]

In continuous operation,

\[
\bar t_{\mathrm{res}}\approx\frac{V_{\mathrm{active}}}{Q},
\]

but the actual distribution requires tracer measurement because recirculation, dead zones, adhesion, and intermittent gates invalidate a single nominal value.

The architecture records throughput and specific energy,

\[
\dot m=\frac{m_{\mathrm{processed}}}{\Delta t},
\qquad
e_s=\frac{E_{\mathrm{input}}}{m_{\mathrm{admitted}}},
\]

together with purity, recovery, contamination, rejection, breakage, and cleaning burden.

## 9. Refusal and containment

Refusal is an active machine state, not a generic error. It leaves material identifiable, contained, and recoverable wherever possible. The machine stops feed, isolates the relevant chamber, reaches a mechanically safe state, preserves ventilation or suppression where stopping it would increase danger, records the causal observations, and exposes a bounded recovery procedure.

Processing grain, sugar, wood, textiles, polymers, and other fine solids can create combustible atmospheres. OSHA guidance emphasizes ignition control, containment, housekeeping, and equipment appropriate to the dust hazard. "Dry enough to process" cannot mean "safe to aerosolize," and food-system flour or sugar handling cannot share exhaust paths with general recovery. See the [OSHA combustible-dust guidance](https://www.osha.gov/otm/section-4-safety-hazards/chapter-5).

A safe state is not necessarily total power loss:

\[
s_{\mathrm{safe}}=
\arg\min_{s\in S_{\mathrm{reachable}}}
\operatorname{Risk}(s\mid\widehat{x},L_{\mathrm{phys}}).
\]

It may require controlled braking instead of abrupt stopping, continued extraction instead of shutting fans off, or continued cooling while material motion is inhibited.

## 10. Evidence status

| Status | Meaning |
| --- | --- |
| **V — Vision** | Intended capability without a specified mechanism |
| **M — Modeled** | Equations, assumptions, and a predicted operating envelope exist |
| **S — Simulated** | Exercised computationally under recorded parameters |
| **D — Demonstrated** | Repeatable physical measurements exist for a bounded test article |
| **Q — Qualified** | Process-specific tests required for a named use have passed |

These statuses do not advance automatically. A Blender animation may support S for geometry or presentation, but not D for separation. A benchtop separation test may support D for one feedstock and speed range but not Q for unattended household operation.

At present, the integrated architecture is predominantly V. Standard physical relations support parts of the rotational model at M, but do not demonstrate the proposed appliance. Existing renders are evidence of representational and procedural development, not yet evidence that the material mechanisms work.

## 11. First falsifiable system model

The concrete protocol for this stage is [Fast Solids Lab Experiment 001: Air-Assisted Classification of Polystyrene, Salt, and Steel](../experiments/fast_solids_lab/protocols/experiment-001.md).

The complete vision remains in the architecture, but its first physical test should be narrow.

A suitable specimen accepts a known, clean, dry mixture of three nonhazardous components with controlled size and shape. It measures mass before and after processing, records speed, airflow, power, vibration, and residence time, collects every fraction, and calculates purity and recovery:

\[
P_i=\frac{m_{i\rightarrow i}}{\sum_jm_{j\rightarrow i}},
\qquad
R_i=\frac{m_{i\rightarrow i}}{m_{i,\mathrm{input}}}.
\]

The experiment fails if it cannot beat a simple baseline such as screening, gravity settling, manual sorting, or a conventional cyclone under comparable conditions. It also fails if mass cannot be reconciled, dust escapes containment, vibration crosses the stop threshold, outputs cannot be traced to their batch, or the device reports a classification beyond what its measurements warrant.

This test would not demonstrate fabrication, repair, food production, clothing manufacture, or hyperbolation as a whole. It would establish the first trustworthy transition upon which those subsystems depend.

## 12. Common notation

| Symbol | Meaning |
| --- | --- |
| \(x,\widehat{x}\) | Presented material and its observed description |
| \(p\) | Named process |
| \(b\) | Batch |
| \(m\) | Mass |
| \(r\) | Radial position |
| \(\omega\) | Angular speed |
| \(J\) | Rotational moment of inertia |
| \(L\) | Angular momentum |
| \(\tau\) | Torque |
| \(d_p\) | Particle diameter |
| \(\rho_p,\rho_f\) | Particle and carrier-fluid densities |
| \(\mu\) | Dynamic viscosity |
| \(C_D\) | Drag coefficient |
| \(t_{\mathrm{res}}\) | Residence time |
| \(q_i\) | Estimated fraction purity |
| \(\sigma_i\) | Classification uncertainty |
| \(U_i\) | Authorized uses |
| \(L_{\mathrm{phys}}\) | Physical event ledger |
| \(L_{\mathrm{epi}}\) | Epistemic warrant ledger |

## 13. Architectural statement

The Centerfuge is a household-scale material-custody architecture organized around controlled rotation but not reducible to a centrifuge. It observes presented matter, admits only process-compatible inputs, separates them through explicitly named physical mechanisms, preserves mass and transformation records, and routes fractions only to downstream subsystems whose contracts they satisfy.

Fabrication, repair, clothing, food, and hyperbolation remain distinct domains with separate contamination, verification, and release boundaries. Unknown material is contained rather than guessed; completed motion is not mistaken for completed recovery; a stated repair is not mistaken for an executed one; and an executed repair is not mistaken for a verified one.

The machine's central product is therefore not merely separated matter, but matter whose permitted continuations are made explicit.
