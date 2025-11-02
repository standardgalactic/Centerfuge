"""
STEP 02 — Add Orthogonal Axes
Adds four orthogonal empties representing X, Y, Z, and diagonal D axes.
"""
import bpy, sys, argparse
parser=argparse.ArgumentParser()
parser.add_argument("--out", required=True)
args,_=parser.parse_known_args(sys.argv[sys.argv.index("--")+1:])
bpy.ops.wm.read_factory_settings(use_empty=True)
axes = {
    "X": ((1,0,0),(1,0,0,1)),
    "Y": ((0,1,0),(0,1,0,1)),
    "Z": ((0,0,1),(0,0,1,1)),
    "D": ((1,1,1),(1,1,0,1))
}
for name,(vec,col) in axes.items():
    empty=bpy.data.objects.new(f"Axis_{name}",None)
    empty.empty_display_type='ARROWS'
    empty.location=tuple(1.5*v for v in vec)
    empty.color=col
    bpy.context.collection.objects.link(empty)
bpy.ops.wm.save_as_mainfile(filepath=args.out)
