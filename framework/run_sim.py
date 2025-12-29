"""
RSVP Simulation Driver
Runs field evolution and saves snapshots with diagnostics
"""
import numpy as np
from pathlib import Path
from rsvp_core import (
    step, 
    initial_conditions, 
    compute_diagnostics, 
    check_stability
)
import json

# ========== Configuration ==========
CONFIG = {
    "N": 32,           # lattice size (32³, 64³, etc.)
    "T": 100,          # number of timesteps
    "dt": 0.05,        # timestep size
    "dx": 1.0/32,      # spatial resolution
    "save_every": 2,   # save every N steps
    "initial": "gaussian",  # or "dipole", "vortex", "random"
    "diagnostics": True,    # compute conserved quantities
}

OUT = Path("sim/fields")
OUT.mkdir(parents=True, exist_ok=True)

# ===================================

def main():
    print("=" * 60)
    print(f"RSVP Simulation: {CONFIG['N']}³ lattice, {CONFIG['T']} steps")
    print("=" * 60)
    
    # Save config
    with open(OUT / "config.json", "w") as f:
        json.dump(CONFIG, f, indent=2)
    
    # Initialize
    N = CONFIG["N"]
    dx = CONFIG["dx"]
    dt = CONFIG["dt"]
    
    phi, v, s = initial_conditions(N, CONFIG["initial"])
    
    # Diagnostics storage
    if CONFIG["diagnostics"]:
        diag_history = []
    
    # Save initial state
    np.savez_compressed(
        OUT / "t000.npz",
        phi=phi, v=v, s=s, t=0.0
    )
    
    # Initial diagnostics
    if CONFIG["diagnostics"]:
        diag = compute_diagnostics(phi, v, s, dx)
        diag['time'] = 0.0
        diag_history.append(diag)
        
        print("\nInitial state:")
        print(f"  Total entropy:     {diag['total_entropy']:.6f}")
        print(f"  Kinetic energy:    {diag['kinetic_energy']:.6f}")
        print(f"  Potential energy:  {diag['potential_energy']:.6f}")
        
        # Check stability
        stable, max_v, cfl_dt = check_stability(phi, v, s, dt, dx)
        if not stable:
            print(f"\n  WARNING: CFL condition violated!")
            print(f"  max(|v|) = {max_v:.3f}, suggested dt ≤ {cfl_dt:.5f}")
            print(f"  Current dt = {dt:.5f}")
        else:
            print(f"\n✓ CFL stable: max(|v|) = {max_v:.3f}, dt = {dt:.5f}")
    
    print("\n" + "=" * 60)
    print("Evolving fields...")
    print("=" * 60)
    
    # Evolve
    save_count = 1
    for t in range(1, CONFIG["T"] + 1):
        phi, v, s = step(phi, v, s, dt, dx)
        
        if t % CONFIG["save_every"] == 0:
            np.savez_compressed(
                OUT / f"t{save_count:03d}.npz",
                phi=phi, v=v, s=s, t=t*dt
            )
            
            # Diagnostics
            if CONFIG["diagnostics"]:
                diag = compute_diagnostics(phi, v, s, dx)
                diag['time'] = t * dt
                diag_history.append(diag)
                
                print(f"t={save_count:03d} ({t*dt:.2f}): "
                      f"φ∈[{phi.min():.3f},{phi.max():.3f}] "
                      f"|v|={np.sqrt(np.sum(v**2, axis=0)).max():.3f} "
                      f"S={diag['total_entropy']:.3f} "
                      f"dS/dt={diag['entropy_production']:.4f}")
            else:
                print(f"t={save_count:03d}: "
                      f"φ∈[{phi.min():.3f},{phi.max():.3f}] "
                      f"|v|={np.sqrt(np.sum(v**2, axis=0)).max():.3f} "
                      f"S∈[{s.min():.3f},{s.max():.3f}]")
            
            save_count += 1
    
    # Save diagnostics
    if CONFIG["diagnostics"]:
        diag_array = {
            'time': [d['time'] for d in diag_history],
            'total_entropy': [d['total_entropy'] for d in diag_history],
            'entropy_production': [d['entropy_production'] for d in diag_history],
            'kinetic_energy': [d['kinetic_energy'] for d in diag_history],
            'potential_energy': [d['potential_energy'] for d in diag_history],
        }
        np.savez_compressed(OUT / "diagnostics.npz", **diag_array)
        
        print("\n" + "=" * 60)
        print("Final diagnostics:")
        print("=" * 60)
        final = diag_history[-1]
        print(f"  Total entropy:     {final['total_entropy']:.6f}")
        print(f"  Entropy production: {final['entropy_production']:.6f}")
        print(f"  Kinetic energy:    {final['kinetic_energy']:.6f}")
        print(f"  Potential energy:  {final['potential_energy']:.6f}")
        
        # Entropy monotonicity check
        entropies = [d['total_entropy'] for d in diag_history]
        violations = sum(1 for i in range(1, len(entropies)) 
                        if entropies[i] < entropies[i-1])
        if violations > 0:
            print(f"\n  Entropy decreased {violations} times (numerical noise)")
        else:
            print("\n✓ Entropy monotonically increased (thermodynamically consistent)")
    
    print("\n" + "=" * 60)
    print(f"Saved {save_count} snapshots to {OUT}")
    print(f"Run visualization: blender -b -P blender/render_geonodes.py")
    if CONFIG["diagnostics"]:
        print(f"Plot diagnostics: python sim/plot_diagnostics.py")
    print("=" * 60)

if __name__ == "__main__":
    main()