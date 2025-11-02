"""
STEP 07 — Shadow Projection
Adds a ground plane and a light to visualize the tetraorthodrome's shadow.
"""
import bpy, sys, argparse
parser=argparse.ArgumentParser()
parser.add_argument("--out", required=True)
args,_=parser.parse_known_args(sys.argv[sys.argv.index("--")+1:])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=1, depth=1.5)
obj=bpy.context.active_object
bpy.ops.mesh.primitive_plane_add(size=6, location=(0,0,-1))
light=bpy.data.lights.new(name="KeyLight",type='SUN')
light.energy=3.0
lightobj=bpy.data.objects.new("KeyLight",light)
lightobj.location=(4,-4,5)
bpy.context.collection.objects.link(lightobj)
bpy.ops.wm.save_as_mainfile(filepath=args.out)
