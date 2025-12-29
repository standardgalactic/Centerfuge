# RSVP Field Theory: Quick Reference Card

---

## The Three Equations

```
∂φ/∂t = D∇²φ − α‖∇S‖²         [Scalar: diffusion with entropy suppression]

∂v/∂t = (1/τ)(−β∇φ − v)       [Vector: relaxation toward −∇φ]

∂S/∂t = η‖v‖ + γφ²             [Entropy: monotonic accumulation]
```

---

## Parameters (Dimensionless)

| D | α | β | τ | η | γ |
|---|---|---|---|---|---|
| 0.1 | 0.5 | 0.8 | 20 | 0.1 | 0.01 |

---

## Boundary Conditions

**Periodic:** φ(x+L) = φ(x) on torus Ω = [0,L]³

---

## Stability

```
dt ≤ min(dx²/(6D), τ)

For 32³ grid (dx = 1/32, D = 0.1):  dt ≤ 0.0016
```

---

## Conserved/Monotonic Quantities

| Quantity | Formula | Property |
|----------|---------|----------|
| Total entropy | S_tot = ∫S dV | dS_tot/dt ≥ 0 |
| Kinetic energy | E_kin = (1/2)∫‖v‖² dV | Not conserved |
| Potential energy | E_pot = (1/2)∫‖∇φ‖² dV | Not conserved |

---

## Physical Interpretation

- **φ**: Structure/information density
- **v**: Emergent flow (alignment, not force)
- **S**: Irreversible entropy accumulation
- **α**: How much entropy suppresses structure
- **η, γ**: How flow and structure generate entropy

---

## Key Properties

✅ Entropy monotonically increases  
✅ No conserved energy (dissipative)  
✅ No gauge symmetry  
✅ No Lorentz invariance  
✅ First-order in time (diffusive, not wave-like)  
✅ Irreversible dynamics  

---

## Validation Tests

1. **Entropy monotonicity:** S_tot(t+dt) ≥ S_tot(t)
2. **Diffusion stability:** dt ≤ dx²/(6D)
3. **Energy dissipation:** E_total decreases
4. **Diffusion limit:** α=0 ⟹ ∂φ/∂t = D∇²φ
5. **Relaxation limit:** τ→0 ⟹ v = −β∇φ

---

## Code Structure

```
sim/rsvp_core.py       # PDEs (this card)
sim/run_sim.py         # Driver + diagnostics
sim/plot_diagnostics.py # Entropy/energy plots
blender/render_*.py    # Visualization backend
```

---

## Notation Fix (Critical)

**OLD (wrong):** Used β for both alignment and flow dissipation  
**NEW (correct):** 
- β = alignment strength in v equation
- η = flow dissipation in S equation

---

## Run Workflow

```bash
make sim      # Evolve fields → sim/fields/*.npz
make plot     # Diagnostics → out/diagnostics.png
make geonodes # Fast render → out/renders/geonodes.png
make full     # Complete pipeline → video
```

---

## Quasi-Steady Regime

At equilibrium: **φ = 0, v = 0** (only trivial solution)

Instead, study **quasi-steady** where:
- ∂φ/∂t ≈ 0
- ∂v/∂t ≈ 0
- ∂S/∂t > 0 (continues to grow slowly)

This is thermodynamically consistent: true equilibrium = maximum entropy = death.

---

## Optional Extensions (Toggleable)

**Entropy damping:**  v → v/(1+κS)  
**Vorticity feedback:**  ∂v/∂t += ε(∇×v)

Enable in `rsvp_core.py`:
```python
ENABLE_ENTROPY_DAMPING = True
ENABLE_VORTICITY_FEEDBACK = True
```

---

## What This Is NOT

❌ Klein-Gordon (no wave equation)  
❌ Navier-Stokes (no advection, pressure)  
❌ Maxwell (no gauge field, dual structure)  
❌ General Relativity (no metric dynamics)  

---

## What This IS

✅ Reaction-diffusion system with entropy  
✅ Thermodynamically consistent field theory  
✅ Testbed for entropy-driven dynamics  
✅ Falsifiable numerical model  

---

## Connection to Full RSVP

This is a **continuous field approximation** of the RSVP lattice. It tests:
- Can entropy limit structure formation?
- Can alignment emerge without forces?
- Is irreversibility sufficient for complexity?

Full RSVP would derive these from:
- Discrete lattice geometry
- Information-theoretic entropy
- Coarse-graining from fundamental scale

---

## One-Line Summary

**Scalar field diffuses, vector field aligns with gradient, entropy accumulates—all without conserved energy or forces.**

---

## For Paper: Equations Box

```
Minimal RSVP Field Theory

∂φ/∂t = D∇²φ − α‖∇S‖²
∂v/∂t = (1/τ)(−β∇φ − v)
∂S/∂t = η‖v‖ + γφ²

Periodic boundaries, explicit Euler, dt ≤ dx²/(6D)
```

---

## Reproducibility

Every equation corresponds exactly to code in `rsvp_core.py`.

**No handwaving. No hidden parameters. Fully falsifiable.**

---

*This card is a complete, self-contained reference for the RSVP field theory implementation.*