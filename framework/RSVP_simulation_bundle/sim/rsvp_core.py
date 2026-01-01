
"""
RSVP Core: Scalar–Vector–Entropy field evolution
"""
import numpy as np

def step(phi, v, s, dt=0.1, dx=1.0):
    grad_phi = np.gradient(phi, dx)
    grad_s   = np.gradient(s, dx)

    lap_phi = (
        np.gradient(grad_phi[0], dx, axis=0) +
        np.gradient(grad_phi[1], dx, axis=1) +
        np.gradient(grad_phi[2], dx, axis=2)
    )

    grad_s_sq = grad_s[0]**2 + grad_s[1]**2 + grad_s[2]**2

    phi_new = phi + dt * (0.1 * lap_phi - 0.5 * grad_s_sq)

    v_target = np.stack([-0.8 * g for g in grad_phi], axis=0)
    v_new = 0.95 * v + 0.05 * v_target

    flow_mag = np.sqrt(v_new[0]**2 + v_new[1]**2 + v_new[2]**2)
    s_new = s + dt * (0.1 * flow_mag + 0.01 * phi**2)

    phi_new = np.clip(phi_new, 0.0, 2.0)
    s_new   = np.clip(s_new,   0.0, 5.0)

    return phi_new, v_new, s_new


def initial_conditions(N, config="gaussian"):
    x = np.linspace(-1, 1, N)
    X, Y, Z = np.meshgrid(x, x, x, indexing="ij")

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
