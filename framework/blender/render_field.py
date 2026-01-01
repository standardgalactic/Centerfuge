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