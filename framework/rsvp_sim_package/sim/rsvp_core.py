import numpy as np

def step(phi, v, s, dt=0.1):
    grad_s = np.gradient(s)
    phi = phi - dt * (grad_s[0]**2 + grad_s[1]**2 + grad_s[2]**2)

    grad_phi = np.gradient(phi)
    v = np.stack([-g for g in grad_phi], axis=0)

    s = s + dt * np.sqrt(sum(vi**2 for vi in v))
    return phi, v, s