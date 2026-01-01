
import numpy as np
from pathlib import Path
from rsvp_core import step, initial_conditions

OUT = Path("sim/fields")
OUT.mkdir(parents=True, exist_ok=True)

N = 24
T = 40
dt = 0.1

phi, v, s = initial_conditions(N, config="gaussian")

for t in range(T):
    phi, v, s = step(phi, v, s, dt=dt)
    np.savez(OUT / f"t{t:03d}.npz", phi=phi, v=v, s=s)
