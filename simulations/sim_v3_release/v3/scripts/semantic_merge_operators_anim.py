import bpy
import math
import random

"""Semantic Merge Operators Animation
--------------------------------------
Visualizes three types of semantic merge between modules A and B:
  - union-like merge
  - intersection-like merge
  - homotopy / interpolation merge

Each module is a colored blob; the merge operator is a third blob whose
geometry + color interpolate between them over time.
"""

FRAMES = 120
COLL_NAME = "SemanticMerge_v3"


def clear_collection(name):
    if name in bpy.data.collections:
        coll = bpy.data.collections[name]
        for obj in list(coll.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(coll)


def ensure_collection(name):
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    return coll


def make_blob(name, loc, color):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=loc)
    obj = bpy.context.active_object
    obj.name = name

    mat = bpy.data.materials.new(f"Mat_{name}")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Subsurface"].default_value = 0.25
    bsdf.inputs["Subsurface Color"].default_value = color
    bsdf.inputs["Emission"].default_value = color
    bsdf.inputs["Emission Strength"].default_value = 2.0
    obj.data.materials.append(mat)
    return obj


def setup_scene():
    clear_collection(COLL_NAME)
    coll = ensure_collection(COLL_NAME)

    A = make_blob("Module_A", (-2.0, 0.0, 0.0), (0.2, 0.6, 1.0, 1.0))
    B = make_blob("Module_B", ( 2.0, 0.0, 0.0), (1.0, 0.5, 0.2, 1.0))
    M = make_blob("Merge_M", ( 0.0, 0.0, 0.0), (0.9, 0.9, 0.9, 1.0))

    # Assign roles
    A["semantic_role"] = "source_A"
    B["semantic_role"] = "source_B"
    M["semantic_role"] = "merge_operator"

    for obj in (A, B, M):
        for c in obj.users_collection:
            c.objects.unlink(obj)
        coll.objects.link(obj)

    return A, B, M


def animate_merge(A, B, M):
    for frame in range(1, FRAMES+1):
        bpy.context.scene.frame_set(frame)
        t = (frame - 1) / (FRAMES - 1)

        # Merge path: oscillate between union-like and intersection-like
        # t in [0, 0.5): emphasize union; [0.5, 1]: emphasize intersection
        if t < 0.5:
            alpha = 2 * t        # union weight
            beta = 0.0
        else:
            alpha = 1.0
            beta = 2 * (t - 0.5) # intersection weight

        # location interpolation
        M.location.x = (1 - t) * A.location.x + t * B.location.x
        M.location.z = 0.5 * math.sin(2 * math.pi * t)

        # scale encodes "semantic volume" of merge
        scale_base = 1.0 + 0.3 * alpha + 0.2 * beta
        M.scale = (scale_base, scale_base, scale_base)

        # color interpolation
        matA = A.active_material
        matB = B.active_material
        matM = M.active_material

        if matA and matB and matM and matM.use_nodes:
            colA = matA.node_tree.nodes["Principled BSDF"].inputs["Emission"].default_value
            colB = matB.node_tree.nodes["Principled BSDF"].inputs["Emission"].default_value
            r = (1 - t) * colA[0] + t * colB[0]
            g = (1 - t) * colA[1] + t * colB[1]
            b = (1 - t) * colA[2] + t * colB[2]
            matM.node_tree.nodes["Principled BSDF"].inputs["Emission"].default_value = (r, g, b, 1.0)
            matM.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 3.0 + 2.0 * beta

        M.keyframe_insert(data_path="location")
        M.keyframe_insert(data_path="scale")

    print("[SemanticMerge] Merge operator animation complete.")


if __name__ == "__main__":
    A, B, M = setup_scene()
    animate_merge(A, B, M)
