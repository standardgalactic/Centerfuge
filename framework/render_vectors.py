"""
Vector Field Visualization
Cylinders aligned to v(x), or streamlines
"""
import bpy
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
import sys, os

sys.path.append(os.path.dirname(__file__))
import common

# ========== Parameters ==========
FIELD_FILE = "sim/fields/t020.npz"
SUBSAMPLE = 4      # show every Nth vector
V_SCALE = 2.0      # arrow length multiplier
V_THRESH = 0.01    # minimum |v| to show
ARROW_RADIUS = 0.02
# ================================

def create_arrow(start, direction, length, radius=0.02):
    """Create cylinder arrow from start point along direction"""
    if length < 1e-6:
        return None
    
    # Create cylinder
    bpy.ops.mesh.primitive_cylinder_add(
        radius=radius,
        depth=length,
        location=(0, 0, 0)
    )
    arrow = bpy.context.active_object
    
    # Rotation to align with direction
    direction = Vector(direction).normalized()
    z_axis = Vector((0, 0, 1))
    
    if (direction - z_axis).length < 0.001:
        rot_mat = Matrix.Identity(3)
    elif (direction + z_axis).length < 0.001:
        rot_mat = Matrix.Rotation(np.pi, 3, 'X')
    else:
        axis = z_axis.cross(direction)
        angle = z_axis.angle(direction)
        rot_mat = Matrix.Rotation(angle, 3, axis)
    
    # Position at start + half-length along direction
    center = Vector(start) + direction * (length / 2)
    arrow.location = center
    arrow.rotation_euler = rot_mat.to_euler()
    
    return arrow


def main():
    common.reset()
    common.camera()
    common.lights()
    
    # Load field
    data = np.load(Path(FIELD_FILE))
    phi = data["phi"]
    v = data["v"]
    s = data["s"]
    
    N = phi.shape[0]
    step = 2.0 / N
    
    # Material for vectors
    mat = bpy.data.materials.new("VectorMat")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.2, 0.7, 1.0, 1.0)
    mat.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 0.8
    
    count = 0
    
    for i in range(0, N, SUBSAMPLE):
        for j in range(0, N, SUBSAMPLE):
            for k in range(0, N, SUBSAMPLE):
                # Get vector
                vx, vy, vz = v[:, i, j, k]
                vmag = np.sqrt(vx**2 + vy**2 + vz**2)
                
                if vmag < V_THRESH:
                    continue
                
                # Position
                x = (i - N/2) * step
                y = (j - N/2) * step
                z = (k - N/2) * step
                
                # Create arrow
                arrow = create_arrow(
                    (x, y, z),
                    (vx, vy, vz),
                    vmag * V_SCALE,
                    ARROW_RADIUS
                )
                
                if arrow:
                    arrow.data.materials.append(mat)
                    count += 1
    
    print(f"Created {count} vector arrows")
    
    # Render
    bpy.context.scene.render.filepath = "out/renders/vectors.png"
    bpy.ops.render.render(write_still=True)
    print(f"Rendered to {bpy.context.scene.render.filepath}")

if __name__ == "__main__":
    main()