"""
Plot RSVP simulation diagnostics
Shows: entropy evolution, energy components, entropy production
"""
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def plot_diagnostics():
    """Generate diagnostic plots from simulation data"""
    
    # Load diagnostics
    data = np.load("sim/fields/diagnostics.npz")
    
    time = data['time']
    S = data['total_entropy']
    dS_dt = data['entropy_production']
    KE = data['kinetic_energy']
    PE = data['potential_energy']
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('RSVP Field Evolution Diagnostics', fontsize=16, fontweight='bold')
    
    # 1. Total Entropy
    ax = axes[0, 0]
    ax.plot(time, S, 'b-', linewidth=2)
    ax.set_xlabel('Time')
    ax.set_ylabel('Total Entropy ∫S dV')
    ax.set_title('Entropy Evolution (should be monotonic)')
    ax.grid(True, alpha=0.3)
    
    # Check monotonicity
    violations = np.sum(np.diff(S) < 0)
    if violations > 0:
        ax.text(0.95, 0.05, f'⚠️ {violations} decreases', 
               transform=ax.transAxes, ha='right', va='bottom',
               bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))
    else:
        ax.text(0.95, 0.05, '✓ Monotonic', 
               transform=ax.transAxes, ha='right', va='bottom',
               bbox=dict(boxstyle='round', facecolor='green', alpha=0.3))
    
    # 2. Entropy Production Rate
    ax = axes[0, 1]
    ax.plot(time, dS_dt, 'r-', linewidth=2)
    ax.set_xlabel('Time')
    ax.set_ylabel('Entropy Production dS/dt')
    ax.set_title('Dissipation Rate (should be ≥ 0)')
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0, color='k', linestyle='--', alpha=0.3)
    
    # 3. Energy Components
    ax = axes[1, 0]
    ax.plot(time, KE, 'b-', linewidth=2, label='Kinetic: (1/2)∫|v|² dV')
    ax.plot(time, PE, 'r-', linewidth=2, label='Potential: (1/2)∫|∇φ|² dV')
    ax.plot(time, KE + PE, 'k--', linewidth=2, label='Total')
    ax.set_xlabel('Time')
    ax.set_ylabel('Energy')
    ax.set_title('Energy Components')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 4. Phase Space: Energy vs Entropy
    ax = axes[1, 1]
    total_E = KE + PE
    ax.plot(S, total_E, 'g-', linewidth=2, alpha=0.7)
    ax.scatter(S[0], total_E[0], c='blue', s=100, marker='o', label='Start', zorder=10)
    ax.scatter(S[-1], total_E[-1], c='red', s=100, marker='s', label='End', zorder=10)
    ax.set_xlabel('Total Entropy')
    ax.set_ylabel('Total Energy')
    ax.set_title('Phase Space Trajectory')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save
    out_path = Path("out/diagnostics.png")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    print(f"Saved diagnostic plot to {out_path}")
    
    # Summary statistics
    print("\n" + "="*60)
    print("Summary Statistics")
    print("="*60)
    print(f"Initial entropy:  {S[0]:.6f}")
    print(f"Final entropy:    {S[-1]:.6f}")
    print(f"ΔS:               {S[-1] - S[0]:.6f} ({100*(S[-1]/S[0]-1):.1f}%)")
    print(f"Mean dS/dt:       {dS_dt.mean():.6f}")
    print(f"Max dS/dt:        {dS_dt.max():.6f}")
    print(f"\nInitial energy:   {total_E[0]:.6f}")
    print(f"Final energy:     {total_E[-1]:.6f}")
    print(f"ΔE:               {total_E[-1] - total_E[0]:.6f} ({100*(total_E[-1]/total_E[0]-1):.1f}%)")
    print("="*60)

if __name__ == "__main__":
    plot_diagnostics()
    plt.show()