# RSVP: Mathematical Formulation

## Field Equations

Let Ω ⊂ ℝ³ and let φ(x,t), v(x,t), S(x,t) denote a scalar density/potential, a vector alignment (flow) field, and an entropy accumulator, respectively. We consider the coupled evolution:

### Scalar Evolution

```
∂φ/∂t = D∇²φ − α‖∇S‖²

where ‖∇S‖² = (∂S/∂x)² + (∂S/∂y)² + (∂S/∂z)²
```

**Physical interpretation:**
- **D∇²φ**: Diffusion term (smoothing, energy minimization)
- **−α‖∇S‖²**: Entropy-gradient suppression (structure cost)

The scalar field φ diffuses but is actively suppressed in regions of high entropy gradient. This creates **entropy-limited structure formation**.

### Vector Evolution (Relaxation-to-Gradient Alignment)

```
∂v/∂t = (1/τ)(v_target − v)

where v_target = −β∇φ
```

**Physical interpretation:**
- Vector field **relaxes toward** −∇φ with timescale τ
- This is **alignment without force** (no acceleration)
- Memory term (1−dt/τ) gives inertia

**Discrete update:**
```
v(t+dt) = (1 − dt/τ)v(t) + (dt/τ)(−β∇φ)
```

### Entropy Evolution (Irreversible Accumulation)

```
∂S/∂t = η‖v‖ + γφ²

where ‖v‖ = √(v_x² + v_y² + v_z²)
```

**Physical interpretation:**
- **η‖v‖**: Dissipation from flow magnitude
- **γφ²**: Structure cost (maintaining φ gradients)
- **∂S/∂t ≥ 0** pointwise (second law)

---

## Numerical Discretization

**Spatial grid:** N³ lattice with periodic boundary conditions, spacing dx  
**Time integration:** Explicit forward Euler with timestep dt

### Periodic Boundary Conditions

All fields are periodic on the torus: φ(x+L) = φ(x) where L = N·dx is the domain size.

Spatial derivatives use centered finite differences with `np.roll` for periodicity:

```
∂f/∂x ≈ (f[i+1] - f[i-1]) / (2dx)    (periodic wrap via roll)
```

### Laplacian (Corrected Implementation)

```
∇²φ = ∂²φ/∂x² + ∂²φ/∂y² + ∂²φ/∂z²
```

Centered finite difference stencil:
```
∂²φ/∂x² ≈ (φ[i+1] - 2φ[i] + φ[i-1]) / dx²
```

Implemented as:
```python
def periodic_laplacian(f, dx):
    lap = np.zeros_like(f)
    for axis in range(3):
        f_plus = np.roll(f, -1, axis=axis)
        f_minus = np.roll(f, 1, axis=axis)
        lap += (f_plus - 2.0*f + f_minus) / (dx*dx)
    return lap
```

### Gradient (Periodic)

```python
def periodic_gradient(f, dx, axis):
    f_plus = np.roll(f, -1, axis=axis)
    f_minus = np.roll(f, 1, axis=axis)
    return (f_plus - f_minus) / (2.0*dx)
```

---

## Stability Conditions

### Diffusion Stability (Explicit Euler, 3D)

```
dt ≲ dx² / (6D)
```

This is the conservative CFL-like condition for explicit diffusion on a 3D Cartesian grid.

### Relaxation Stability

For the convex combination in v update to remain stable:
```
dt ≤ τ
```

Typically use dt ≪ τ for accuracy.

### Combined Condition

```
dt ≤ min(dx²/(6D), τ)
```

Our implementation checks this automatically and warns if violated.

---

## Conserved and Monotonic Quantities

### Total Entropy (Monotonic)

Define total entropy:
```
S_total(t) = ∫_Ω S(x,t) dV

dS_total/dt = ∫_Ω [η‖v‖ + γφ²] dV ≥ 0
```

**Note:** S_total is non-decreasing in the continuum model. In discrete time-stepping we monitor monotonicity up to numerical tolerance (discretization errors can cause small local decreases).

### Entropy Production Rate

```
dS/dt = ∫_Ω [η‖v‖ + γφ²] dV ≥ 0
```

This quantifies irreversible dissipation.

### Energy Components

**Kinetic energy:**
```
E_kin = (1/2) ∫_Ω ‖v‖² dV
```

**Potential energy:**
```
E_pot = (1/2) ∫_Ω ‖∇φ‖² dV
```

**Total energy is not conserved** because entropy production is irreversible. Energy dissipates into entropy over time.

---

## Parameters (Dimensionless Reference)

Current implementation uses:

| Parameter | Symbol | Value | Physical meaning |
|-----------|--------|-------|------------------|
| Diffusion | D | 0.1 | Scalar smoothing rate |
| Entropy suppression | α | 0.5 | Structure cost weight |
| Vector alignment | β | 0.8 | Flow alignment strength |
| Relaxation time | τ | 20 | Vector memory timescale |
| Flow dissipation | η | 0.1 | Entropy from flow |
| Structure cost | γ | 0.01 | Entropy from gradients |

These are **dimensionless** in the current formulation. Physical units would require dimensional analysis of the underlying field theory.

---

## Equilibrium and Quasi-Steady Regimes

At strict equilibrium (∂/∂t = 0):

```
∂φ/∂t = 0  ⟹  D∇²φ = α‖∇S‖²
∂v/∂t = 0  ⟹  v = −β∇φ
∂S/∂t = 0  ⟹  η‖v‖ + γφ² = 0
```

The last condition implies η‖v‖ + γφ² = 0, which for η, γ > 0 requires **v = 0 and φ = 0** (trivial fields).

**Physical interpretation:** The system generally has no nontrivial fixed point because S accumulates irreversibly. Instead we study **quasi-steady regimes** where φ and v stabilize while S continues to increase at a slow rate.

This is fully consistent with irreversible thermodynamics: true equilibrium is maximum entropy (uniform, structureless).

---

## Optional Extensions (Toggleable)

These are RSVP-consistent extensions that can be enabled via flags in the code.

### Extension A: Entropy Damping

```
v → v / (1 + κS)
```

**Physical interpretation:** Entropy resists coherent flow (prevents blow-ups).

### Extension B: Vorticity Feedback

```
∂v/∂t += ε(∇ × v)
```

**Physical interpretation:** Weak torsion / lamphrodyne-style circulation without introducing forces.

**Implementation:**
```
curl_v = ∇ × v = (
    ∂v_z/∂y - ∂v_y/∂z,
    ∂v_x/∂z - ∂v_z/∂x,
    ∂v_y/∂x - ∂v_x/∂y
)
```

---

## Validation Tests

### 1. Entropy Monotonicity
Check that S_total(t+dt) ≥ S_total(t) at every timestep (up to numerical tolerance ~10⁻⁶).

### 2. Diffusion Stability
Verify dt ≤ dx²/(6D) throughout simulation.

### 3. Energy Dissipation
Confirm E_total = E_kin + E_pot decreases over time due to entropy production.

### 4. Diffusion Limit
In the limit α → 0, φ should satisfy pure diffusion equation:
```
∂φ/∂t = D∇²φ
```

### 5. Relaxation Limit
In the limit τ → 0, v should instantly align with −β∇φ:
```
v = −β∇φ
```

### 6. Regime Behavior
Identify quasi-steady plateaus in φ and v while S grows monotonically.

---

## Relation to RSVP Theory

These equations implement a **minimal thermodynamically consistent field theory** where:

1. **Structure (φ) costs entropy** (γφ² term)
2. **Flow (v) generates entropy** (η‖v‖ term)
3. **Entropy limits structure** (−α‖∇S‖² suppression)
4. **Vector alignment emerges** (no force, just relaxation toward −∇φ)
5. **Irreversibility is built in** (S_total monotonically increases)

This is **not** the full RSVP lattice theory, but a continuous field approximation suitable for:
- Numerical simulation
- Visualization
- Testing entropy-based dynamics
- Falsifying structure-formation claims

---

## Implementation Notes

### Boundary Conditions
**Periodic boundaries** on the torus Ω = [0,L]³ with L = N·dx, implemented via `np.roll`.

Alternative boundary conditions (not currently implemented):
- **Dirichlet:** φ = 0 at ∂Ω
- **Neumann:** ∂φ/∂n = 0 at ∂Ω (no flux)
- **Open/Absorbing:** Mur boundaries for wave exit

### Numerical Hygiene
- Always check stability condition before running long simulations
- Monitor entropy monotonicity as a sanity check (violations indicate discretization errors)
- Use `np.clip()` for bounds to prevent numerical overflow (not physics constraints)
- Periodic boundaries eliminate edge effects but impose topology (torus not sphere)

### Performance
For N³ lattice:
- **Memory:** ~12N³ floats (φ, v, S) ≈ 1.5 MB for 32³
- **Compute:** O(N³) per timestep
- **Bottleneck:** Gradient/Laplacian computations (use NumPy's optimized routines)

**Scaling:**
| N³ | Memory | Time/step | Total (100 steps) |
|----|--------|-----------|-------------------|
| 32³ | 1.5 MB | ~10 ms | ~1 sec |
| 64³ | 12 MB | ~50 ms | ~5 sec |
| 128³ | 96 MB | ~400 ms | ~40 sec |

---

## Next Steps: Rigorous Formulation

For a full RSVP theory, one would need to derive these equations from:

1. **Lattice action principle**
   - Define S[φ, v, S] on discrete spacetime
   - Specify geometric structure of lattice

2. **Entropy functional**
   - Identify S as geometric/information-theoretic entropy
   - Connect to lattice curvature or entanglement

3. **Euler-Lagrange equations with dissipation**
   - Derive field equations from variational principle
   - Include irreversible terms via thermodynamic potentials

4. **Coarse-graining from discrete to continuum**
   - Show these PDEs emerge as large-N limit
   - Identify coupling constants from microscopic theory

This would provide:
- Physical units (length, time, mass scales)
- Coupling constants from first principles
- Connection to underlying geometry (curvature, torsion)
- Predictions testable against observation
- Unification with standard field theories

The current formulation is a **numerical testbed**, not a fundamental theory. It demonstrates that entropy-driven dynamics can produce nontrivial structure formation without introducing ad-hoc forces.

---

## Code-to-Paper Correspondence

Every equation in this document corresponds **exactly** to a line in `rsvp_core.py`:

| Equation | Code |
|----------|------|
| ∂φ/∂t = D∇²φ − α‖∇S‖² | `phi_new = phi + dt * (D * lap_phi - ALPHA * grad_s_sq)` |
| v_target = −β∇φ | `v_target = -BETA * grad_phi` |
| v^(n+1) = (1−dt/τ)v^n + (dt/τ)v_target | `v_new = (1.0 - dt/TAU)*v + (dt/TAU)*v_target` |
| ∂S/∂t = η‖v‖ + γφ² | `s_new = s + dt * (ETA * flow_mag + GAMMA * phi**2)` |
| ∇²φ | `periodic_laplacian(phi, dx)` |
| ∇φ | `periodic_gradient(phi, dx, axis)` |

This ensures **complete reproducibility** and falsifiability.