
# Scene 08 – Bioluminescent Grotto (close-up) — Flyxion
import bpy, sys, argparse, math, random, json
def parse():
    ap=argparse.ArgumentParser(); ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=1920); ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--seed", type=int, default=11); return ap.parse_known_args(sys.argv[sys.argv.index("--")+1:])
def emissive(name, rgba, strength=3.0):
    m=bpy.data.materials.new(name); m.use_nodes=True
    e=m.node_tree.nodes.new("ShaderNodeEmission")
    e.inputs[0].default_value=rgba; e.inputs[1].default_value=strength
    m.node_tree.links.new(e.outputs[0], m.node_tree.nodes["Material Output"].inputs[0])
    return m
def run(out,w,h,seed):
    random.seed(seed); bpy.ops.wm.read_factory_settings(use_empty=True)
    sc=bpy.context.scene; sc.render.engine="BLENDER_EEVEE"; sc.view_layers["View Layer"].use_freestyle=True
    sc.render.resolution_x=w; sc.render.resolution_y=h
    sc.world.use_nodes=True; wn=sc.world.node_tree; wn.nodes.clear()
    bg=wn.nodes.new("ShaderNodeBackground"); outw=wn.nodes.new("ShaderNodeOutputWorld")
    bg.inputs[0].default_value=(0.01,0.01,0.015,1); bg.inputs[1].default_value=1.0; wn.links.new(bg.outputs[0], outw.inputs[0])
    bpy.ops.mesh.primitive_uv_sphere_add(radius=14, location=(0,0,3)); shell=bpy.context.active_object
    bpy.ops.object.modifier_add(type="DISPLACE"); tx=bpy.data.textures.new("t","VORONOI")
    shell.modifiers["Displace"].texture=tx; shell.modifiers["Displace"].strength=2.0
    mwall=bpy.data.materials.new("Wall"); mwall.use_nodes=True
    mwall.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(0.08,0.08,0.09,1); shell.data.materials.append(mwall)
    glow=emissive("Glow",(0.1,1.0,0.9,1), strength=3.0)
    for _ in range(140):
        x,y,z=(random.uniform(-6,6),random.uniform(-6,6),random.uniform(-1,6))
        bpy.ops.mesh.primitive_cone_add(radius1=0.25, depth=0.6, location=(x,y,z))
        bpy.context.active_object.data.materials.append(glow)
    bpy.ops.object.camera_add(location=(7,-8,4), rotation=(math.radians(75),0,math.radians(35))); sc.camera=bpy.context.active_object
    sc.render.filepath=out; bpy.ops.render.render(write_still=True)
    with open(out.replace(".png",".json"),"w") as f: json.dump({"scene":"scene_08_biolume_grotto_closeup","seed":seed,"size":[w,h]}, f, indent=2)
if __name__=="__main__":
    a,_=parse(); run(a.out,a.width,a.height,a.seed)
