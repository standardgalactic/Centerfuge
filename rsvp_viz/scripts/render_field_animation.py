# scripts/render_field_animation.py
import bpy, argparse, sys, yaml, math

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    return ap.parse_known_args(sys.argv[sys.argv.index("--")+1:])[0]

def main():
    args=parse_args()
    with open(args.config,"r") as f: cfg=yaml.safe_load(f)
    scene=bpy.context.scene
    frames=int(cfg.get("animation",{}).get("frames",180))
    scene.frame_start=1; scene.frame_end=frames
    scene.render.engine='CYCLES'
    scene.cycles.samples=64
    scene.render.fps=24
    scene.render.image_settings.file_format='FFMPEG'
    scene.render.ffmpeg.format='MPEG4'
    scene.render.ffmpeg.codec='H264'
    scene.render.ffmpeg.constant_rate_factor='HIGH'
    scene.render.filepath=f"{args.out}/animation.mp4"

    cam_radius=float(cfg.get("animation",{}).get("camera_radius",3.0))
    if not any(o.type=='CAMERA' for o in bpy.context.scene.objects):
        bpy.ops.object.camera_add(location=(cam_radius,0,cam_radius*0.7))
    cam=[o for o in bpy.context.scene.objects if o.type=='CAMERA'][0]
    scene.camera=cam

    deg=float(cfg.get("animation",{}).get("camera_orbit_degrees",360))
    for f in range(scene.frame_start, frames+1):
        t=(f-scene.frame_start)/(frames-scene.frame_start+1)
        ang=math.radians(deg)*t
        cam.location.x=cam_radius*math.cos(ang)
        cam.location.y=cam_radius*math.sin(ang)
        cam.keyframe_insert(data_path="location", frame=f)

    bpy.ops.render.render(animation=True)

if __name__=="__main__":
    main()
