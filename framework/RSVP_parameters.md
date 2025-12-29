# RSVP Field Theory: Parameter Reference

## Summary of Notation (Corrected)

| Symbol | Name | Role | Equation | Default Value |
|--------|------|------|----------|---------------|
| **φ** | Scalar field | Density/potential | ∂φ/∂t = D∇²φ − α‖∇S‖² | Initial condition |
| **v** | Vector field | Flow/alignment | ∂v/∂t = (1/τ)(v_target − v) | v_target = −β∇φ |
| **S** | Entropy field | Irreversible accumulator | ∂S/∂t = η‖v‖ + γφ² | Starts at ~0.1 |
| **D** | Diffusion | Scalar smoothing | φ equation | 0.1 |
| **α** | Entropy suppression | Structure cost | φ equation | 0.5 |
| **β** | Alignment strength | Flow → −∇φ | v equation | 0.8 |
| **τ** | Relaxation time | Vector memory | v equation | 20 |
| **η** | Flow dissipation | Entropy from ‖v‖ | S equation | 0.1 |
| **γ** | Structure cost | Entropy from φ² | S equation | 0.01 |

---

## Dimensional Analysis

All current parameters are **dimensionless** (natural units where fundamental scales = 1).

To assign physical units, choose base units:
- [x] = length (e.g., meters, Planck lengths)
- [t] = time (e.g., seconds, Planck times)
- [φ] = scalar density (e.g., kg/m³, dimensionless)

Then:
```
[D] = L²/T         (diffusivity)
[α] = 1            (dimensionless coupling)
[β] = 1            (dimensionless coupling)
[τ] = T            (time)
[η] = 1/T          (rate)
[γ] = 1/T          (rate)
```

For RSVP on lattice of spacing a and timestep Δt:
```
dx = a             (lattice constant)
dt = Δt            (evolution step)
D → D·Δt/a²        (rescaled diffusion)
```

---

## Parameter Regimes

### Diffusion-Dominated (D ≫ α, η, γ)
- φ spreads rapidly
- Structure is smooth
- Entropy accumulates slowly
- **Regime:** Equilibration toward uniform state

### Entropy-Limited (α ≫ D)
- Structure formation is strongly suppressed by entropy gradients
- φ develops localized features that resist diffusion
- **Regime:** Soliton-like persistent structures

### Flow-Dominated (η ≫ γ)
- Entropy production comes mainly from vector flow
- Structure cost (φ²) is negligible
- **Regime:** Turbulent-like dynamics

### Structure-Dominated (γ ≫ η)
- Entropy production comes mainly from maintaining φ gradients
- Flow contributes little
- **Regime:** Static patterns with slow evolution

### Fast Relaxation (τ ≪ 1)
- v instantly aligns with −β∇φ
- No memory effects
- **Regime:** Quasi-static flow

### Slow Relaxation (τ ≫ 1)
- v changes slowly, high inertia
- Flow patterns persist even as φ changes
- **Regime:** Hydrodynamic-like evolution

---

## Stability Constraints

### Diffusion Stability
```
dt ≤ dx² / (6D)
```

For our defaults (D=0.1, dx=1/32):
```
dt ≤ (1/32)² / (6·0.1) ≈ 0.0016
```

Current default dt = 0.05 is **on the edge** for 32³ grid. Reduce dt or increase D for stability.

### Relaxation Stability
```
dt ≤ τ
```

For τ=20, dt=0.05 is well within bound.

### Combined
```
dt ≤ min(dx²/(6D), τ) = min(0.0016, 20) = 0.0016
```

**Recommendation:** Use dt ≤ 0.001 for 32³ grid with current parameters.

---

## Suggested Parameter Scans

### Scan 1: Entropy Suppression (α)
Fix all others, vary α ∈ [0.0, 0.1, 0.5, 1.0, 2.0]

**Prediction:**
- α = 0: Pure diffusion, φ → uniform
- α = 0.5: Moderate structure formation
- α = 2.0: Strong localization, soliton-like

### Scan 2: Relaxation Timescale (τ)
Fix all others, vary τ ∈ [1, 5, 20, 50]

**Prediction:**
- τ = 1: v instantly follows −∇φ
- τ = 50: v has strong memory, hydrodynamic flow

### Scan 3: Entropy Sources (η vs γ)
Fix D, α, β, τ. Scan (η, γ) on grid:
- η ∈ [0.01, 0.1, 1.0]
- γ ∈ [0.001, 0.01, 0.1]

**Prediction:**
- η ≫ γ: Flow-dominated entropy
- γ ≫ η: Structure-dominated entropy

### Scan 4: Diffusion Strength (D)
Fix all others, vary D ∈ [0.01, 0.1, 0.5, 1.0]

**Prediction:**
- D = 0.01: Structures persist longer
- D = 1.0: Rapid smoothing, no structure

---

## Physical Interpretation Guide

### What does φ represent?
In RSVP context, φ could be:
- Lattice curvature scalar
- Entanglement density
- Information content per vertex
- Effective metric component

### What does v represent?
- Flow of information
- Preferred direction of lattice evolution
- Emergent "vector potential" (without gauge field)
- Alignment of local lattice structure

### What does S represent?
- Accumulated entropy (Shannon, von Neumann, or geometric)
- Irreversibility measure
- "Aging" of lattice configuration
- Coarse-graining cost

### Why is S not conserved?
S is **not a Noether charge**. It's a bookkeeping field that tracks irreversible processes. In full RSVP:
- S emerges from coarse-graining
- S ↔ information loss at small scales
- dS/dt ≥ 0 is the second law, not a symmetry

---

## Connection to Standard Field Theories

### Klein-Gordon (scalar field)
```
∂²φ/∂t² = ∇²φ − m²φ
```

Our φ equation with α=0, η=0, γ=0:
```
∂φ/∂t = D∇²φ
```

This is **diffusion**, not wave propagation (first-order in time, not second).

To get Klein-Gordon-like behavior, need:
- Second time derivative (inertia)
- Mass term (potential)

### Navier-Stokes (fluid flow)
```
∂v/∂t + (v·∇)v = ν∇²v − ∇p
```

Our v equation **lacks**:
- Advection term (v·∇)v
- Pressure gradient ∇p
- Viscosity ∇²v

Instead we have:
```
∂v/∂t = (1/τ)(−β∇φ − v)
```

This is **relaxation toward potential flow**, not hydrodynamics.

### Maxwell (electromagnetism)
```
∂E/∂t = ∇×B,  ∂B/∂t = −∇×E
```

Our system has **no curl-curl structure**. Extension B adds vorticity feedback:
```
∂v/∂t += ε(∇×v)
```

But this is still not Maxwell (no dual field, no gauge invariance).

---

## Comparison Table

| Property | RSVP (this model) | Klein-Gordon | Navier-Stokes | Maxwell |
|----------|-------------------|--------------|---------------|---------|
| Time order | 1st (diffusion) | 2nd (wave) | 1st (dissipative) | 1st (wave) |
| Conserved energy | ❌ | ✅ | ❌ | ✅ |
| Entropy | ✅ (monotonic) | ❌ | ✅ (implicit) | ❌ |
| Gauge symmetry | ❌ | ❌ | ❌ | ✅ |
| Lorentz invariant | ❌ | ✅ | ❌ | ✅ |
| Irreversible | ✅ | ❌ | ✅ | ❌ |

**Key difference:** RSVP is fundamentally **dissipative** and **irreversible**, unlike fundamental field theories which are time-reversible.

---

## How to Modify Parameters in Code

Edit `rsvp_core.py`:

```python
# ========== Parameters ==========
D = 0.1      # Diffusion coefficient
ALPHA = 0.5  # Entropy-gradient suppression
BETA = 0.8   # Vector alignment strength
TAU = 20.0   # Relaxation timescale
ETA = 0.1    # Entropy from flow
GAMMA = 0.01 # Entropy from structure
# ================================
```

Then run:
```bash
make sim
make plot
```

**Warning:** Changing parameters may violate stability conditions. Always check:
```
dt ≤ dx² / (6D)
```

Adjust dt in `run_sim.py` if needed.

---

## Further Reading

- **Diffusion equations:** Crank-Nicolson, ADI methods for implicit schemes
- **Entropy in field theory:** Boltzmann H-theorem, Bekenstein bound
- **Irreversible thermodynamics:** Onsager relations, fluctuation-dissipation
- **Relaxation dynamics:** Ginzburg-Landau, Allen-Cahn equations
- **Lattice field theory:** Wilson action, continuum limit

This model is closest to **reaction-diffusion systems** with an additional entropy accounting field.