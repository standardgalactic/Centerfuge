"""
STEP 01 — Base Tetrahedron
Constructs the canonical tetrahedron frame used for all subsequent rotations.
"""
import bpy, sys, argparse
from mathutils import Vector
parser = argparse.ArgumentParser()
parser.add_argument("--out", required=True)
args, _ = parser.parse_known_args(sys.argv[sys.argv.index("--")+1:])
bpy.ops.wm.read_factory_settings(use_empty=True)
verts = [
    Vector((1, 1, 1)),
    Vector((-1, -1, 1)),
    Vector((-1, 1, -1)),
    Vector((1, -1, -1))
]
faces = [(0,1,2), (0,1,3), (0,2,3), (1,2,3)]
mesh = bpy.data.meshes.new("Tetrahedron")
mesh.from_pydata(verts, [], faces)
obj = bpy.data.objects.new("Tetrahedron", mesh)
bpy.context.collection.objects.link(obj)
bpy.ops.object.shade_smooth()
mat = bpy.data.materials.new("TetraGlow")
mat.use_nodes = True
em = mat.node_tree.nodes.new("ShaderNodeEmission")
em.inputs[0].default_value = (0.2, 0.6, 1, 1)
mat.node_tree.links.new(em.outputs[0], mat.node_tree.nodes["Material Output"].inputs[0])
obj.data.materials.append(mat)
bpy.ops.wm.save_as_mainfile(filepath=args.out)
