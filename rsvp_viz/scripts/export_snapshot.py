# scripts/export_snapshot.py
import bpy, argparse, sys, os

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    return ap.parse_known_args(sys.argv[sys.argv.index("--")+1:])[0]

def main():
    args=parse_args()
    scene=bpy.context.scene
    scene.render.engine='CYCLES'
    scene.cycles.samples=64
    scene.render.fps=24
    scene.render.image_settings.file_format='PNG'
    scene.render.filepath=args.out
    bpy.ops.render.render(write_still=True)

if __name__=="__main__":
    main()
