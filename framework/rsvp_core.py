import numpy as np

# ========== Optional Extensions ==========
ENABLE_ENTROPY_DAMPING = False
ENABLE_VORTICITY_FEEDBACK = False
# =========================================

# ========== Parameters ==========
D = 0.1      # Diffusion coefficient
ALPHA = 0.5  # Entropy-gradient suppression
BETA = 0.8   # Vector alignment strength
TAU = 20.0   # Relaxation timescale (inverse of 1/τ = 0.05)
ETA = 0.1    # Entropy from flow (renamed from β)
GAMMA = 0.01 # Entropy from structure
# ================================


def periodic_gradient(f, dx, axis):
    """
    Compute gradient with periodic boundary conditions.
    Uses centered finite differences with np.roll for periodicity.
    
    Args:
        f: array to differentiate
        dx: grid spacing
        axis: axis along which to differentiate (0, 1, or 2)
    
    Returns:
        ∂f/∂x_i with periodic boundaries
    """
    # Centered difference: (f[i+1] - f[i-1]) / (2*dx)
    f_plus = np.roll(f, -1, axis=axis)
    f_minus = np.roll(f, 1, axis=axis)
    return (f_plus - f_minus) / (2.0 * dx)


def periodic_laplacian(f, dx):
    """
    Compute Laplacian ∇²f with periodic boundaries.
    
    ∇²f = ∂²f/∂x² + ∂²f/∂y² + ∂²f/∂z²
    
    Uses centered finite differences:
    ∂²f/∂x² ≈ (f[i+1] - 2f[i] + f[i-1]) / dx²
    """
    lap = np.zeros_like(f)
    
    for axis in range(3):
        f_plus = np.roll(f, -1, axis=axis)
        f_minus = np.roll(f, 1, axis=axis)
        lap += (f_plus - 2.0 * f + f_minus) / (dx * dx)
    
    return lap


def step(phi, v, s, dt=0.1, dx=1.0):
    """
    One RSVP evolution step with periodic boundaries.

    PDEs:
      ∂φ/∂t = D∇²φ − α|∇S|²
      ∂v/∂t = (1/τ)(v_target − v),  v_target = −β∇φ
      ∂S/∂t = η|v| + γφ²

    Args:
        phi : (N,N,N) scalar field
        v   : (3,N,N,N) vector field
        s   : (N,N,N) entropy field
        dt  : timestep
        dx  : spatial resolution

    Returns:
        phi_new, v_new, s_new
    """

    # ---------- gradients (periodic) ----------
    grad_phi = np.array([
        periodic_gradient(phi, dx, axis=0),
        periodic_gradient(phi, dx, axis=1),
        periodic_gradient(phi, dx, axis=2)
    ])
    
    grad_s = np.array([
        periodic_gradient(s, dx, axis=0),
        periodic_gradient(s, dx, axis=1),
        periodic_gradient(s, dx, axis=2)
    ])

    # ---------- Laplacian (periodic) ----------
    lap_phi = periodic_laplacian(phi, dx)

    # ---------- scalar field ----------
    # ∂φ/∂t = D∇²φ − α|∇S|²
    grad_s_sq = (
        grad_s[0]**2 +
        grad_s[1]**2 +
        grad_s[2]**2
    )

    phi_new = phi + dt * (
        D * lap_phi         # diffusion / smoothing
        - ALPHA * grad_s_sq # entropy-gradient suppression
    )

    # ---------- vector field ----------
    # ∂v/∂t = (1/τ)(v_target − v),  v_target = −β∇φ
    v_target = -BETA * grad_phi

    v_new = (
        (1.0 - dt/TAU) * v +      # memory / inertia
        (dt/TAU) * v_target        # alignment
    )

    # ---------- entropy field ----------
    # ∂S/∂t = η|v| + γφ²
    flow_mag = np.sqrt(
        v_new[0]**2 +
        v_new[1]**2 +
        v_new[2]**2
    )

    s_new = s + dt * (
        ETA * flow_mag +    # dissipation from flow
        GAMMA * phi**2      # structure cost
    )

    # ========== OPTIONAL EXTENSION A: Entropy damping ==========
    if ENABLE_ENTROPY_DAMPING:
        # Entropy resists coherent flow (prevents blow-ups)
        v_new /= (1.0 + 0.3 * s_new)
    # ===========================================================

    # ========== OPTIONAL EXTENSION B: Vorticity feedback ==========
    if ENABLE_VORTICITY_FEEDBACK:
        # Weak torsion / lamphrodyne-style circulation (no forces)
        curl_v = np.array([
            periodic_gradient(v_new[2], dx, axis=1) - periodic_gradient(v_new[1], dx, axis=2),
            periodic_gradient(v_new[0], dx, axis=2) - periodic_gradient(v_new[2], dx, axis=0),
            periodic_gradient(v_new[1], dx, axis=0) - periodic_gradient(v_new[0], dx, axis=1),
        ])
        v_new += dt * 0.02 * curl_v
    # ==============================================================

    # ---------- bounds (numerical hygiene) ----------
    phi_new = np.clip(phi_new, 0.0, 2.0)
    s_new   = np.clip(s_new,   0.0, 5.0)

    return phi_new, v_new, s_new


def initial_conditions(N, config="gaussian"):
    """
    Generate initial RSVP field configurations.
    
    Args:
        N: lattice size
        config: "gaussian", "dipole", "vortex", or "random"
    """
    x = np.linspace(-1, 1, N)
    X, Y, Z = np.meshgrid(x, x, x, indexing="ij")

    # Explicit zero initialization (safe for all branches)
    phi = np.zeros((N, N, N))
    v   = np.zeros((3, N, N, N))
    s   = np.zeros((N, N, N))

    if config == "gaussian":
        phi = np.exp(-(X**2 + Y**2 + Z**2))
        s   = 0.1 * np.ones_like(phi)

    elif config == "dipole":
        r1 = np.sqrt((X+0.3)**2 + Y**2 + Z**2)
        r2 = np.sqrt((X-0.3)**2 + Y**2 + Z**2)
        phi = np.exp(-r1**2) + 0.5 * np.exp(-r2**2)
        s   = 0.1 * phi

    elif config == "vortex":
        r = np.sqrt(X**2 + Y**2)
        phi = np.exp(-r**2) * np.exp(-Z**2)
        v[0] = -Y * np.exp(-r**2)
        v[1] =  X * np.exp(-r**2)
        s    = 0.1 * np.ones_like(phi)

    elif config == "random":
        phi = np.random.rand(N, N, N)
        v   = 0.1 * np.random.randn(3, N, N, N)
        s   = 0.1 * np.random.rand(N, N, N)

    return phi, v, s


# ========== Diagnostic Utilities ==========

def compute_diagnostics(phi, v, s, dx=1.0):
    """
    Compute conserved quantities and production rates.
    
    Returns:
        dict with:
            - total_entropy: ∫S dV
            - entropy_production: rate dS/dt
            - kinetic_energy: (1/2)∫|v|² dV
            - potential_energy: (1/2)∫|∇φ|² dV
    """
    flow_mag = np.sqrt(v[0]**2 + v[1]**2 + v[2]**2)
    
    grad_phi = np.array([
        periodic_gradient(phi, dx, axis=0),
        periodic_gradient(phi, dx, axis=1),
        periodic_gradient(phi, dx, axis=2)
    ])
    grad_phi_sq = grad_phi[0]**2 + grad_phi[1]**2 + grad_phi[2]**2
    
    return {
        'total_entropy': np.sum(s) * dx**3,
        'entropy_production': np.sum(ETA * flow_mag + GAMMA * phi**2) * dx**3,
        'kinetic_energy': 0.5 * np.sum(flow_mag**2) * dx**3,
        'potential_energy': 0.5 * np.sum(grad_phi_sq) * dx**3,
    }


def check_stability(phi, v, s, dt, dx):
    """
    Check diffusion stability condition.
    
    For explicit Euler diffusion in 3D:
      dt ≲ dx² / (6D)
    
    Returns:
        (is_stable, max_velocity, suggested_dt)
    """
    max_v = np.sqrt(np.max(v[0]**2 + v[1]**2 + v[2]**2))
    
    # Diffusion stability: dt < dx²/(6D)
    diffusion_dt = dx * dx / (6.0 * D)
    
    # Relaxation stability: dt < τ
    relaxation_dt = TAU
    
    # Most restrictive
    suggested_dt = min(diffusion_dt, relaxation_dt)
    
    is_stable = dt <= suggested_dt
    
    return is_stable, max_v, suggested_dt