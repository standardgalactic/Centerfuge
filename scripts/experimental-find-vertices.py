import bpy
import bmesh
import mathutils

def extract_outline_points(obj, use_all_vertices=True, resolution=100):
    """
    Convert the given object (assumed to be a text or curve object)
    into a mesh, then extract the outline vertices.
    
    Parameters:
      obj: The object to convert.
      use_all_vertices: If True, use all mesh vertices; else, try to sample along the edges.
      resolution: (Optional) How many points to sample along each edge if not using all vertices.
    
    Returns:
      A list of 3D points in world coordinates.
    """
    # Duplicate the object so we don’t lose the original.
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.duplicate()
    dup = bpy.context.active_object
    
    # Convert the duplicate to a mesh.
    bpy.ops.object.convert(target='MESH')
    
    # Get a bmesh representation.
    bm = bmesh.new()
    bm.from_mesh(dup.data)
    
    # Option 1: Use all vertices.
    points = [dup.matrix_world @ v.co for v in bm.verts]
    
    # (Option 2: If you want to sample along the edges uniformly, you could iterate over each edge,
    #  subdivide it (or use edge.calc_length()) and sample a number of points along it.
    #  This requires more work and is left as an exercise.)
    
    bm.free()
    
    # Delete the duplicate mesh object.
    bpy.data.objects.remove(dup, do_unlink=True)
    
    return points

def create_markers_from_points(points, collection_name="OutlineMarkers"):
    """
    Create empty objects (markers) at each point for visualization.
    """
    # Create or get a collection for markers.
    if collection_name in bpy.data.collections:
        coll = bpy.data.collections[collection_name]
        # Remove existing objects.
        for obj in list(coll.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
    else:
        coll = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(coll)
    
    markers = []
    for i, co in enumerate(points):
        marker = bpy.data.objects.new(f"Marker_{i:03d}", None)
        marker.location = co
        marker.empty_display_size = 0.1
        marker.empty_display_type = 'SPHERE'
        coll.objects.link(marker)
        markers.append(marker)
    return markers

# -----------------------
# MAIN EXECUTION
# -----------------------

# Make sure you have a text (or curve) object selected in 2D view.
active_obj = bpy.context.active_object
if active_obj is None:
    raise Exception("Please select a text or curve object.")

# Optionally, if your object is a Text object, you might want to convert it to a curve first:
if active_obj.type == 'FONT':
    bpy.ops.object.convert(target='CURVE')
    active_obj = bpy.context.active_object

# Extract outline points (in 2D, these will lie roughly on the same plane)
outline_points = extract_outline_points(active_obj)

# Create markers for visualization
markers = create_markers_from_points(outline_points)

print(f"Extracted {len(outline_points)} outline points from the object.")
