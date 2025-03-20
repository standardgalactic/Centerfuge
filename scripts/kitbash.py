import bpy
import math
import mathutils

# -----------------------
# UTILITY FUNCTIONS
# -----------------------

def sample_polygon(vertices, n_samples):
    """
    Given a list of 2D vertices (ordered, forming a closed polygon),
    return n_samples points uniformly sampled along its perimeter.
    """
    # Compute edge lengths and total perimeter.
    distances = []
    total = 0
    N = len(vertices)
    for i in range(N):
        v1 = vertices[i]
        v2 = vertices[(i+1) % N]
        d = math.hypot(v2[0]-v1[0], v2[1]-v1[1])
        distances.append(d)
        total += d

    sample_points = []
    spacing = total / n_samples
    for i in range(n_samples):
        target = i * spacing
        cum = 0
        for j, d in enumerate(distances):
            if cum + d >= target:
                frac = (target - cum) / d if d != 0 else 0
                v1 = vertices[j]
                v2 = vertices[(j+1) % N]
                x = v1[0] + frac * (v2[0] - v1[0])
                y = v1[1] + frac * (v2[1] - v1[1])
                sample_points.append((x, y))
                break
            cum += d
    return sample_points

def get_circle_points(n, radius=1.0):
    """Return n uniformly sampled points on a circle of given radius."""
    return [(radius * math.cos(2 * math.pi * i / n), radius * math.sin(2 * math.pi * i / n)) for i in range(n)]

def get_square_points(n, half_side=1.0):
    """Return n points sampled along the perimeter of a square centered at the origin."""
    vertices = [
        ( half_side,  half_side),
        ( half_side, -half_side),
        (-half_side, -half_side),
        (-half_side,  half_side)
    ]
    return sample_polygon(vertices, n)

def get_triangle_points(n):
    """Return n points sampled along the perimeter of an equilateral triangle centered at the origin."""
    # Use an equilateral triangle with vertices chosen to roughly fit in a unit circle.
    v0 = (0, 1)
    v1 = ( math.sqrt(3)/2, -0.5)
    v2 = (-math.sqrt(3)/2, -0.5)
    vertices = [v0, v1, v2]
    return sample_polygon(vertices, n)

def get_plus_points(n):
    """
    Return n points sampled along the perimeter of a plus sign.
    The plus sign is defined by the union of two rectangles.
    Coordinates below are chosen so that the overall shape fits roughly in a circle of radius 1.
    """
    vertices = [
        (-0.2,  1.0), (0.2,  1.0), 
        (0.2,  0.2), (1.0,  0.2), 
        (1.0, -0.2), (0.2, -0.2), 
        (0.2, -1.0), (-0.2, -1.0), 
        (-0.2, -0.2), (-1.0, -0.2), 
        (-1.0,  0.2), (-0.2,  0.2)
    ]
    return sample_polygon(vertices, n)

def create_filled_curve(points, name="MorphCurve"):
    """
    Create a new 2D curve object from a list of 2D points.
    The curve is closed and its fill_mode is set to 'BOTH' (filled).
    """
    curve_data = bpy.data.curves.new(name=name, type='CURVE')
    curve_data.dimensions = '2D'
    curve_data.fill_mode = 'BOTH'
    spline = curve_data.splines.new('POLY')
    spline.points.add(len(points) - 1)
    for i, (x, y) in enumerate(points):
        spline.points[i].co = (x, y, 0, 1)
    spline.use_cyclic_u = True  # close the curve
    curve_obj = bpy.data.objects.new(name, curve_data)
    bpy.context.scene.collection.objects.link(curve_obj)
    return curve_obj

# -----------------------
# PARAMETERS & TARGET SHAPES
# -----------------------

n_points = 64  # number of points per shape (all target shapes will use the same number)
# Generate the target shapes:
shape_A = get_circle_points(n_points, radius=1.0)         # Top-Left: Circle
shape_B = get_square_points(n_points, half_side=1.0)        # Top-Right: Square
shape_C = get_triangle_points(n_points)                     # Bottom-Left: Triangle
shape_D = get_plus_points(n_points)                         # Bottom-Right: Plus sign

# -----------------------
# GRID SETTINGS FOR THE KITBASH SHEET
# -----------------------

columns = 12  # number of interpolation steps along u
rows = 12     # number of interpolation steps along v
spacing_x = 4.0  # horizontal spacing between shapes
spacing_y = 4.0  # vertical spacing between shapes

# Create (or get) a collection for the kitbash shapes.
collection_name = "MorphKitbash_Filled"
if collection_name in bpy.data.collections:
    kitbash_coll = bpy.data.collections[collection_name]
    # Remove previous objects.
    for obj in list(kitbash_coll.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
else:
    kitbash_coll = bpy.data.collections.new(collection_name)
    bpy.context.scene.collection.children.link(kitbash_coll)

# -----------------------
# CREATE THE KITBASH GRID OF INTERPOLATED FILLED SHAPES
# -----------------------

for row_idx in range(rows):
    # v parameter: 0 at bottom, 1 at top.
    v = row_idx / (rows - 1) if rows > 1 else 0
    for col_idx in range(columns):
        # u parameter: 0 at left, 1 at right.
        u = col_idx / (columns - 1) if columns > 1 else 0

        # For each point index, compute bilinear interpolation:
        interp_points = []
        for i in range(n_points):
            # Each target shape provides a 2D point.
            Ax, Ay = shape_A[i]
            Bx, By = shape_B[i]
            Cx, Cy = shape_C[i]
            Dx, Dy = shape_D[i]
            # Bilinear interpolation:
            x = (1-u)*(1-v)*Ax + u*(1-v)*Bx + (1-u)*v*Cx + u*v*Dx
            y = (1-u)*(1-v)*Ay + u*(1-v)*By + (1-u)*v*Cy + u*v*Dy
            interp_points.append((x, y))
        
        # Create the filled 2D curve from the interpolated points.
        obj_name = f"Morph_r{row_idx:02d}_c{col_idx:02d}"
        curve_obj = create_filled_curve(interp_points, name=obj_name)
        # Position the shape in the grid.
        curve_obj.location = (col_idx * spacing_x, row_idx * spacing_y, 0)
        kitbash_coll.objects.link(curve_obj)
        bpy.context.scene.collection.objects.unlink(curve_obj)

print(f"Created a kitbash sheet of {rows*columns} filled morphing shapes in collection '{collection_name}'.")
