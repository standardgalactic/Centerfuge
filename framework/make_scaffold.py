# Create the RSVP simulation + Blender inspection zip structure

import zipfile
from pathlib import Path

root = Path("rsvp_sim_package")
(root / "sim").mkdir(parents=True, exist_ok=True)
(root / "sim/fields").mkdir(parents=True, exist_ok=True)
(root / "blender").mkdir(parents=True, exist_ok=True)
(root / "out/renders").mkdir(parents=True, exist_ok=True)
(root / "out/meshes").mkdir(parents=True, exist_ok=True)

# --- sim/rsvp_core.py ---
(root / "sim/rsvp_core.py").write_text("""
import numpy as np

def step(phi, v, s, dt=0.1):
    grad_s = np.gradient(s)
    phi = phi - dt * (grad_s[0]**2 + grad_s[1]**2 + grad_s[2]**2)

    grad_phi = np.gradient(phi)
    v = np.stack([-g for g in grad_phi], axis=0)

    s = s + dt * np.sqrt(sum(vi**2 for vi in v))
    return phi, v, s
""".strip())

# --- sim/run_sim.py ---
(root / "sim/run_sim.py").write_text("""
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
""".strip())

# --- blender/common.py ---
(root / "blender/common.py").write_text("""
import bpy

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 64

def camera():
    cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Cam"))
    bpy.context.scene.collection.objects.link(cam)
    cam.location = (6,-6,4)
    cam.rotation_euler = (1.1, 0, 0.8)
    bpy.context.scene.camera = cam

def lights():
    light = bpy.data.lights.new("Key", type='AREA')
    light.energy = 2000
    obj = bpy.data.objects.new("Key", light)
    obj.location = (4,-4,6)
    bpy.context.scene.collection.objects.link(obj)
""".strip())

# --- blender/render_field.py ---
(root / "blender/render_field.py").write_text("""
import bpy
import numpy as np
from pathlib import Path
import sys, os

sys.path.append(os.path.dirname(__file__))
import common

FIELD_FILE = "sim/fields/t020.npz"
THRESH = 0.1
SCALE = 0.15

def main():
    common.reset()
    common.camera()
    common.lights()

    data = np.load(Path(FIELD_FILE))
    phi = data["phi"]

    N = phi.shape[0]
    step = 1.0 / N

    mat = bpy.data.materials.new("Phi")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 2.0

    for i in range(N):
        for j in range(N):
            for k in range(N):
                val = phi[i,j,k]
                if val < THRESH:
                    continue
                bpy.ops.mesh.primitive_uv_sphere_add(
                    radius=SCALE * val,
                    location=((i-N/2)*step, (j-N/2)*step, (k-N/2)*step)
                )
                bpy.context.active_object.data.materials.append(mat)

    bpy.context.scene.render.filepath = "out/renders/frame.png"
    bpy.ops.render.render(write_still=True)

if __name__ == "__main__":
    main()
""".strip())

# Zip it
zip_path = Path("RSVP_Simulation_Blender_Package.zip")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for file in root.rglob("*"):
        z.write(file, file.relative_to(root))

zip_path