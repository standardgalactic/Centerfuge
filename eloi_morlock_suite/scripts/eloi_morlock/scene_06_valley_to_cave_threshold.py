
# Scene 06 – Valley→Cave Threshold — Flyxion
import bpy, sys, argparse, math, random, json
def parse():
    ap=argparse.ArgumentParser(); ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=1920); ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--seed", type=int, default=19); return ap.parse_known_args(sys.argv[sys.argv.index("--")+1:])
def mc(rgba): m=bpy.data.materials.new("M"); m.use_nodes=True; m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=rgba; return m
def run(out,w,h,seed):
    random.seed(seed); bpy.ops.wm.read_factory_settings(use_empty=True)
    sc=bpy.context.scene; sc.render.engine="BLENDER_EEVEE"; sc.view_layers["View Layer"].use_freestyle=True
    sc.render.resolution_x=w; sc.render.resolution_y=h
    bpy.ops.mesh.primitive_plane_add(size=100, location=(0,0,-1.5)); valley=bpy.context.active_object
    valley.data.materials.append(mc((0.85,1.0,0.85,1)))
    bpy.ops.mesh.primitive_plane_add(size=100, location=(0,0,-1.6)); cave=bpy.context.active_object
    cave.data.materials.append(mc((0.08,0.09,0.1,1)))
    bpy.ops.mesh.primitive_torus_add(major_radius=12, minor_radius=2, location=(0,8,0), rotation=(math.pi/2,0,0))
    ring=bpy.context.active_object; ring.data.materials.append(mc((0.2,0.25,0.3,1)))
    bpy.ops.object.light_add(type="SUN", location=(20,-20,30)); bpy.context.active_object.data.energy=2.5
    bpy.ops.object.light_add(type="POINT", location=(0,5,5)); bpy.context.active_object.data.energy=250.0
    bpy.ops.object.camera_add(location=(-18,-30,14), rotation=(math.radians(60),0,math.radians(15))); sc.camera=bpy.context.active_object
    sc.render.filepath=out; bpy.ops.render.render(write_still=True)
    with open(out.replace(".png",".json"),"w") as f: json.dump({"scene":"scene_06_valley_to_cave_threshold","seed":seed,"size":[w,h]}, f, indent=2)
if __name__=="__main__":
    a,_=parse(); run(a.out,a.width,a.height,a.seed)
