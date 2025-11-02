
# Scene 03 – Morlock Caves — Flyxion
import bpy, sys, argparse, math, random, json
def parse():
    ap=argparse.ArgumentParser(); ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=1920); ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--seed", type=int, default=13); return ap.parse_known_args(sys.argv[sys.argv.index("--")+1:])
def mc(rgba):
    m=bpy.data.materials.new("M"); m.use_nodes=True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=rgba; return m
def run(out,w,h,seed):
    random.seed(seed); bpy.ops.wm.read_factory_settings(use_empty=True)
    sc=bpy.context.scene; sc.render.engine="BLENDER_EEVEE"
    sc.render.resolution_x=w; sc.render.resolution_y=h; sc.view_layers["View Layer"].use_freestyle=True
    sc.world.use_nodes=True; wn=sc.world.node_tree; wn.nodes.clear()
    bg=wn.nodes.new("ShaderNodeBackground"); outw=wn.nodes.new("ShaderNodeOutputWorld")
    bg.inputs[0].default_value=(0.02,0.02,0.03,1); bg.inputs[1].default_value=1.0; wn.links.new(bg.outputs[0], outw.inputs[0])
    # cave shell
    bpy.ops.mesh.primitive_uv_sphere_add(radius=20, location=(0,0,6)); shell=bpy.context.active_object
    bpy.ops.object.modifier_add(type="DISPLACE"); tx=bpy.data.textures.new("rock","NOISE")
    shell.modifiers["Displace"].texture=tx; shell.modifiers["Displace"].strength=3.0
    shell.data.materials.append(mc((0.1,0.1,0.12,1)))
    # floor
    bpy.ops.mesh.primitive_plane_add(size=60, location=(0,0,-2)); floor=bpy.context.active_object
    floor.data.materials.append(mc((0.08,0.08,0.09,1)))
    # biolum lights
    for _ in range(80):
        bpy.ops.object.light_add(type="POINT", location=(random.uniform(-10,10),random.uniform(-10,10),random.uniform(0,10)))
        lp=bpy.context.active_object; lp.data.energy=80; lp.data.color=(0.2,0.8,1.0)
    # camera
    bpy.ops.object.camera_add(location=(12,-16,4), rotation=(math.radians(75),0,math.radians(35))); sc.camera=bpy.context.active_object
    sc.render.filepath=out; bpy.ops.render.render(write_still=True)
    with open(out.replace(".png",".json"),"w") as f: json.dump({"scene":"scene_03_morlock_caves","seed":seed,"size":[w,h]}, f, indent=2)
if __name__=="__main__":
    a,_=parse(); run(a.out,a.width,a.height,a.seed)
