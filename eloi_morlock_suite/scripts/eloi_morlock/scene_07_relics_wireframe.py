
# Scene 07 – City Relics Wireframe — Flyxion
import bpy, sys, argparse, math, random, json
def parse():
    ap=argparse.ArgumentParser(); ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=1920); ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--seed", type=int, default=5); return ap.parse_known_args(sys.argv[sys.argv.index("--")+1:])
def mc(rgba): m=bpy.data.materials.new("M"); m.use_nodes=True; m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=rgba; return m
def run(out,w,h,seed):
    random.seed(seed); bpy.ops.wm.read_factory_settings(use_empty=True)
    sc=bpy.context.scene; sc.render.engine="BLENDER_EEVEE"; sc.view_layers["View Layer"].use_freestyle=True
    sc.render.resolution_x=w; sc.render.resolution_y=h
    base=mc((0.82,0.82,0.86,1))
    for i in range(32):
        x=random.uniform(-40,40); y=random.uniform(-40,40); z=random.uniform(0.2,3.0)
        bpy.ops.mesh.primitive_cube_add(size=random.uniform(2,6), location=(x,y,z/2))
        o=bpy.context.active_object; o.data.materials.append(base)
        mod=o.modifiers.new("Wire","WIREFRAME"); mod.thickness=0.03
    bpy.ops.object.camera_add(location=(0,-55,28), rotation=(math.radians(65),0,0)); sc.camera=bpy.context.active_object
    sc.render.filepath=out; bpy.ops.render.render(write_still=True)
    with open(out.replace(".png",".json"),"w") as f: json.dump({"scene":"scene_07_relics_wireframe","seed":seed,"size":[w,h]}, f, indent=2)
if __name__=="__main__":
    a,_=parse(); run(a.out,a.width,a.height,a.seed)
