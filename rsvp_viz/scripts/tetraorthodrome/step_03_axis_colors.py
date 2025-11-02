"""
STEP 03 — Axis Coloring
Creates colored cylinders along each axis to make orientation visible.
"""
import bpy, sys, argparse, math
parser=argparse.ArgumentParser()
parser.add_argument("--out", required=True)
args,_=parser.parse_known_args(sys.argv[sys.argv.index("--")+1:])
bpy.ops.wm.read_factory_settings(use_empty=True)
axes = {
    "X": ((1,0,0),(1,0.2,0.2,1),(0,math.pi/2,0)),
    "Y": ((0,1,0),(0.2,1,0.2,1),(-math.pi/2,0,0)),
    "Z": ((0,0,1),(0.2,0.2,1,1),(0,0,0))
}
for name,(loc,col,rot) in axes.items():
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=2, location=(0,0,0))
    cyl=bpy.context.active_object
    cyl.rotation_euler=rot
    mat=bpy.data.materials.new(f"Mat_{name}")
    mat.use_nodes=True
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=col
    cyl.data.materials.append(mat)
    bpy.context.collection.objects.link(cyl)
bpy.ops.wm.save_as_mainfile(filepath=args.out)
