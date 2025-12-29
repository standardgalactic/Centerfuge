"""
Time Evolution Animation
One Blender run renders all t000–tNNN
"""
import bpy
import numpy as np
from pathlib import Path
import sys, os

sys.path.append(os.path.dirname(__file__))
import common

# ========== Parameters ==========
FIELD_DIR = Path("sim/fields")
OUT_DIR = Path("out/renders/anim")
THRESH = 0.15
SCALE = 0.15
START_FRAME = 0
END_FRAME = 50  # or None for all
# ================================

def load_timestep(filepath):
    """Load a single timestep"""
    data = np.load(filepath)
    return data["phi"], data["v"], data["s"]


def update_spheres(phi, thresh, scale):
    """Update sphere positions and sizes for current timestep"""
    # Clear existing spheres
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    # Recreate camera and lights
    common.camera()
    common.lights()
    
    N = phi.shape[0]
    step = 2.0 / N
    
    mat = bpy.data.materials.new("Phi")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 2.0
    
    for i in range(N):
        for j in range(N):
            for k in range(N):
                val = phi[i, j, k]
                if val < thresh:
                    continue
                
                bpy.ops.mesh.primitive_uv_sphere_add(
                    radius=scale * val,
                    location=(
                        (i - N/2) * step,
                        (j - N/2) * step,
                        (k - N/2) * step
                    )
                )
                obj = bpy.context.active_object
                obj.data.materials.append(mat)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    common.reset()
    
    # Find all timestep files
    files = sorted(FIELD_DIR.glob("t*.npz"))
    
    if END_FRAME is not None:
        files = files[START_FRAME:END_FRAME+1]
    else:
        files = files[START_FRAME:]
    
    print(f"Rendering {len(files)} frames...")
    
    for idx, filepath in enumerate(files):
        print(f"Frame {idx:03d}: {filepath.name}")
        
        # Load field
        phi, v, s = load_timestep(filepath)
        
        # Update geometry
        update_spheres(phi, THRESH, SCALE)
        
        # Render
        frame_path = OUT_DIR / f"frame_{idx:04d}.png"
        bpy.context.scene.render.filepath = str(frame_path)
        bpy.ops.render.render(write_still=True)
    
    print(f"\nRendered {len(files)} frames to {OUT_DIR}")
    print(f"Create video: ffmpeg -framerate 30 -i {OUT_DIR}/frame_%04d.png -c:v libx264 -pix_fmt yuv420p out/evolution.mp4")

if __name__ == "__main__":
    main()