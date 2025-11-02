"""
STEP 06 — Full Precession
Illustrates compound rotation through changing Euler angles (Z–Y–X order).
"""
import bpy, sys, argparse, math
parser=argparse.ArgumentParser()
parser.add_argument("--out", required=True)
parser.add_argument("--frames", type=int, default=180)
args,_=parser.parse_known_args(sys.argv[sys.argv.index("--")+1:])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=1, depth=1.5)
obj=bpy.context.active_object
obj.rotation_mode='ZYX'
for f in range(1, args.frames+1, 5):
    t=f/args.frames
    obj.rotation_euler[0]=math.radians(360*t)                # Z
    obj.rotation_euler[1]=math.radians(180*t)                # Y
    obj.rotation_euler[2]=math.radians(90*math.sin(t*2*math.pi))  # X (modulated)
    obj.keyframe_insert(data_path="rotation_euler",frame=f)
bpy.ops.wm.save_as_mainfile(filepath=args.out)
