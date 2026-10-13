"""Chapter 21: build meshes from arrays, and check what was built."""
import numpy as np
import bpy, bmesh


def mesh_from_arrays(name, verts, faces):
    """verts: (n,3) floats; faces: list of equal-length index tuples (all triangles or all quads), built with foreach_set."""
    verts = np.asarray(verts, dtype=np.float32); faces = np.asarray(faces, dtype=np.int32)
    k = faces.shape[1]
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(verts)); me.vertices.foreach_set('co', verts.ravel())
    me.loops.add(faces.size); me.loops.foreach_set('vertex_index', faces.ravel())
    me.polygons.add(len(faces))
    me.polygons.foreach_set('loop_start', np.arange(0, faces.size, k, dtype=np.int32))
    me.update(calc_edges=True)
    return me


def report(me):
    """Facts about a mesh that a script should check before trusting it."""
    bm = bmesh.new(); bm.from_mesh(me)
    nonmanifold = sum(1 for e in bm.edges if len(e.link_faces) > 2)
    boundary = sum(1 for e in bm.edges if e.is_boundary)
    out = dict(V=len(me.vertices), E=len(me.edges), F=len(me.polygons), L=len(me.loops),
               euler=len(me.vertices) - len(me.edges) + len(me.polygons), boundary_edges=boundary, nonmanifold_edges=nonmanifold,
               area=round(sum(p.area for p in me.polygons), 6))
    bm.free(); return out
