"""
STEP 05 — Dual-Axis Spin
Simultaneous rotation around X and Y axes.
"""
import bpy, sys, argparse, math
parser=argparse.ArgumentParser()
parser.add_argument("--out", required=True)
parser.add_argument("--frames", type=int, default=180)
args,_=parser.parse_known_args(sys.argv[sys.argv.index("--")+1:])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=1, depth=1.5)
obj=bpy.context.active_object
obj.rotation_mode='XYZ'
for f in range(1, args.frames+1, 5):
    obj.rotation_euler[0]=math.radians(2*f)
    obj.rotation_euler[1]=math.radians(1.5*f)
    obj.keyframe_insert(data_path="rotation_euler",frame=f)
bpy.ops.wm.save_as_mainfile(filepath=args.out)
