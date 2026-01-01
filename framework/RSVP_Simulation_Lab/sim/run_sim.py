
import numpy as np
from pathlib import Path
from rsvp_core import step, initial_conditions
import json

CONFIG = {
    "N": 32,
    "T": 100,
    "dt": 0.05,
    "save_every": 2,
    "initial": "gaussian"
}

OUT = Path("sim/fields")
OUT.mkdir(parents=True, exist_ok=True)

def main():
    N = CONFIG["N"]
    dx = 1.0 / N

    with open(OUT / "config.json", "w") as f:
        cfg = dict(CONFIG)
        cfg["dx"] = dx
        json.dump(cfg, f, indent=2)

    phi, v, s = initial_conditions(N, CONFIG["initial"])

    np.savez_compressed(OUT / "t000.npz", phi=phi, v=v, s=s, t=0.0)

    save_count = 1
    for t in range(1, CONFIG["T"] + 1):
        s_prev = s.copy()
        phi, v, s = step(phi, v, s, CONFIG["dt"], dx)

        if t % CONFIG["save_every"] == 0:
            np.savez_compressed(
                OUT / f"t{save_count:03d}.npz",
                phi=phi, v=v, s=s, t=t * CONFIG["dt"]
            )
            save_count += 1

if __name__ == "__main__":
    main()
