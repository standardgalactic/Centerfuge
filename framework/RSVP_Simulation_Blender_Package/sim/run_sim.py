import numpy as np
from pathlib import Path
from rsvp_core import step

OUT = Path("sim/fields")
OUT.mkdir(parents=True, exist_ok=True)

N = 24
T = 30
dt = 0.1

x = np.linspace(-1,1,N)
X,Y,Z = np.meshgrid(x,x,x, indexing="ij")

phi = np.exp(-(X**2 + Y**2 + Z**2))
v = np.zeros((3,N,N,N))
s = np.zeros((N,N,N))

for t in range(T):
    phi, v, s = step(phi, v, s, dt)
    np.savez(OUT / f"t{t:03d}.npz", phi=phi, v=v, s=s)