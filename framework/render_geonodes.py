"""
Geometry Nodes Backend
Single mesh + vertex attributes = 10-100x faster than instancing
"""
import bpy
import numpy as np
from pathlib import Path
import sys, os

sys.path.append(os.path.dirname(__file__))
import common

# ========== Parameters ==========
FIELD_FILE = "sim/fields/t020.npz"
THRESH = 0.15
RADIUS_SCALE = 0.3
# ================================

def create_geonodes_visualizer():
    """Create geometry nodes setup for field visualization"""
    # Create empty mesh
    mesh = bpy.data.meshes.new("FieldMesh")
    obj = bpy.data.objects.new("FieldViz", mesh)
    bpy.context.collection.objects.link(obj)
    
    # Add geometry nodes modifier
    mod = obj.modifiers.new("GeoNodes", 'NODES')
    node_tree = bpy.data.node_groups.new("FieldNodes", 'GeometryNodeTree')
    mod.node_group = node_tree
    
    # Create nodes
    nodes = node_tree.nodes
    links = node_tree.links
    
    # Input/Output
    input_node = nodes.new('NodeGroupInput')
    output_node = nodes.new('NodeGroupOutput')
    input_node.location = (-400, 0)
    output_node.location = (400, 0)
    
    # Instance on points
    instance_node = nodes.new('GeometryNodeInstanceOnPoints')
    instance_node.location = (0, 0)
    
    # Sphere to instance
    sphere_node = nodes.new('GeometryNodeMeshUVSphere')
    sphere_node.location = (-200, -200)
    
    # Links
    links.new(input_node.outputs[0], instance_node.inputs[0])
    links.new(sphere_node.outputs[0], instance_node.inputs[2])
    links.new(instance_node.outputs[0], output_node.inputs[0])
    
    # Create sockets
    node_tree.interface.new_socket("Geometry", in_out='INPUT', socket_type='NodeSocketGeometry')
    node_tree.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    
    return obj


def populate_field_points(obj, phi, v, s, thresh, scale):
    """Convert field data to vertex cloud with attributes"""
    N = phi.shape[0]
    step = 2.0 / N
    
    # Collect valid points
    points = []
    radii = []
    colors = []
    entropies = []
    
    for i in range(N):
        for j in range(N):
            for k in range(N):
                val = phi[i, j, k]
                if val < thresh:
                    continue
                
                x = (i - N/2) * step
                y = (j - N/2) * step
                z = (k - N/2) * step
                
                points.append([x, y, z])
                radii.append(scale * val)
                
                # Color by entropy
                s_val = s[i, j, k]
                colors.append([s_val, 0.5, 1.0 - s_val, 1.0])
                entropies.append(s_val)
    
    if not points:
        return
    
    # Create mesh from points
    mesh = obj.data
    mesh.clear_geometry()
    
    mesh.vertices.add(len(points))
    mesh.vertices.foreach_set("co", np.array(points).flatten())
    
    # Add custom attributes
    radius_attr = mesh.attributes.new("radius", 'FLOAT', 'POINT')
    radius_attr.data.foreach_set("value", radii)
    
    entropy_attr = mesh.attributes.new("entropy", 'FLOAT', 'POINT')
    entropy_attr.data.foreach_set("value", entropies)
    
    # Color attribute
    if not mesh.color_attributes:
        mesh.color_attributes.new("Color", 'FLOAT_COLOR', 'POINT')
    color_attr = mesh.color_attributes.active_color
    color_attr.data.foreach_set("color", np.array(colors).flatten())
    
    mesh.update()


def main():
    common.reset()
    common.camera()
    common.lights()
    
    # Load field
    data = np.load(Path(FIELD_FILE))
    phi = data["phi"]
    v = data["v"]
    s = data["s"]
    
    print(f"Loaded: φ∈[{phi.min():.3f},{phi.max():.3f}], "
          f"S∈[{s.min():.3f},{s.max():.3f}]")
    
    # Create visualizer
    obj = create_geonodes_visualizer()
    
    # Populate
    populate_field_points(obj, phi, v, s, THRESH, RADIUS_SCALE)
    
    # Material
    mat = bpy.data.materials.new("FieldMat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 1.5
    
    # Use vertex color
    vcol = nodes.new('ShaderNodeVertexColor')
    vcol.layer_name = "Color"
    mat.node_tree.links.new(
        vcol.outputs[0],
        nodes["Principled BSDF"].inputs[0]
    )
    
    obj.data.materials.append(mat)
    
    # Render
    bpy.context.scene.render.filepath = "out/renders/geonodes.png"
    bpy.ops.render.render(write_still=True)
    print(f"Rendered to {bpy.context.scene.render.filepath}")

if __name__ == "__main__":
    main()