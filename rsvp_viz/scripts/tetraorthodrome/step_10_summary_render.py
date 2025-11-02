"""
STEP 10 — Summary Render
Orbits camera around the tetraorthodrome, producing a complete animation.
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
    t=f/args.frames
    obj.rotation_euler[0]=math.radians(360*t)
    obj.rotation_euler[1]=math.radians(180*t)
    obj.rotation_euler[2]=math.radians(90*math.sin(t*2*math.pi))
    obj.keyframe_insert(data_path="rotation_euler",frame=f)
bpy.ops.object.camera_add(location=(4,0,2))
cam=bpy.context.active_object
bpy.context.scene.camera=cam
for f in range(1, args.frames+1, 5):
    ang=2*math.pi*f/args.frames
    cam.location.x=4*math.cos(ang)
    cam.location.y=4*math.sin(ang)
    cam.keyframe_insert(data_path="location",frame=f)
# basic render setup
scene=bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.samples=64
scene.render.fps=24
scene.render.image_settings.file_format='FFMPEG'
scene.render.ffmpeg.format='MPEG4'
scene.render.ffmpeg.codec='H264'
scene.render.filepath=f"{args.out[:-6]}.mp4"
bpy.ops.render.render(animation=True)
bpy.ops.wm.save_as_mainfile(filepath=args.out)
