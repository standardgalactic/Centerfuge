"""
STEP 08 — Entropy Color Map
Applies dynamic emission color keyed to a sinusoid over time.
"""
import bpy, sys, argparse, math
parser=argparse.ArgumentParser()
parser.add_argument("--out", required=True)
parser.add_argument("--frames", type=int, default=180)
args,_=parser.parse_known_args(sys.argv[sys.argv.index("--")+1:])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=1, depth=1.5)
obj=bpy.context.active_object
mat=bpy.data.materials.new("EntropyMat")
mat.use_nodes=True
em=mat.node_tree.nodes.new("ShaderNodeEmission")
mat.node_tree.links.new(em.outputs[0],mat.node_tree.nodes["Material Output"].inputs[0])
obj.data.materials.append(mat)
for f in range(1, args.frames+1, 5):
    t=f/args.frames
    hue=t
    color=(abs(math.sin(2*math.pi*hue)),abs(math.sin(4*math.pi*hue)),abs(math.sin(6*math.pi*hue)),1)
    em.inputs[0].default_value=color
    em.inputs[1].default_value=2.0
    em.keyframe_insert(data_path="inputs[0].default_value", frame=f)
bpy.ops.wm.save_as_mainfile(filepath=args.out)
