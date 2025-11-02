"""
STEP 09 — Field Overlay
Adds vector arrows around the tetrahedron to suggest flow (Φ, 𝒗, S).
"""
import bpy, sys, argparse, math, random
parser=argparse.ArgumentParser()
parser.add_argument("--out", required=True)
parser.add_argument("--count", type=int, default=80)
args,_=parser.parse_known_args(sys.argv[sys.argv.index("--")+1:])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=1, depth=1.5)
core=bpy.context.active_object
core.name="TetraCore"
random.seed(42)
for i in range(args.count):
    theta=2*math.pi*random.random()
    phi=math.acos(2*random.random()-1)
    r=1.5+random.random()
    x=r*math.sin(phi)*math.cos(theta)
    y=r*math.sin(phi)*math.sin(theta)
    z=r*math.cos(phi)
    bpy.ops.mesh.primitive_cone_add(radius1=0.05, depth=0.3, location=(x,y,z))
    arrow=bpy.context.active_object
    arrow.rotation_euler=(phi,0,theta)
    mat=bpy.data.materials.new(f"ArrowMat{i}")
    mat.use_nodes=True
    col=(random.random(),0.5*random.random(),1.0-random.random()/2,1)
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=col
    arrow.data.materials.append(mat)
bpy.ops.wm.save_as_mainfile(filepath=args.out)
