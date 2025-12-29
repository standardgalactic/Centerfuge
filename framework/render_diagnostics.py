"""
Quantitative Overlays
Entropy histograms, field statistics rendered as meshes
"""
import bpy
import numpy as np
from pathlib import Path
import sys, os

sys.path.append(os.path.dirname(__file__))
import common

# ========== Parameters ==========
FIELD_FILE = "sim/fields/t020.npz"
# ================================

def create_histogram_mesh(values, bins=20, position=(0, 0, 0), scale=1.0):
    """Create 3D bar chart histogram"""
    hist, edges = np.histogram(values, bins=bins)
    hist = hist / hist.max()  # normalize
    
    collection = bpy.data.collections.new("Histogram")
    bpy.context.scene.collection.children.link(collection)
    
    mat = bpy.data.materials.new("HistMat")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (1.0, 0.5, 0.2, 1.0)
    
    width = 0.8 * scale / bins
    
    for i, h in enumerate(hist):
        if h < 0.01:
            continue
        
        x = position[0] + (i - bins/2) * scale / bins
        
        bpy.ops.mesh.primitive_cube_add(
            size=1.0,
            location=(x, position[1], position[2] + h * scale / 2)
        )
        obj = bpy.context.active_object
        obj.scale = (width, width, h * scale)
        obj.data.materials.append(mat)
        
        # Move to collection
        for coll in obj.users_collection:
            coll.objects.unlink(obj)
        collection.objects.link(obj)
    
    return collection


def create_text_overlay(text, location=(0, 0, 0)):
    """Create 3D text object"""
    curve = bpy.data.curves.new(type="FONT", name="Text")
    curve.body = text
    curve.size = 0.2
    
    obj = bpy.data.objects.new("TextObj", curve)
    obj.location = location
    bpy.context.collection.objects.link(obj)
    
    mat = bpy.data.materials.new("TextMat")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 3.0
    obj.data.materials.append(mat)
    
    return obj


def create_stats_panel(phi, v, s):
    """Create floating panel with field statistics"""
    stats_text = (
        f"φ: [{phi.min():.3f}, {phi.max():.3f}]\n"
        f"|v|: {np.sqrt(np.sum(v**2, axis=0)).max():.3f}\n"
        f"S: [{s.min():.3f}, {s.max():.3f}]\n"
        f"⟨S⟩: {s.mean():.3f}"
    )
    
    # Background plane
    bpy.ops.mesh.primitive_plane_add(
        size=2.0,
        location=(3, 0, 2)
    )
    plane = bpy.context.active_object
    plane.scale = (1.5, 1.0, 1.0)
    
    mat = bpy.data.materials.new("PanelMat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.1, 0.1, 0.1, 1.0)
    nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.8
    mat.blend_method = 'BLEND'
    plane.data.materials.append(mat)
    
    # Text
    for i, line in enumerate(stats_text.split('\n')):
        create_text_overlay(line, (2.5, 0, 2.5 - i*0.3))


def main():
    common.reset()
    common.camera()
    common.lights()
    
    # Load field
    data = np.load(Path(FIELD_FILE))
    phi = data["phi"]
    v = data["v"]
    s = data["s"]
    
    print(f"Creating diagnostic visualizations...")
    
    # Entropy histogram
    create_histogram_mesh(
        s.flatten(),
        bins=30,
        position=(-2, -3, 0),
        scale=2.0
    )
    
    # Label
    create_text_overlay("Entropy Distribution", (-2, -3, 2.5))
    
    # Stats panel
    create_stats_panel(phi, v, s)
    
    # Also show field
    N = phi.shape[0]
    step = 2.0 / N
    thresh = 0.15
    scale = 0.15
    
    mat = bpy.data.materials.new("Phi")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 1.5
    
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
    
    # Render
    bpy.context.scene.render.filepath = "out/renders/diagnostics.png"
    bpy.ops.render.render(write_still=True)
    print(f"Rendered to {bpy.context.scene.render.filepath}")

if __name__ == "__main__":
    main()