
# Scene 05 – Ridge Overlook — Flyxion
import bpy, sys, argparse, math, random, json
def parse():
    ap=argparse.ArgumentParser(); ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=1920); ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--seed", type=int, default=33); return ap.parse_known_args(sys.argv[sys.argv.index("--")+1:])
def mc(rgba): m=bpy.data.materials.new("M"); m.use_nodes=True; m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=rgba; return m
def run(out,w,h,seed):
    random.seed(seed); bpy.ops.wm.read_factory_settings(use_empty=True)
    sc=bpy.context.scene; sc.render.engine="BLENDER_EEVEE"; sc.view_layers["View Layer"].use_freestyle=True
    sc.render.resolution_x=w; sc.render.resolution_y=h
    sc.world.use_nodes=True; wn=sc.world.node_tree; wn.nodes.clear()
    bg=wn.nodes.new("ShaderNodeBackground"); outw=wn.nodes.new("ShaderNodeOutputWorld")
    bg.inputs[0].default_value=(0.90,0.98,1.0,1); bg.inputs[1].default_value=1.0; wn.links.new(bg.outputs[0], outw.inputs[0])
    bpy.ops.mesh.primitive_grid_add(size=100, x_subdivisions=200, y_subdivisions=200); t=bpy.context.active_object
    bpy.ops.object.modifier_add(type="DISPLACE"); tx=bpy.data.textures.new("ridge","MUSGRAVE")
    tx.noise_scale=8.0; t.modifiers["Displace"].texture=tx; t.modifiers["Displace"].strength=10.0
    t.data.materials.append(mc((0.78,0.98,0.85,1)))
    bpy.ops.object.light_add(type="SUN", location=(15,-25,50)); bpy.context.active_object.data.energy=2.5
    bpy.ops.object.camera_add(location=(-30,-50,40), rotation=(math.radians(60),0,math.radians(-10))); sc.camera=bpy.context.active_object
    sc.render.filepath=out; bpy.ops.render.render(write_still=True)
    with open(out.replace(".png",".json"),"w") as f: json.dump({"scene":"scene_05_ridge_overlook","seed":seed,"size":[w,h]}, f, indent=2)
if __name__=="__main__":
    a,_=parse(); run(a.out,a.width,a.height,a.seed)
