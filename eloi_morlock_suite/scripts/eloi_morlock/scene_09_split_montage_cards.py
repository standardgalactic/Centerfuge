
# Scene 09 – Split Montage Cards — Flyxion
import bpy, sys, argparse, json
def parse():
    ap=argparse.ArgumentParser(); ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=1920); ap.add_argument("--height", type=int, default=1080)
    return ap.parse_known_args(sys.argv[sys.argv.index("--")+1:])
def mc(rgba): m=bpy.data.materials.new("M"); m.use_nodes=True; m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=rgba; return m
def run(out,w,h):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc=bpy.context.scene; sc.render.engine="BLENDER_EEVEE"; sc.view_layers["View Layer"].use_freestyle=True
    sc.render.resolution_x=w; sc.render.resolution_y=h
    def card(x, col):
        bpy.ops.mesh.primitive_plane_add(size=10, location=(x,0,0))
        p=bpy.context.active_object; p.data.materials.append(mc(col))
    card(-6,(0.85,1.0,0.9,1))
    card( 6,(0.07,0.1,0.12,1))
    bpy.ops.object.camera_add(location=(0,-18,0), rotation=(1.5708,0,0)); sc.camera=bpy.context.active_object
    sc.render.filepath=out; bpy.ops.render.render(write_still=True)
    with open(out.replace(".png",".json"),"w") as f: json.dump({"scene":"scene_09_split_montage_cards","size":[w,h]}, f, indent=2)
if __name__=="__main__":
    a,_=parse(); run(a.out,a.width,a.height)
